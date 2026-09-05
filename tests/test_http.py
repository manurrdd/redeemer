from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
import zipfile
from http.client import HTTPConnection
from pathlib import Path

from redeemer.server import Config, Server


class HttpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        config = Config()
        config.db_path = str(Path(self.tmp.name) / "test.db")
        config.backup_dir = str(Path(self.tmp.name) / "backups")
        config.host, config.port = "127.0.0.1", 0
        config.password = "secreto"
        self.server = Server(config)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.server.db.add_app("99arcade", "99 Arcade")
        self.free_id = self.server.db.add_code("FREE99", "99arcade", max_uses=1)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def request(self, method: str, path: str, body=None, headers=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        payload = body.encode() if isinstance(body, str) else (json.dumps(body).encode() if body is not None else None)
        conn.request(method, path, payload, headers or {"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response, data

    def redeem(self, **payload):
        response, data = self.request("POST", "/v1/redeem", payload)
        return response.status, json.loads(data)

    def test_redeem_endpoint(self):
        status, body = self.redeem(app="99arcade", code="free99", device_id="device-a")
        self.assertEqual((status, body), (200, {"granted": True, "reason": "ok"}))
        status, body = self.redeem(app="99arcade", code="FREE99", device_id="device-b")
        self.assertEqual(body, {"granted": False, "reason": "exhausted"})

    def test_bad_request(self):
        status, body = self.redeem(app="99arcade", code="FREE99")
        self.assertEqual((status, body["reason"]), (400, "bad_request"))

    def test_rate_limit(self):
        for _ in range(30):
            self.redeem(app="99arcade", code="X", device_id="device-a")
        status, body = self.redeem(app="99arcade", code="X", device_id="device-a")
        self.assertEqual((status, body["reason"]), (429, "rate_limited"))

    def login(self) -> str:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/login", "password=secreto",
                     {"Content-Type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        response.read()
        cookie = response.getheader("Set-Cookie").split(";")[0]
        conn.close()
        return cookie

    def test_panel_requires_login(self):
        response, _ = self.request("GET", "/", headers={})
        self.assertEqual((response.status, response.getheader("Location")), (303, "/login"))

    def test_login_and_dashboard(self):
        cookie = self.login()
        response, data = self.request("GET", "/", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)
        self.assertIn(b"99 Arcade", data)

    def test_wrong_password(self):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/login", "password=nope",
                     {"Content-Type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        response.read()
        conn.close()
        self.assertEqual(response.status, 401)

    def test_client_metadata_is_sanitized(self):
        self.redeem(app="99arcade", code="FREE99", device_id="d1",
                    platform="  iOS  ", app_version="1.4.2", country="es")
        row = self.server.db.redemptions()[0]
        self.assertEqual((row["platform"], row["country"]), ("ios", "es".upper()))

    def test_junk_metadata_is_dropped(self):
        self.redeem(app="99arcade", code="FREE99", device_id="d1",
                    platform="a" * 40, country="Spain", app_version={"x": 1})
        row = self.server.db.redemptions()[0]
        self.assertEqual((row["platform"], row["country"], row["app_version"]), (None, None, None))

    def test_proxy_country_header_is_ignored_without_a_proxy(self):
        self.send_country_header()
        self.assertEqual(self.server.db.redemptions()[0]["country"], "FR")

    def test_proxy_country_header_wins_behind_a_proxy(self):
        self.server.config.behind_proxy = True
        self.send_country_header()
        self.assertEqual(self.server.db.redemptions()[0]["country"], "DE")

    def send_country_header(self):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/v1/redeem",
                     json.dumps({"app": "99arcade", "code": "FREE99",
                                 "device_id": "d1", "country": "FR"}),
                     {"Content-Type": "application/json", "CF-IPCountry": "DE"})
        conn.getresponse().read()
        conn.close()

    def test_csv_export(self):
        response, data = self.request("GET", "/a/99arcade/codes.csv",
                                      headers={"Cookie": self.login()})
        self.assertEqual(response.status, 200)
        self.assertIn(b"FREE99", data)

    def test_toggle_and_delete_code(self):
        cookie = self.login()
        headers = {"Cookie": cookie, "Content-Type": "application/x-www-form-urlencoded"}
        self.request("POST", f"/c/{self.free_id}/toggle", None, headers)
        self.assertEqual(self.server.db.code(self.free_id)["enabled"], 0)
        self.request("POST", f"/c/{self.free_id}/delete", None, headers)
        self.assertIsNone(self.server.db.code(self.free_id))

    def test_toggle_ignores_external_referer(self):
        headers = {"Cookie": self.login(), "Referer": "https://evil.example/x",
                   "Content-Type": "application/x-www-form-urlencoded"}
        response, _ = self.request("POST", f"/c/{self.free_id}/toggle", None, headers)
        self.assertEqual(response.getheader("Location"), "/x")

    def test_nonce_grants_once_and_replays(self):
        self.anon_id = self.server.db.add_code("ANON", "99arcade", max_uses=1)
        first = self.redeem(app="99arcade", code="ANON", nonce="attempt-1")
        retry = self.redeem(app="99arcade", code="ANON", nonce="attempt-1")
        self.assertEqual(first[1], {"granted": True, "reason": "ok"})
        self.assertEqual(retry[1], {"granted": True, "reason": "already"})
        self.assertEqual(self.server.db.code(self.anon_id)["uses"], 1)

    def test_nonce_replays_failures_too(self):
        first = self.redeem(app="99arcade", code="NOPE", nonce="attempt-2")
        retry = self.redeem(app="99arcade", code="NOPE", nonce="attempt-2")
        self.assertEqual(first[1], retry[1])
        self.assertFalse(retry[1]["granted"])

    def test_new_nonce_spends_another_use(self):
        self.anon_id = self.server.db.add_code("ANON", "99arcade", max_uses=1)
        self.redeem(app="99arcade", code="ANON", nonce="attempt-1")
        status, body = self.redeem(app="99arcade", code="ANON", nonce="attempt-2")
        self.assertEqual(body["reason"], "exhausted")

    def test_device_and_nonce_are_exclusive(self):
        both = self.redeem(app="99arcade", code="FREE99", device_id="d1", nonce="n1")
        neither = self.redeem(app="99arcade", code="FREE99")
        self.assertEqual(both[0], 400)
        self.assertEqual(neither[0], 400)

    def test_garbage_numbers_do_not_crash_the_panel(self):
        headers = {"Cookie": self.login(), "Content-Type": "application/x-www-form-urlencoded"}
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/a/99arcade/codes", "quantity=abc&max_uses=-4&code=SAFE1", headers)
        response = conn.getresponse()
        response.read()
        conn.close()
        self.assertEqual(response.status, 303)
        self.assertIsNone(next(c for c in self.server.db.codes("99arcade") if c["code"] == "SAFE1")["max_uses"])

    def test_unknown_app_and_code_are_404(self):
        headers = {"Cookie": self.login(), "Content-Type": "application/x-www-form-urlencoded"}
        missing_app, _ = self.request("POST", "/a/nope/codes", None, headers)
        missing_code, _ = self.request("POST", "/c/NOPE1234", None, headers)
        csv, _ = self.request("GET", "/a/nope/codes.csv", headers={"Cookie": headers["Cookie"]})
        self.assertEqual([missing_app.status, missing_code.status, csv.status], [404, 404, 404])

    def test_form_keeps_values_when_it_fails(self):
        headers = {"Cookie": self.login(), "Content-Type": "application/x-www-form-urlencoded"}
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/apps", "slug=Bad+Slug&name=Keep+Me", headers)
        response = conn.getresponse()
        body = response.read()
        conn.close()
        self.assertEqual(response.status, 400)
        self.assertIn(b"Keep Me", body)
        self.assertIn(b"Bad Slug", body)

    def test_platform_scoped_code_over_http(self):
        self.server.db.add_code("IOSONLY", "99arcade", platforms="ios")
        ok = self.redeem(app="99arcade", code="IOSONLY", device_id="d1", platform="ios")
        no = self.redeem(app="99arcade", code="IOSONLY", device_id="d2", platform="android")
        self.assertTrue(ok[1]["granted"])
        self.assertEqual(no[1]["reason"], "wrong_platform")

    def test_creating_codes_points_at_the_new_batch(self):
        headers = {"Cookie": self.login(), "Content-Type": "application/x-www-form-urlencoded"}
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/a/99arcade/codes", "quantity=3", headers)
        response = conn.getresponse()
        response.read()
        conn.close()
        location = response.getheader("Location")
        self.assertIn("?batch=", location)
        page, body = self.request("GET", location, headers={"Cookie": headers["Cookie"]})
        self.assertIn(b"3 codes just created", body)
        self.assertIn(b'class="fresh"', body)
        batch = location.split("?batch=")[1]
        csv, data = self.request("GET", f"/a/99arcade/codes.csv?batch={batch}",
                                 headers={"Cookie": headers["Cookie"]})
        self.assertEqual(len(data.decode().strip().splitlines()), 4)

    def upload(self, cookie: str, payload: bytes):
        boundary = "----test"
        body = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            'filename="backup.db.gz"\r\nContent-Type: application/octet-stream\r\n\r\n'
        ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/restore", body,
                     {"Cookie": cookie, "Content-Type":
                      f"multipart/form-data; boundary={boundary}"})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response, data

    def test_backup_round_trip(self):
        cookie = self.login()
        response, blob = self.request("GET", "/backup.db.gz", headers={"Cookie": cookie})
        self.assertEqual((response.status, blob[:2]), (200, b"\x1f\x8b"))
        self.server.db.delete_app("99arcade")
        restored, _ = self.upload(cookie, blob)
        self.assertEqual(restored.status, 303)
        self.assertIsNotNone(self.server.db.app("99arcade"))
        self.assertIsNotNone(self.server.db.code(self.free_id))

    def test_restore_keeps_the_session(self):
        cookie = self.login()
        _, blob = self.request("GET", "/backup.db.gz", headers={"Cookie": cookie})
        self.upload(cookie, blob)
        response, _ = self.request("GET", "/data", headers={"Cookie": cookie})
        self.assertEqual(response.status, 200)

    def test_restore_rejects_anything_else(self):
        cookie = self.login()
        response, body = self.upload(cookie, b"not a database")
        self.assertEqual(response.status, 400)
        self.assertIn(b"Not a Redeemer backup.", body)
        self.assertIsNotNone(self.server.db.app("99arcade"))

    def test_selected_and_global_scopes_with_both_quotas(self):
        self.server.db.add_app("second", "Second")
        self.server.db.add_app("outside", "Outside")
        headers = {"Cookie": self.login(), "Content-Type": "application/x-www-form-urlencoded"}
        for scope in ("selected", "global"):
            for mode in ("shared", "per_app"):
                text = f"{scope}-{mode}".replace("_", "-").upper()
                payload = f"code={text}&scope={scope}&app:99arcade=1&app:second=1&quota_mode={mode}&max_uses=1"
                response, _ = self.request("POST", "/a/99arcade/codes", payload, headers)
                self.assertEqual(response.status, 303)
                self.assertTrue(self.redeem(app="99arcade", code=text, device_id="d1")[1]["granted"])
                second = self.redeem(app="second", code=text, device_id="d1")[1]
                self.assertEqual(second["granted"], mode == "per_app")
                if scope == "selected":
                    self.assertEqual(self.redeem(app="outside", code=text, device_id="d1")[1]["reason"], "wrong_app")
                row = next(c for c in self.server.db.codes("99arcade") if c["code"] == text)
                page, body = self.request("GET", f"/c/{row['id']}", headers=headers)
                self.assertEqual(page.status, 200)
                self.assertIn(b"Uses by app", body)
                self.assertIn(b"Quota", body)
                self.assertIn(b"/app" if mode == "per_app" else b"shared", body)
        _, csv = self.request("GET", "/a/99arcade/codes.csv", headers=headers)
        self.assertIn(b"quota_mode,apps", csv)
        self.assertIn(b"per_app", csv)

    def test_duplicate_text_panel_actions_are_independent(self):
        self.server.db.add_app("second", "Second")
        other_id = self.server.db.add_code("FREE99", "second")
        headers = {"Cookie": self.login(), "Content-Type": "application/x-www-form-urlencoded"}
        response, _ = self.request("POST", f"/c/{self.free_id}",
                                   "note=Changed&quota_mode=per_app&max_uses=2&enabled=1", headers)
        self.assertEqual(response.status, 303)
        self.assertEqual(self.server.db.code(self.free_id)["quota_mode"], "per_app")
        self.assertEqual(self.server.db.code(other_id)["quota_mode"], "shared")
        response, body = self.request("GET", "/a/second", headers=headers)
        self.assertEqual(response.status, 200)
        self.assertIn(f'/c/{other_id}'.encode(), body)
        self.assertNotIn(f'/c/{self.free_id}/toggle'.encode(), body)
        self.request("POST", f"/c/{self.free_id}/delete", None, headers)
        self.assertIsNotNone(self.server.db.code(other_id))
        self.assertTrue(self.redeem(app="second", code="FREE99", device_id="d1")[1]["granted"])

    def test_invalid_selection_preserves_form_and_creates_nothing(self):
        headers = {"Cookie": self.login(), "Content-Type": "application/x-www-form-urlencoded"}
        response, body = self.request("POST", "/global/codes",
                                       "code=CHOSEN&scope=selected&quota_mode=per_app", headers)
        self.assertEqual(response.status, 400)
        self.assertIn(b"Select at least one app", body)
        self.assertIn(b'value="CHOSEN"', body)
        self.assertIn(b'value="per_app" selected', body)
        self.assertEqual(self.server.db.totals()["codes"], 1)
        response, body = self.request("POST", "/global/codes",
                                       "code=FREE99&scope=global&quota_mode=shared", headers)
        self.assertEqual(response.status, 400)
        self.assertIn(b"already applies", body)

    def test_healthz(self):
        response, data = self.request("GET", "/healthz")
        self.assertEqual((response.status, json.loads(data)), (200, {"ok": True}))

    def export(self, query: str, cookie: str):
        return self.request("GET", f"/data/export?{query}", headers={"Cookie": cookie})

    def test_export_formats(self):
        cookie = self.login()
        self.redeem(app="99arcade", code="FREE99", device_id="d1")
        response, csv = self.export("include=codes", cookie)
        self.assertEqual(response.status, 200)
        self.assertIn(".csv", response.getheader("Content-Disposition"))
        self.assertIn(b"FREE99", csv)
        response, blob = self.export("include=codes&include=redemptions&devices=1", cookie)
        archive = zipfile.ZipFile(io.BytesIO(blob))
        self.assertEqual(archive.namelist(), ["codes.csv", "redemptions.csv"])
        self.assertIn(b"d1", archive.read("redemptions.csv"))
        _, blob = self.export("include=codes&include=redemptions", cookie)
        self.assertNotIn(b"d1", zipfile.ZipFile(io.BytesIO(blob)).read("redemptions.csv"))
        _, body = self.export("format=json&include=codes&include=apps", cookie)
        data = json.loads(body)
        self.assertEqual([c["code"] for c in data["codes"]], ["FREE99"])
        self.assertEqual(data["apps"][0]["slug"], "99arcade")
        _, body = self.export("format=txt", cookie)
        self.assertEqual(body, b"FREE99")

    def test_export_scope_and_filters(self):
        cookie = self.login()
        self.server.db.add_app("second", "Second")
        self.server.db.add_code("SECOND1", "second")
        self.redeem(app="99arcade", code="FREE99", device_id="d1")
        _, body = self.export("scope=selected&app=second&include=codes", cookie)
        self.assertIn(b"SECOND1", body)
        self.assertNotIn(b"FREE99", body)
        _, body = self.export("include=codes&status=unused", cookie)
        self.assertIn(b"SECOND1", body)
        self.assertNotIn(b"FREE99", body)
        _, body = self.export("include=redemptions&from=2000-01-01&to=2000-01-02", cookie)
        self.assertEqual(len(body.decode().strip().splitlines()), 1)

    def test_export_rejects_bad_options(self):
        cookie = self.login()
        for query in ("include=", "scope=selected&include=codes", "format=xml&include=codes",
                      "scope=nowhere&include=codes", "include=codes&status=nope"):
            response, _ = self.export(query, cookie)
            self.assertEqual(response.status, 400, query)


if __name__ == "__main__":
    unittest.main()
