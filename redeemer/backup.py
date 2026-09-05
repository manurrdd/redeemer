from __future__ import annotations

import gzip
import shutil
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .db import Database


def snapshot(db: Database, directory: str | Path, keep: int = 14) -> Path:
    """Consistent copy, safe to take while the server is running."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = directory / f"redeemer-{stamp}.db.gz"
    with tempfile.TemporaryDirectory() as tmp:
        raw = db.backup_to(Path(tmp) / "snapshot.db")
        with open(raw, "rb") as source, gzip.open(target, "wb") as packed:
            shutil.copyfileobj(source, packed)
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
