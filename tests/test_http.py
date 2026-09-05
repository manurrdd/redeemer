from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from redeemer.server import Config, Server


class HttpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        config = Config()
        config.db_path = str(Path(self.tmp.name) / "test.db")
        config.host, config.port = "127.0.0.1", 0
        config.password = "secreto"
        self.server = Server(config)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.server.db.add_app("99arcade", "99 Arcade")
        self.server.db.add_code("FREE99", "99arcade", max_uses=1)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def request(self, method: str, path: str, body=None, headers=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        payload = json.dumps(body).encode() if body is not None else None
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
        self.request("POST", "/c/FREE99/toggle", None, headers)
        self.assertEqual(self.server.db.code("FREE99")["enabled"], 0)
        self.request("POST", "/c/FREE99/delete", None, headers)
        self.assertIsNone(self.server.db.code("FREE99"))

    def test_toggle_ignores_external_referer(self):
        headers = {"Cookie": self.login(), "Referer": "https://evil.example/x",
                   "Content-Type": "application/x-www-form-urlencoded"}
        response, _ = self.request("POST", "/c/FREE99/toggle", None, headers)
        self.assertEqual(response.getheader("Location"), "/x")

    def test_nonce_grants_once_and_replays(self):
        self.server.db.add_code("ANON", "99arcade", max_uses=1)
        first = self.redeem(app="99arcade", code="ANON", nonce="attempt-1")
        retry = self.redeem(app="99arcade", code="ANON", nonce="attempt-1")
        self.assertEqual(first[1], {"granted": True, "reason": "ok"})
        self.assertEqual(retry[1], {"granted": True, "reason": "already"})
        self.assertEqual(self.server.db.code("ANON")["uses"], 1)

    def test_nonce_replays_failures_too(self):
        first = self.redeem(app="99arcade", code="NOPE", nonce="attempt-2")
        retry = self.redeem(app="99arcade", code="NOPE", nonce="attempt-2")
        self.assertEqual(first[1], retry[1])
        self.assertFalse(retry[1]["granted"])

    def test_new_nonce_spends_another_use(self):
        self.server.db.add_code("ANON", "99arcade", max_uses=1)
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
        self.assertIsNone(self.server.db.code("SAFE1")["max_uses"])

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

    def test_healthz(self):
        response, data = self.request("GET", "/healthz")
        self.assertEqual((response.status, json.loads(data)), (200, {"ok": True}))


if __name__ == "__main__":
    unittest.main()
