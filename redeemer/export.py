from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone

from .db import Database

FORMATS = {"csv": "CSV", "json": "JSON", "txt": "Code list"}
DATASETS = {"codes": "Codes", "redemptions": "Redemptions", "apps": "Apps"}
SCOPES = {"all": "All apps", "selected": "Selected apps"}
STATUS = {"all": "All", "active": "Active", "disabled": "Disabled", "unused": "Never redeemed"}

COLUMNS = {
    "codes": ("code", "note", "uses", "max_uses", "expires_at", "enabled", "quota_mode",
              "apps", "created_at"),
    "redemptions": ("redeemed_at", "app", "code", "platform", "app_version", "country",
                    "device_id"),
    "apps": ("slug", "name", "created_at", "redemptions"),
}

TYPES = {
    "csv": "text/csv; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "txt": "text/plain; charset=utf-8",
    "zip": "application/zip",
}


def filename(suffix: str) -> str:
    return f"redeemer-export-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.{suffix}"


def collect(
    db: Database,
    *,
    datasets,
    slugs=None,
    only_global: bool = False,
    status: str = "all",
    since: str | None = None,
    until: str | None = None,
    devices: bool = True,
    batch: str | None = None,
) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    if "codes" in datasets:
        tables["codes"] = [
            {
                "code": row["code"],
                "note": row["note"],
                "uses": row["uses"],
                "max_uses": row["max_uses"],
                "expires_at": row["expires_at"],
                "enabled": bool(row["enabled"]),
                "quota_mode": row["quota_mode"],
                "apps": "all" if row["is_global"] else (row["app_names"] or ""),
                "created_at": row["created_at"],
            }
            for row in db.export_codes(slugs=slugs, only_global=only_global,
                                       status=status, batch=batch)
        ]
    if "redemptions" in datasets:
        tables["redemptions"] = [
            {
                "redeemed_at": row["redeemed_at"],
                "app": row["app_slug"],
                "code": row["code"],
                "platform": row["platform"],
                "app_version": row["app_version"],
                "country": row["country"],
                **({"device_id": row["device_id"]} if devices else {}),
            }
            for row in db.export_redemptions(slugs=slugs, since=since, until=until)
        ]
    if "apps" in datasets:
        tables["apps"] = [dict(row) for row in db.export_apps(slugs)]
    return tables


def build(db: Database, *, fmt: str, datasets, devices: bool = True, **filters):
    """Returns the payload, the extension it should be saved under and its content type."""
    if fmt not in FORMATS:
        raise ValueError("Unknown format.")
    chosen = ["codes"] if fmt == "txt" else [name for name in DATASETS if name in datasets]
    if not chosen:
        raise ValueError("Choose what to export.")
    tables = collect(db, datasets=chosen, devices=devices, **filters)
    if fmt == "json":
        return json.dumps(tables, indent=2).encode(), "json", TYPES["json"]
    if fmt == "txt":
        return "\n".join(row["code"] for row in tables["codes"]).encode(), "txt", TYPES["txt"]
    if len(tables) == 1:
        name, rows = next(iter(tables.items()))
        return _csv(name, rows, devices).encode(), "csv", TYPES["csv"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, rows in tables.items():
            archive.writestr(f"{name}.csv", _csv(name, rows, devices))
    return buffer.getvalue(), "zip", TYPES["zip"]


def _csv(name: str, rows: list[dict], devices: bool) -> str:
    columns = [c for c in COLUMNS[name] if devices or c != "device_id"]
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_cell(row[c]) for c in columns])
    return out.getvalue()


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return value
