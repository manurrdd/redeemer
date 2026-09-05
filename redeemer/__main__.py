from __future__ import annotations

import sys

from .backup import snapshot
from .db import Database
from .server import Config, serve

USAGE = "usage: python3 -m redeemer [serve | backup [directory]]"


def main(argv: list[str]) -> None:
    command = argv[1] if len(argv) > 1 else "serve"
    if command == "serve":
        serve()
    elif command == "backup":
        config = Config()
        directory = argv[2] if len(argv) > 2 else config.backup_dir
        print(snapshot(Database(config.db_path), directory, config.backup_keep), flush=True)
    else:
        raise SystemExit(USAGE)


if __name__ == "__main__":
    main(sys.argv)
