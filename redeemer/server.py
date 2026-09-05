from __future__ import annotations

import hmac
import json
import os
import threading
import time
import traceback
from datetime import datetime, timezone
from email.parser import BytesParser
from hashlib import sha256
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import views
from .backup import dump, filename, load, schedule, snapshot
from .db import (
    COUNTRY,
    DEVICE,
    NONCE,
    PLATFORM,
    VERSION,
    Database,
    clean,
    generate_batch,
    generate_code,
    normalize_code,
)

MAX_BODY = 64 * 1024
MAX_UPLOAD = 128 * 1024 * 1024
NONCE_TTL = 600
SESSION_COOKIE = "redeemer_session"
SESSION_TTL = 7 * 24 * 3600


class Config:
    def __init__(self) -> None:
        self.db_path = os.environ.get("REDEEMER_DB", "redeemer.db")
        self.host = os.environ.get("REDEEMER_HOST", "127.0.0.1")
        self.port = int(os.environ.get("REDEEMER_PORT", "8787"))
        self.password = os.environ.get("REDEEMER_ADMIN_PASSWORD", "")
        self.behind_proxy = os.environ.get("REDEEMER_BEHIND_PROXY", "") == "1"
        default_backups = os.path.join(os.path.dirname(self.db_path) or ".", "backups")
        self.backup_dir = os.environ.get("REDEEMER_BACKUP_DIR", default_backups)
        self.backup_keep = int(os.environ.get("REDEEMER_BACKUP_KEEP", "14"))
        self.backup_hours = float(os.environ.get("REDEEMER_BACKUP_HOURS", "24"))


class RateLimiter:
    """Fixed window per key. Redeem attempts are cheap to guess, so they are capped."""

    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], tuple[int, float]] = {}
        self._lock = threading.Lock()

    def allow(self, bucket: str, key: str, limit: int, window: float) -> bool:
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > 20000:
                self._hits = {k: v for k, v in self._hits.items() if v[1] > now}
            count, reset = self._hits.get((bucket, key), (0, 0.0))
            if reset <= now:
                count, reset = 0, now + window
            count += 1
            self._hits[(bucket, key)] = (count, reset)
            return count <= limit


class Nonces:
    """Replay window for anonymous redemptions.

    Without a device id a retry cannot be recognised, so a dropped connection would spend a
    second use. The nonce the app sends per attempt answers that: the first result is kept
    for a few minutes and handed back to the retry. It never reaches disk and it expires,
    so nothing about the person redeeming is retained.
    """

    def __init__(self, ttl: float = NONCE_TTL) -> None:
        self.ttl = ttl
        self.lock = threading.Lock()
        self._seen: dict[str, tuple[float, tuple[bool, str]]] = {}

    def get(self, key: str) -> tuple[bool, str] | None:
        now = time.monotonic()
        if len(self._seen) > 10000:
            self._seen = {k: v for k, v in self._seen.items() if v[0] > now}
        entry = self._seen.get(key)
        return None if entry is None or entry[0] <= now else entry[1]

    def put(self, key: str, result: tuple[bool, str]) -> None:
        self._seen[key] = (time.monotonic() + self.ttl, result)


class Handler(BaseHTTPRequestHandler):
    server_version = "Redeemer"
    protocol_version = "HTTP/1.1"
    limit = MAX_BODY

    # --- plumbing -----------------------------------------------------------

    @property
    def db(self) -> Database:
        return self.server.db

    @property
    def config(self) -> Config:
        return self.server.config

    def log_message(self, fmt, *args):  # noqa: A003 - the default logs the client IP
        print(fmt % args, flush=True)

    def client_ip(self) -> str:
        if self.config.behind_proxy:
            forwarded = self.headers.get("X-Forwarded-For", "")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return self.client_address[0]

    def body(self) -> bytes:
        """Read once and cache: the socket must be drained before responding."""
        cached = getattr(self, "_body", None)
        if cached is not None:
            return cached
        length = int(self.headers.get("Content-Length") or 0)
        remaining = max(0, length)
        chunks = []
        while remaining:
            chunk = self.rfile.read(min(remaining, 8192))
            if not chunk:
                break
            remaining -= len(chunk)
            if length <= self.limit:
                chunks.append(chunk)
        self._body = b"".join(chunks)
        return self._body

    def query(self, name: str) -> str:
        values = parse_qs(urlparse(self.path).query).get(name)
        return values[0][:64] if values else ""

    def upload(self, field: str) -> bytes:
        """The panel has one file field, so multipart is read here instead of pulled in."""
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            return b""
        message = BytesParser().parsebytes(
            b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + self.body()
        )
        for part in message.walk():
            if part.get_param("name", header="content-disposition") == field:
                return part.get_payload(decode=True) or b""
        return b""

    def form(self) -> dict[str, str]:
        parsed = parse_qs(self.body().decode("utf-8", "replace"), keep_blank_values=True)
        return {k: v[0] for k, v in parsed.items()}

    @staticmethod
    def number(value: str | None, default: int | None = None) -> int | None:
        """Form fields are text: anything that is not a positive number falls back."""
        value = (value or "").strip()
        return int(value) if value.isdigit() and int(value) > 0 else default

    def send(self, status: int, body: bytes, content_type: str, headers: list[tuple[str, str]] = ()) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "same-origin")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def html(self, markup: str, status: int = 200, headers=()) -> None:
        self.send(status, markup.encode(), "text/html; charset=utf-8", headers)

    def json(self, payload: dict, status: int = 200) -> None:
        self.send(status, json.dumps(payload).encode(), "application/json; charset=utf-8")

    def redirect(self, location: str, headers=()) -> None:
        self.send(HTTPStatus.SEE_OTHER, b"", "text/plain", [("Location", location), *headers])

    # --- session ------------------------------------------------------------

    def _sign(self, expiry: int) -> str:
        mac = hmac.new(self.db.secret(), str(expiry).encode(), sha256).hexdigest()
        return f"{expiry}.{mac}"

    def _session_cookie(self, value: str, ttl: int) -> tuple[str, str]:
        # Only when the request really arrived over TLS: a Secure cookie sent over plain
        # HTTP is dropped by the browser, which would loop the login form forever.
        https = self.headers.get("X-Forwarded-Proto", "") == "https"
        flags = "; Secure" if self.config.behind_proxy and https else ""
        return (
            "Set-Cookie",
            f"{SESSION_COOKIE}={value}; Path=/; Max-Age={ttl}; HttpOnly; SameSite=Strict{flags}",
        )

    def authenticated(self) -> bool:
        raw = SimpleCookie(self.headers.get("Cookie", "")).get(SESSION_COOKIE)
        if raw is None or "." not in raw.value:
            return False
        expiry, _, _ = raw.value.partition(".")
        if not expiry.isdigit() or int(expiry) < time.time():
            return False
        return hmac.compare_digest(self._sign(int(expiry)), raw.value)

    # --- routing ------------------------------------------------------------

    def handle_one_request(self) -> None:
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception:
            traceback.print_exc()
            self.close_connection = True
            try:
                self.send(500, b"", "text/plain")
            except Exception:
                pass

    def do_GET(self) -> None:
        self._body = None
        path = urlparse(self.path).path
        if path == "/style.css":
            # Revalidate: the stylesheet ships inside the binary and changes with upgrades,
            # so a cached copy would outlive the version it belongs to.
            return self.send(200, views.CSS.encode(), "text/css; charset=utf-8",
                             [("Cache-Control", "no-cache")])
        if path == "/healthz":
            return self.json({"ok": True})
        if path == "/login":
            return self.html(views.login_page())
        if not self.authenticated():
            return self.redirect("/login")
        if path == "/":
            return self.html(self.render_dashboard())
        if path == "/apps/new":
            return self.html(views.new_app(self.db.apps()))
        if path == "/backup":
            return self.html(self.render_backup())
        if path == "/backup.db.gz":
            return self.send(200, dump(self.db), "application/gzip",
                             [("Content-Disposition", f'attachment; filename="{filename()}"')])
        if path == "/global":
            return self.html(self.render_app(None, None, fresh=self.query("batch")))
        if path == "/global/codes.csv":
            return self.codes_csv(None)
        if path.startswith("/a/") and path.endswith("/codes.csv"):
            return self.codes_csv(path[3:-10])
        if path.startswith("/a/"):
            app = self.db.app(path[3:])
            if app is None:
                return self.html(views.not_found(self.db.apps()), 404)
            return self.html(self.render_app(app, app["slug"], fresh=self.query("batch")))
        if path.startswith("/c/"):
            code = self.db.code(path[3:])
            if code is None:
                return self.html(views.not_found(self.db.apps()), 404)
            name = code["id"]
            return self.html(
                views.code_page(
                    code,
                    self.db.apps(),
                    self.db.redemptions(code=name),
                    self.db.breakdown("platform", code=name),
                    self.db.breakdown("country", code=name),
                    self.db.code_apps(name),
                    self.db.breakdown("app_slug", code=name, limit=10000),
                )
            )
        return self.html(views.not_found(self.db.apps()), 404)

    do_HEAD = do_GET

    def do_POST(self) -> None:
        self._body = None
        path = urlparse(self.path).path
        self.limit = MAX_UPLOAD if path == "/restore" else MAX_BODY
        self.body()
        if path == "/v1/redeem":
            return self.api_redeem()
        if path == "/login":
            return self.login()
        if not self.authenticated():
            return self.redirect("/login")
        if path == "/logout":
            return self.redirect("/login", [self._session_cookie("", 0)])
        if path == "/apps":
            return self.create_app()
        if path == "/restore":
            return self.restore()
        if path == "/global/codes":
            return self.create_codes(None)
        if path.startswith("/a/") and path.endswith("/codes"):
            return self.create_codes(path[3:-6])
        if path.startswith("/a/") and path.endswith("/delete"):
            self.db.delete_app(path[3:-7])
            return self.redirect("/")
        if path.startswith("/c/") and path.endswith("/delete"):
            code = self.db.code(path[3:-7])
            if code is None:
                return self.html(views.not_found(self.db.apps()), 404)
            self.db.delete_code(code["id"])
            return self.redirect("/")
        if path.startswith("/c/") and path.endswith("/toggle"):
            code = self.db.code(path[3:-7])
            if code is None:
                return self.html(views.not_found(self.db.apps()), 404)
            self.db.set_enabled(code["id"], not code["enabled"])
            return self.redirect(self.back())
        if path.startswith("/c/"):
            return self.update_code(path[3:])
        return self.html(views.not_found(self.db.apps()), 404)

    # --- api ----------------------------------------------------------------

    def api_redeem(self) -> None:
        # The IP rate limits the request and is then forgotten: what a redemption keeps is
        # only what the app chose to send.
        if not self.server.limiter.allow("ip", self.client_ip(), 30, 60):
            return self.json({"granted": False, "reason": "rate_limited"}, 429)
        try:
            payload = json.loads(self.body() or b"{}")
            app_slug = str(payload["app"]).strip().lower()
            code = str(payload["code"])
        except (ValueError, KeyError, TypeError, AttributeError):
            return self.json({"granted": False, "reason": "bad_request"}, 400)
        device_id = clean(payload.get("device_id"), DEVICE)
        nonce = clean(payload.get("nonce"), NONCE)
        # Exactly one: a device id identifies repeat redemptions, a nonce only a retry.
        if not app_slug or bool(device_id) == bool(nonce):
            return self.json({"granted": False, "reason": "bad_request"}, 400)
        context = {
            "platform": clean(payload.get("platform"), PLATFORM, lambda v: v.strip().lower()),
            "app_version": clean(payload.get("app_version"), VERSION),
            "country": self.country(payload.get("country")),
        }
        if device_id is not None:
            if not self.server.limiter.allow("device", device_id, 30, 3600):
                return self.json({"granted": False, "reason": "rate_limited"}, 429)
            granted, reason = self.db.redeem(app_slug, code, device_id, **context)
        else:
            granted, reason = self.redeem_once(app_slug, code, nonce, context)
        return self.json({"granted": granted, "reason": reason})

    def redeem_once(self, app_slug: str, code: str, nonce: str, context: dict) -> tuple[bool, str]:
        """Anonymous redemption, guarded by the nonce so a retry cannot spend a second use."""
        key = f"{app_slug}/{normalize_code(code)}/{nonce}"
        with self.server.nonces.lock:
            seen = self.server.nonces.get(key)
            if seen is not None:
                return (True, "already") if seen[0] else seen
            result = self.db.redeem(app_slug, code, **context)
            self.server.nonces.put(key, result)
            return result

    def back(self) -> str:
        """Referer is attacker-controlled, so only its path is ever followed."""
        path = urlparse(self.headers.get("Referer", "")).path
        return path if path.startswith("/") else "/"

    def country(self, sent) -> str | None:
        """Behind a proxy its header wins: the device only knows its own region. Direct
        requests could forge that header, so there it is ignored."""
        header = (
            clean(self.headers.get("CF-IPCountry"), COUNTRY, lambda v: v.strip().upper())
            if self.config.behind_proxy
            else None
        )
        return header or clean(sent, COUNTRY, lambda v: v.strip().upper())

    # --- panel actions ------------------------------------------------------

    def login(self) -> None:
        password = self.form().get("password", "")
        if not self.config.password:
            return self.html(views.login_page("REDEEMER_ADMIN_PASSWORD is not set."), 500)
        if not self.server.limiter.allow("login", self.client_ip(), 10, 300):
            return self.html(views.login_page("Too many attempts."), 429)
        if not hmac.compare_digest(password, self.config.password):
            return self.html(views.login_page("Wrong password."), 401)
        cookie = self._sign(int(time.time()) + SESSION_TTL)
        return self.redirect("/", [self._session_cookie(cookie, SESSION_TTL)])

    def create_app(self) -> None:
        data = self.form()
        try:
            slug = self.db.add_app(data.get("slug", ""), data.get("name", ""))
        except ValueError as error:
            return self.html(views.new_app(self.db.apps(), data, str(error)), 400)
        return self.redirect(f"/a/{slug}")

    def create_codes(self, app_slug: str | None) -> None:
        if app_slug is not None and self.db.app(app_slug) is None:
            return self.html(views.not_found(self.db.apps()), 404)
        data = self.form()
        target = f"/a/{app_slug}" if app_slug else "/global"
        quantity = min(500, self.number(data.get("quantity"), 1))
        custom = normalize_code(data.get("code", ""))
        options = {
            "quota_mode": data.get("quota_mode", "shared"),
            "note": data.get("note", ""),
            "max_uses": self.number(data.get("max_uses")),
            "expires_at": self.expiry(data.get("expires_at")),
            "platforms": data.get("platforms", ""),
        }
        batch = generate_batch()
        try:
            scope = data.get("scope", "selected" if app_slug else "global")
            if scope not in ("selected", "global"):
                raise ValueError("Choose selected apps or all apps.")
            targets = [key[4:] for key, value in data.items() if key.startswith("app:") and value == "1"]
            if "scope" not in data and app_slug:
                targets = [app_slug]
            if scope == "selected":
                options["app_slugs"] = targets
                if targets:
                    target = f"/a/{targets[0]}"
            else:
                target = "/global"
            for _ in range(1 if custom else quantity):
                self.db.add_code(custom or generate_code(), batch=batch, **options)
        except ValueError as error:
            app = self.db.app(app_slug) if app_slug else None
            return self.html(self.render_app(app, app_slug, values=data, error=str(error)), 400)
        return self.redirect(f"{target}?batch={batch}")

    @staticmethod
    def expiry(value: str | None) -> str | None:
        """A date input gives a day; a code lives until the end of it."""
        return f"{value}T23:59:59Z" if value else None

    def render_dashboard(self) -> str:
        return views.dashboard(
            self.db.totals(),
            self.db.apps(),
            self.db.breakdown("platform"),
            self.db.breakdown("country"),
            self.db.redemptions(limit=25),
        )

    def render_app(self, app, app_slug, values=None, error: str = "", fresh: str = "") -> str:
        scope = {"app_slug": app_slug} if app_slug else {"only_global": True}
        return views.app_page(
            app,
            self.db.apps(),
            self.db.codes(app_slug),
            self.db.redemptions(limit=25, **scope),
            self.db.breakdown("platform", **scope),
            self.db.breakdown("country", **scope),
            values,
            error,
            fresh,
            len(self.db.codes(app_slug, batch=fresh)) if fresh else 0,
        )

    def codes_csv(self, app_slug: str | None) -> None:
        if app_slug is not None and self.db.app(app_slug) is None:
            return self.html(views.not_found(self.db.apps()), 404)
        rows = ["code,note,uses,max_uses,expires_at,enabled,quota_mode,apps"]
        for c in self.db.codes(app_slug, batch=self.query("batch")):
            note = c["note"].replace('"', '""')
            rows.append(
                f'{c["code"]},"{note}",{c["uses"]},{c["max_uses"] if c["max_uses"] is not None else ""},'
                f'{c["expires_at"] or ""},{"yes" if c["enabled"] else "no"},{c["quota_mode"]},'
                f'{"all" if c["is_global"] else ";".join(self.db.code_apps(c["id"]))}'
            )
        name = f"{app_slug or 'global'}-codes.csv"
        self.send(
            200,
            "\n".join(rows).encode(),
            "text/csv; charset=utf-8",
            [("Content-Disposition", f'attachment; filename="{name}"')],
        )

    def render_backup(self, error: str = "") -> str:
        files = sorted(Path(self.config.backup_dir).glob("redeemer-*.db.gz"))
        latest = (
            f"{datetime.fromtimestamp(files[-1].stat().st_mtime, timezone.utc):%Y-%m-%d %H:%M}"
            if files else ""
        )
        return views.backup_page(self.db.apps(), len(files), latest, error)

    def restore(self) -> None:
        try:
            snapshot(self.db, self.config.backup_dir, self.config.backup_keep)
            load(self.db, self.upload("file"))
        except ValueError as error:
            return self.html(self.render_backup(str(error)), 400)
        return self.redirect("/")

    def update_code(self, code: str) -> None:
        if self.db.code(code) is None:
            return self.html(views.not_found(self.db.apps()), 404)
        data = self.form()
        try:
            self.db.update_code(
                code,
                note=data.get("note", ""),
                max_uses=self.number(data.get("max_uses")),
                expires_at=self.expiry(data.get("expires_at")),
                platforms=data.get("platforms", ""),
                enabled=data.get("enabled") == "1",
                quota_mode=data.get("quota_mode", "shared"),
            )
        except ValueError:
            return self.html(views.not_found(self.db.apps()), 400)
        return self.redirect(f"/c/{code}")


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, config: Config) -> None:
        super().__init__((config.host, config.port), Handler)
        self.config = config
        self.db = Database(config.db_path)
        self.limiter = RateLimiter()
        self.nonces = Nonces()


def serve(config: Config | None = None) -> None:
    config = config or Config()
    if not config.password:
        raise SystemExit("REDEEMER_ADMIN_PASSWORD is not set")
    server = Server(config)
    if config.backup_hours > 0:
        schedule(config.db_path, config.backup_dir, config.backup_keep, config.backup_hours * 3600)
    print(f"redeemer http://{config.host}:{config.port} db={config.db_path}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
