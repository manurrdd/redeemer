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
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT NOT NULL,
    is_global  INTEGER NOT NULL DEFAULT 0 CHECK (is_global IN (0, 1)),
    quota_mode TEXT NOT NULL DEFAULT 'shared' CHECK (quota_mode IN ('shared', 'per_app')),
    note       TEXT NOT NULL DEFAULT '',
    max_uses   INTEGER,
    expires_at TEXT,
    platforms  TEXT,
    batch      TEXT,
    enabled    INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS code_apps (
    code_id INTEGER NOT NULL REFERENCES codes(id) ON DELETE CASCADE,
    app_slug TEXT NOT NULL REFERENCES apps(slug) ON DELETE CASCADE,
    PRIMARY KEY (code_id, app_slug)
);

CREATE TABLE IF NOT EXISTS redemptions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code_id     INTEGER NOT NULL REFERENCES codes(id) ON DELETE CASCADE,
    app_slug    TEXT NOT NULL,
    device_id   TEXT,
    redeemed_at TEXT NOT NULL,
    platform    TEXT,
    app_version TEXT,
    country     TEXT,
    UNIQUE (code_id, app_slug, device_id)
);

CREATE INDEX IF NOT EXISTS codes_by_text ON codes(code);
CREATE INDEX IF NOT EXISTS code_apps_by_app ON code_apps(app_slug);
CREATE INDEX IF NOT EXISTS codes_by_batch ON codes(batch);
CREATE INDEX IF NOT EXISTS redemptions_by_code ON redemptions(code_id);
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

BREAKDOWN_FIELDS = ("platform", "country", "app_version", "app_slug")

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
        columns = {r["name"] for r in self.conn.execute("PRAGMA table_info(codes)")}
        if columns and not {"id", "is_global", "quota_mode"} <= columns:
            self.close()
            raise ValueError("Unsupported database schema. Start with a new database file.")
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

    def restore_from(self, source: str | Path) -> None:
        """Copy a snapshot over the live database.

        Content is replaced through SQLite itself, so connections held by other threads keep
        working and the file is never swapped underneath them. The session secret is carried
        over from the database being replaced: a snapshot from another install would
        otherwise sign the panel out mid-restore.
        """
        incoming = sqlite3.connect(source)
        try:
            tables = {
                row[0]
                for row in incoming.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            if not {"meta", "apps", "codes", "code_apps", "redemptions"} <= tables:
                raise ValueError("Not a Redeemer backup.")
            for table, columns in {
                "codes": {"id", "code", "is_global", "quota_mode", "note", "max_uses", "expires_at", "platforms", "batch", "enabled", "created_at"},
                "code_apps": {"code_id", "app_slug"},
                "redemptions": {"id", "code_id", "app_slug", "device_id", "redeemed_at", "platform", "app_version", "country"},
                "apps": {"slug", "name", "created_at"}, "meta": {"key", "value"},
            }.items():
                if not columns <= {r[1] for r in incoming.execute(f"PRAGMA table_info({table})")}:
                    raise ValueError("Not a Redeemer backup.")
            if incoming.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or incoming.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Not a Redeemer backup.")
            secret = self.conn.execute("SELECT value FROM meta WHERE key = 'secret'").fetchone()
            incoming.backup(self.conn)
        except sqlite3.DatabaseError as error:
            raise ValueError("Not a Redeemer backup.") from error
        finally:
            incoming.close()
        self.conn.executescript(SCHEMA)
        if secret is not None:
            self.conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('secret', ?)", (secret["value"],)
            )

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
        conn = self.conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("DELETE FROM apps WHERE slug = ?", (slug,))
            conn.execute("DELETE FROM codes WHERE is_global = 0 AND NOT EXISTS (SELECT 1 FROM code_apps WHERE code_id = codes.id)")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def app(self, slug: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT apps.*, (SELECT COUNT(*) FROM redemptions WHERE app_slug = apps.slug) AS redemption_count FROM apps WHERE slug = ?", (slug,)).fetchone()

    def apps(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT a.*,
                   (SELECT COUNT(*) FROM codes c WHERE c.is_global = 1 OR EXISTS (SELECT 1 FROM code_apps ca WHERE ca.code_id = c.id AND ca.app_slug = a.slug)) AS code_count,
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
        self, code: str, app_slug: str | None = None, *,
        app_slugs: list[str] | None = None, quota_mode: str = "shared",
        note: str = "", max_uses: int | None = None,
        expires_at: str | None = None, platforms: str | None = None,
        batch: str | None = None,
    ) -> int:
        """Create a code for selected apps, or all apps when neither scope is supplied."""
        code = normalize_code(code)
        if not CODE.match(code):
            raise ValueError("Code must be 4-32 chars: A-Z, 0-9 and dashes.")
        if app_slug is not None and app_slugs is not None:
            raise ValueError("Choose one app scope.")
        targets = sorted(set(app_slugs if app_slugs is not None else ([app_slug] if app_slug is not None else [])))
        is_global = app_slug is None and app_slugs is None
        if not is_global and not targets:
            raise ValueError("Select at least one app.")
        self._validate_options(platforms, quota_mode, max_uses)
        conn = self.conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            for slug in targets:
                if self.app(slug) is None:
                    raise ValueError("Unknown app.")
            for existing in conn.execute("SELECT id, is_global FROM codes WHERE code = ?", (code,)):
                if is_global or existing["is_global"] or any(
                    conn.execute("SELECT 1 FROM code_apps WHERE code_id = ? AND app_slug = ?", (existing["id"], slug)).fetchone()
                    for slug in targets
                ):
                    raise ValueError(f"Code '{code}' already applies to one of these apps; global codes cannot overlap any app code.")
            cursor = conn.execute(
                """INSERT INTO codes (code, is_global, quota_mode, note, max_uses,
                                      expires_at, platforms, batch, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (code, int(is_global), quota_mode, note.strip(), max_uses,
                 expires_at or None, platforms or None, batch, utcnow()),
            )
            code_id = cursor.lastrowid
            conn.executemany("INSERT INTO code_apps (code_id, app_slug) VALUES (?, ?)",
                             [(code_id, slug) for slug in targets])
            conn.execute("COMMIT")
            return code_id
        except Exception:
            conn.execute("ROLLBACK")
            raise

    @staticmethod
    def _validate_options(platforms, quota_mode, max_uses):
        if (platforms or "") not in PLATFORM_SCOPES:
            raise ValueError("Unknown platform scope.")
        if quota_mode not in ("shared", "per_app"):
            raise ValueError("Choose shared or per-app quota.")
        if max_uses is not None and (not isinstance(max_uses, int) or max_uses < 1):
            raise ValueError("Max uses must be positive.")

    def code_apps(self, code_id) -> list[str]:
        return [r["app_slug"] for r in self.conn.execute(
            "SELECT app_slug FROM code_apps WHERE code_id = ? ORDER BY app_slug", (code_id,))]

    def update_code(
        self,
        code: int | str,
        *,
        note: str,
        max_uses: int | None,
        expires_at: str | None,
        platforms: str | None,
        enabled: bool,
        quota_mode: str = "shared",
    ) -> None:
        self._validate_options(platforms, quota_mode, max_uses)
        self.conn.execute(
            """
            UPDATE codes SET note = ?, max_uses = ?, expires_at = ?, platforms = ?, enabled = ?, quota_mode = ?
             WHERE id = ?
            """,
            (note.strip(), max_uses, expires_at or None, platforms or None,
             1 if enabled else 0, quota_mode, code),
        )

    def set_enabled(self, code: int | str, enabled: bool) -> None:
        self.conn.execute("UPDATE codes SET enabled = ? WHERE id = ?", (1 if enabled else 0, code))

    def delete_code(self, code: int | str) -> None:
        self.conn.execute("DELETE FROM codes WHERE id = ?", (code,))

    def code(self, code: int | str) -> sqlite3.Row | None:
        return self.conn.execute(
            """
            SELECT c.*, (SELECT group_concat(app_slug, ", ") FROM code_apps WHERE code_id = c.id) AS app_names, (SELECT COUNT(*) FROM redemptions r WHERE r.code_id = c.id) AS uses
              FROM codes c WHERE c.id = ?
            """,
            (code,),
        ).fetchone()

    def codes(self, app_slug: str | None, *, batch: str | None = None) -> list[sqlite3.Row]:
        where = ["c.is_global = 1" if app_slug is None else "(c.is_global = 1 OR EXISTS (SELECT 1 FROM code_apps ca WHERE ca.code_id = c.id AND ca.app_slug = ?))"]
        params = [] if app_slug is None else [app_slug]
        if batch:
            where.append("c.batch = ?")
            params.append(batch)
        return self.conn.execute(
            f"""
            SELECT c.*, (SELECT group_concat(app_slug, ", ") FROM code_apps WHERE code_id = c.id) AS app_names, (SELECT COUNT(*) FROM redemptions r WHERE r.code_id = c.id) AS uses
              FROM codes c WHERE {" AND ".join(where)}
             ORDER BY c.created_at DESC, c.code
            """,
            params,
        ).fetchall()

    # --- redemptions --------------------------------------------------------

    @staticmethod
    def _scope(code: int | None, app_slug: str | None, only_global: bool) -> tuple[str, list]:
        """Which redemptions a view is about: one code, one app, or the global codes."""
        if code is not None:
            return "WHERE code_id = ?", [code]
        if app_slug is not None:
            return "WHERE app_slug = ?", [app_slug]
        if only_global:
            return "WHERE code_id IN (SELECT id FROM codes WHERE is_global = 1)", []
        return "", []

    def redemptions(
        self,
        *,
        code: int | None = None,
        app_slug: str | None = None,
        only_global: bool = False,
        limit: int = 50,
    ) -> list[sqlite3.Row]:
        where, params = self._scope(code, app_slug, only_global)
        return self.conn.execute(
            f"SELECT r.*, (SELECT code FROM codes WHERE id = r.code_id) AS code FROM redemptions r {where} ORDER BY redeemed_at DESC, id DESC LIMIT ?",
            [*params, limit],
        ).fetchall()

    def breakdown(
        self,
        field: str,
        *,
        code: int | None = None,
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
            row = conn.execute(
                """SELECT c.* FROM codes c WHERE c.code = ? AND
                   (c.is_global = 1 OR EXISTS (SELECT 1 FROM code_apps ca
                    WHERE ca.code_id = c.id AND ca.app_slug = ?))""", (code, app_slug)
            ).fetchone()
            if row is None:
                exists = conn.execute("SELECT 1 FROM codes WHERE code = ?", (code,)).fetchone()
                return False, "wrong_app" if exists else "unknown"
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
                    "SELECT 1 FROM redemptions WHERE code_id = ? AND app_slug = ? AND device_id = ?",
                    (row["id"], app_slug, device_id),
                ).fetchone()
                if already is not None:
                    return True, "already"
            if row["max_uses"] is not None:
                quota_filter = " AND app_slug = ?" if row["quota_mode"] == "per_app" else ""
                params = [row["id"], app_slug] if quota_filter else [row["id"]]
                used = conn.execute(
                    "SELECT COUNT(*) AS n FROM redemptions WHERE code_id = ?" + quota_filter, params
                ).fetchone()["n"]
                if used >= row["max_uses"]:
                    return False, "exhausted"
            conn.execute(
                """
                INSERT INTO redemptions
                       (code_id, app_slug, device_id, redeemed_at, platform, app_version, country)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (row["id"], app_slug, device_id, utcnow(), platform, app_version, country),
            )
            return True, "ok"
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            if conn.in_transaction:
                conn.execute("COMMIT")
