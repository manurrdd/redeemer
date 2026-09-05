from __future__ import annotations

import gzip
import tempfile
import threading
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path

from .db import Database


def filename() -> str:
    return f"redeemer-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.db.gz"


def dump(db: Database) -> bytes:
    """Consistent copy, safe to take while the server is running."""
    with tempfile.TemporaryDirectory() as tmp:
        return gzip.compress(db.backup_to(Path(tmp) / "snapshot.db").read_bytes())


def load(db: Database, payload: bytes) -> None:
    """Restore either form of snapshot: the compressed download or a plain database file."""
    if payload[:2] == b"\x1f\x8b":
        try:
            payload = gzip.decompress(payload)
        except (OSError, EOFError, zlib.error) as error:
            raise ValueError("Damaged backup file.") from error
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "restore.db"
        path.write_bytes(payload)
        db.restore_from(path)


def snapshot(db: Database, directory: str | Path, keep: int = 14) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / filename()
    target.write_bytes(dump(db))
    for old in sorted(directory.glob("redeemer-*.db.gz"))[:-keep]:
        old.unlink()
    return target


def schedule(db_path: str | Path, directory: str | Path, keep: int, interval: float) -> None:
    """Daily snapshot from inside the process: no cron, no systemd timer."""

    def loop() -> None:
        db = Database(db_path)
        while True:
            time.sleep(interval)
            try:
                print(f"backup {snapshot(db, directory, keep)}", flush=True)
            except Exception as error:
                print(f"backup failed: {error}", flush=True)

    threading.Thread(target=loop, daemon=True).start()
