from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from redeemer.db import Database


def stamp(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


class RedeemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.db.add_app("99arcade", "99 Arcade")
        self.db.add_app("99puzzle", "99 Puzzle")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_grants_and_counts(self):
        self.db.add_code("FREE99", "99arcade")
        self.assertEqual(self.db.redeem("99arcade", "free99", "device-a"), (True, "ok"))
        self.assertEqual(self.db.code("FREE99")["uses"], 1)

    def test_same_device_does_not_consume_twice(self):
        self.db.add_code("FREE99", "99arcade", max_uses=1)
        self.db.redeem("99arcade", "FREE99", "device-a")
        self.assertEqual(self.db.redeem("99arcade", "FREE99", "device-a"), (True, "already"))
        self.assertEqual(self.db.code("FREE99")["uses"], 1)

    def test_exhausted(self):
        self.db.add_code("FREE99", "99arcade", max_uses=1)
        self.db.redeem("99arcade", "FREE99", "device-a")
        self.assertEqual(self.db.redeem("99arcade", "FREE99", "device-b"), (False, "exhausted"))

    def test_unlimited_by_default(self):
        self.db.add_code("FREE99", "99arcade")
        for i in range(5):
            self.assertTrue(self.db.redeem("99arcade", "FREE99", f"device-{i}")[0])

    def test_wrong_app(self):
        self.db.add_code("FREE99", "99arcade")
        self.assertEqual(self.db.redeem("99puzzle", "FREE99", "device-a"), (False, "wrong_app"))

    def test_global_code_works_everywhere_and_counts_per_app(self):
        self.db.add_code("PRESS", None, max_uses=2)
        self.assertTrue(self.db.redeem("99arcade", "PRESS", "device-a")[0])
        self.assertTrue(self.db.redeem("99puzzle", "PRESS", "device-a")[0])
        self.assertEqual(self.db.redeem("99arcade", "PRESS", "device-b"), (False, "exhausted"))

    def test_disabled(self):
        self.db.add_code("FREE99", "99arcade")
        self.db.set_enabled("FREE99", False)
        self.assertEqual(self.db.redeem("99arcade", "FREE99", "device-a"), (False, "disabled"))

    def test_expired(self):
        self.db.add_code("OLDX", "99arcade", expires_at=stamp(-1))
        self.db.add_code("SOON", "99arcade", expires_at=stamp(1))
        self.assertEqual(self.db.redeem("99arcade", "OLDX", "device-a"), (False, "expired"))
        self.assertTrue(self.db.redeem("99arcade", "SOON", "device-a")[0])

    def test_unknown_code_and_app(self):
        self.assertEqual(self.db.redeem("99arcade", "NOPE", "device-a"), (False, "unknown"))
        self.assertEqual(self.db.redeem("99relax", "NOPE", "device-a"), (False, "unknown_app"))

    def test_deleting_code_removes_its_redemptions(self):
        self.db.add_code("FREE99", "99arcade")
        self.db.redeem("99arcade", "FREE99", "device-a")
        self.db.delete_code("FREE99")
        self.assertEqual(self.db.redemptions(), [])

    def test_backup_is_readable(self):
        self.db.add_code("FREE99", "99arcade")
        copy = self.db.backup_to(Path(self.tmp.name) / "copy.db")
        restored = Database(copy)
        self.assertIsNotNone(restored.code("FREE99"))
        restored.close()


if __name__ == "__main__":
    unittest.main()


class MetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.db.add_app("99arcade", "99 Arcade")
        self.db.add_code("FREE99", "99arcade")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_stores_context(self):
        self.db.redeem("99arcade", "FREE99", "d1",
                       platform="ios", app_version="1.4.2", country="ES")
        row = self.db.redemptions()[0]
        self.assertEqual(
            (row["platform"], row["app_version"], row["country"]), ("ios", "1.4.2", "ES")
        )

    def test_no_ip_is_stored(self):
        self.db.redeem("99arcade", "FREE99", "d1")
        self.assertNotIn("ip", self.db.redemptions()[0].keys())

    def test_context_is_optional(self):
        self.db.redeem("99arcade", "FREE99", "d1")
        row = self.db.redemptions()[0]
        self.assertIsNone(row["platform"])
        self.assertIsNone(row["country"])

    def test_breakdown_groups_and_labels_unknown(self):
        self.db.add_code("OTHER", "99arcade")
        self.db.redeem("99arcade", "FREE99", "d1", platform="ios")
        self.db.redeem("99arcade", "FREE99", "d2", platform="ios")
        self.db.redeem("99arcade", "OTHER", "d3")
        rows = self.db.breakdown("platform", app_slug="99arcade")
        self.assertEqual([(r["value"], r["count"]) for r in rows], [("ios", 2), ("?", 1)])

    def test_breakdown_rejects_unknown_field(self):
        with self.assertRaises(ValueError):
            self.db.breakdown("device_id")

    def test_duplicate_app_and_code_are_rejected(self):
        with self.assertRaises(ValueError):
            self.db.add_app("99arcade", "Otra")
        with self.assertRaises(ValueError):
            self.db.add_code("FREE99", "99arcade")

    def test_deleting_app_removes_its_codes(self):
        self.db.delete_app("99arcade")
        self.assertIsNone(self.db.code("FREE99"))


class AnonymousTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.db")
        self.db.add_app("99arcade", "99 Arcade")

    def tearDown(self) -> None:
        self.db.close()
        self.tmp.cleanup()

    def test_stores_no_device(self):
        self.db.add_code("FREE99", "99arcade")
        self.assertEqual(self.db.redeem("99arcade", "FREE99"), (True, "ok"))
        self.assertIsNone(self.db.redemptions()[0]["device_id"])

    def test_each_redemption_spends_a_use(self):
        self.db.add_code("FREE99", "99arcade", max_uses=2)
        self.db.redeem("99arcade", "FREE99")
        self.db.redeem("99arcade", "FREE99")
        self.assertEqual(self.db.redeem("99arcade", "FREE99"), (False, "exhausted"))

    def test_limits_still_apply(self):
        self.db.add_code("OFFX", "99arcade")
        self.db.set_enabled("OFFX", False)
        self.assertEqual(self.db.redeem("99arcade", "OFFX"), (False, "disabled"))

    def test_devices_total_ignores_anonymous(self):
        self.db.add_code("FREE99", "99arcade")
        self.db.redeem("99arcade", "FREE99")
        self.db.redeem("99arcade", "FREE99", "device-a")
        self.assertEqual(self.db.totals()["devices"], 1)
