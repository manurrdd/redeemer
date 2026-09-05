from __future__ import annotations

import re
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS apps (
    slug       TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS codes (
    code       TEXT PRIMARY KEY,
    app_slug   TEXT REFERENCES apps(slug) ON DELETE CASCADE,
    note       TEXT NOT NULL DEFAULT '',
    max_uses   INTEGER,
    expires_at TEXT,
    platforms  TEXT,
    batch      TEXT,
    enabled    INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS redemptions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL REFERENCES codes(code) ON DELETE CASCADE,
    app_slug    TEXT NOT NULL,
    device_id   TEXT,
    redeemed_at TEXT NOT NULL,
    platform    TEXT,
    app_version TEXT,
    country     TEXT,
    UNIQUE (code, app_slug, device_id)
);

CREATE INDEX IF NOT EXISTS codes_by_app ON codes(app_slug);
CREATE INDEX IF NOT EXISTS codes_by_batch ON codes(batch);
CREATE INDEX IF NOT EXISTS redemptions_by_code ON redemptions(code);
CREATE INDEX IF NOT EXISTS redemptions_by_app ON redemptions(app_slug);
CREATE INDEX IF NOT EXISTS redemptions_by_time ON redemptions(redeemed_at DESC);
"""

# No 0/O/1/I: generated codes get read aloud and typed by hand.
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

DEVICE = re.compile(r"^[\x21-\x7e]{1,128}$")
NONCE = DEVICE
SLUG = re.compile(r"^[a-z0-9][a-z0-9.-]{1,63}$")
CODE = re.compile(r"^[A-Z0-9-]{4,32}$")
PLATFORM = re.compile(r"^[a-z0-9_.-]{1,16}$")
VERSION = re.compile(r"^[A-Za-z0-9_.+-]{1,32}$")
COUNTRY = re.compile(r"^[A-Z]{2}$")

BREAKDOWN_FIELDS = ("platform", "country", "app_version")

# What a code may be restricted to. None means any platform, including ones not listed here.
PLATFORM_SCOPES = {
    "": None,
    "ios": ("ios",),
    "android": ("android",),
    "ios,android": ("ios", "android"),
}


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_code(code: str) -> str:
    return re.sub(r"\s+", "", code or "").upper()


def generate_code(length: int = 10) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def generate_batch() -> str:
    """Marks the codes made by one submit, so the panel can point them out afterwards."""
    return secrets.token_hex(4)


def clean(value, pattern: re.Pattern[str], transform=str.strip) -> str | None:
    """Optional client-sent field: kept only when it matches, dropped otherwise."""
    if not isinstance(value, str):
        return None
    value = transform(value)
    return value if pattern.match(value) else None


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self.conn.executescript(SCHEMA)

    @property
    def conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.path, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA busy_timeout = 5000")
            self._local.conn = conn
        return conn

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    def secret(self) -> bytes:
        self.conn.execute(
            "INSERT OR IGNORE INTO meta (key, value) VALUES ('secret', ?)",
            (secrets.token_hex(32),),
        )
        row = self.conn.execute("SELECT value FROM meta WHERE key = 'secret'").fetchone()
        return bytes.fromhex(row["value"])

    def backup_to(self, destination: str | Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        target = sqlite3.connect(destination)
        try:
            self.conn.backup(target)
        finally:
            target.close()
        return destination

    # --- apps ---------------------------------------------------------------

    def add_app(self, slug: str, name: str) -> str:
        slug = (slug or "").strip().lower()
        if not SLUG.match(slug):
            raise ValueError("Slug must be 2-64 chars: lowercase letters, digits, dots and dashes.")
        if self.app(slug) is not None:
            raise ValueError(f"App '{slug}' already exists.")
        self.conn.execute(
            "INSERT INTO apps (slug, name, created_at) VALUES (?, ?, ?)",
            (slug, (name or slug).strip(), utcnow()),
        )
        return slug

    def delete_app(self, slug: str) -> None:
        self.conn.execute("DELETE FROM apps WHERE slug = ?", (slug,))

    def app(self, slug: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM apps WHERE slug = ?", (slug,)).fetchone()

    def apps(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT a.*,
                   (SELECT COUNT(*) FROM codes c WHERE c.app_slug = a.slug) AS code_count,
                   (SELECT COUNT(*) FROM redemptions r WHERE r.app_slug = a.slug) AS redemption_count
              FROM apps a
             ORDER BY a.name COLLATE NOCASE
            """
        ).fetchall()

    def totals(self) -> sqlite3.Row:
        return self.conn.execute(
            """
            SELECT (SELECT COUNT(*) FROM apps) AS apps,
                   (SELECT COUNT(*) FROM codes) AS codes,
                   (SELECT COUNT(*) FROM codes WHERE enabled = 1) AS active_codes,
                   (SELECT COUNT(*) FROM redemptions) AS redemptions,
                   (SELECT COUNT(DISTINCT device_id) FROM redemptions
                     WHERE device_id IS NOT NULL) AS devices
            """
        ).fetchone()

    # --- codes --------------------------------------------------------------

    def add_code(
        self,
        code: str,
        app_slug: str | None,
        *,
        note: str = "",
        max_uses: int | None = None,
        expires_at: str | None = None,
        platforms: str | None = None,
        batch: str | None = None,
    ) -> str:
        code = normalize_code(code)
        if not CODE.match(code):
            raise ValueError("Code must be 4-32 chars: A-Z, 0-9 and dashes.")
        if app_slug is not None and self.app(app_slug) is None:
            raise ValueError("Unknown app.")
        if self.conn.execute("SELECT 1 FROM codes WHERE code = ?", (code,)).fetchone():
            raise ValueError(f"Code '{code}' already exists.")
        if (platforms or "") not in PLATFORM_SCOPES:
            raise ValueError("Unknown platform scope.")
        self.conn.execute(
            """
            INSERT INTO codes (code, app_slug, note, max_uses, expires_at, platforms,
                               batch, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (code, app_slug, note.strip(), max_uses, expires_at or None,
             platforms or None, batch, utcnow()),
        )
        return code

    def update_code(
        self,
        code: str,
        *,
        note: str,
        max_uses: int | None,
        expires_at: str | None,
        platforms: str | None,
        enabled: bool,
    ) -> None:
        if (platforms or "") not in PLATFORM_SCOPES:
            raise ValueError("Unknown platform scope.")
        self.conn.execute(
            """
            UPDATE codes SET note = ?, max_uses = ?, expires_at = ?, platforms = ?, enabled = ?
             WHERE code = ?
            """,
            (note.strip(), max_uses, expires_at or None, platforms or None,
             1 if enabled else 0, code),
        )

    def set_enabled(self, code: str, enabled: bool) -> None:
        self.conn.execute("UPDATE codes SET enabled = ? WHERE code = ?", (1 if enabled else 0, code))

    def delete_code(self, code: str) -> None:
        self.conn.execute("DELETE FROM codes WHERE code = ?", (normalize_code(code),))

    def code(self, code: str) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT c.*, (SELECT COUNT(*) FROM redemptions r WHERE r.code = c.code) AS uses
              FROM codes c WHERE c.code = ?
            """,
            (normalize_code(code),),
        ).fetchone()

    def codes(self, app_slug: str | None, *, batch: str | None = None) -> list[sqlite3.Row]:
        where = ["c.app_slug IS NULL" if app_slug is None else "c.app_slug = ?"]
        params = [] if app_slug is None else [app_slug]
        if batch:
            where.append("c.batch = ?")
            params.append(batch)
        return self.conn.execute(
            f"""
            SELECT c.*, (SELECT COUNT(*) FROM redemptions r WHERE r.code = c.code) AS uses
              FROM codes c WHERE {" AND ".join(where)}
             ORDER BY c.created_at DESC, c.code
            """,
            params,
        ).fetchall()

    # --- redemptions --------------------------------------------------------

    @staticmethod
    def _scope(code: str | None, app_slug: str | None, only_global: bool) -> tuple[str, list]:
        """Which redemptions a view is about: one code, one app, or the global codes."""
        if code is not None:
            return "WHERE code = ?", [normalize_code(code)]
        if app_slug is not None:
            return "WHERE app_slug = ?", [app_slug]
        if only_global:
            return "WHERE code IN (SELECT code FROM codes WHERE app_slug IS NULL)", []
        return "", []

    def redemptions(
        self,
        *,
        code: str | None = None,
        app_slug: str | None = None,
        only_global: bool = False,
        limit: int = 50,
    ) -> list[sqlite3.Row]:
        where, params = self._scope(code, app_slug, only_global)
        return self.conn.execute(
            f"SELECT * FROM redemptions {where} ORDER BY redeemed_at DESC, id DESC LIMIT ?",
            [*params, limit],
        ).fetchall()

    def breakdown(
        self,
        field: str,
        *,
        code: str | None = None,
        app_slug: str | None = None,
        only_global: bool = False,
        limit: int = 8,
    ) -> list[sqlite3.Row]:
        """Redemption counts grouped by platform, country or app_version."""
        if field not in BREAKDOWN_FIELDS:
            raise ValueError("Unknown field.")
        where, params = self._scope(code, app_slug, only_global)
        return self.conn.execute(
            f"""
            SELECT COALESCE({field}, '?') AS value, COUNT(*) AS count
              FROM redemptions {where}
             GROUP BY value ORDER BY count DESC, value LIMIT ?
            """,
            [*params, limit],
        ).fetchall()

    def redeem(
        self,
        app_slug: str,
        code: str,
        device_id: str | None = None,
        *,
        platform: str | None = None,
        app_version: str | None = None,
        country: str | None = None,
    ) -> tuple[bool, str]:
        """Validate and consume one use. Reasons are documented in docs/INTEGRATION.md.

        Without a device_id the redemption is anonymous: nothing links it to whoever made
        it, and repeat redemptions can no longer be recognised.
        """
        code = normalize_code(code)
        conn = self.conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            if conn.execute("SELECT 1 FROM apps WHERE slug = ?", (app_slug,)).fetchone() is None:
                return False, "unknown_app"
            row = conn.execute("SELECT * FROM codes WHERE code = ?", (code,)).fetchone()
            if row is None:
                return False, "unknown"
            if row["app_slug"] is not None and row["app_slug"] != app_slug:
                return False, "wrong_app"
            # A platform-scoped code cannot be granted to a request that did not say which
            # platform it came from: there would be nothing to check it against.
            if row["platforms"] and platform not in row["platforms"].split(","):
                return False, "wrong_platform"
            if not row["enabled"]:
                return False, "disabled"
            if row["expires_at"] and utcnow() > row["expires_at"]:
                return False, "expired"
            if device_id is not None:
                already = conn.execute(
                    "SELECT 1 FROM redemptions WHERE code = ? AND app_slug = ? AND device_id = ?",
                    (code, app_slug, device_id),
                ).fetchone()
                if already is not None:
                    return True, "already"
            if row["max_uses"] is not None:
                used = conn.execute(
                    "SELECT COUNT(*) AS n FROM redemptions WHERE code = ?", (code,)
                ).fetchone()["n"]
                if used >= row["max_uses"]:
                    return False, "exhausted"
            conn.execute(
                """
                INSERT INTO redemptions
                       (code, app_slug, device_id, redeemed_at, platform, app_version, country)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (code, app_slug, device_id, utcnow(), platform, app_version, country),
            )
            return True, "ok"
        finally:
            conn.execute("COMMIT")
