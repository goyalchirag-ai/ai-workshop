import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location("frontend_server", Path(__file__).resolve().parents[1] / "server.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeBackend(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.respond(200, {"data": {"requested_path": self.path}})

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if payload.get("event_id") == "full":
            self.respond(409, {"error": "Event capacity has been reached"})
        else:
            self.respond(201, {"data": payload})

    def respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


class ProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = ThreadingHTTPServer(("127.0.0.1", 0), FakeBackend)
        class QuietHandler(module.Handler):
            def log_message(self, *args):
                pass
        QuietHandler.backend = f"http://127.0.0.1:{cls.backend.server_port}"
        cls.frontend = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.base = f"http://127.0.0.1:{cls.frontend.server_port}"
        cls.threads = []
        for server in (cls.backend, cls.frontend):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            cls.threads.append(thread)

    @classmethod
    def tearDownClass(cls):
        for server in (cls.frontend, cls.backend):
            server.shutdown()
            server.server_close()
        for thread in cls.threads:
            thread.join()

    def request(self, path, payload=None):
        request = Request(self.base + path, data=json.dumps(payload).encode() if payload is not None else None,
                          headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.read(), response.headers

    def test_serves_frontend_and_assets(self):
        for path, expected in (("/", b"Gather"), ("/styles.css", b"@media"), ("/app.js", b"/registrations")):
            status, body, _ = self.request(path)
            self.assertEqual(status, 200)
            self.assertIn(expected, body)

    def test_forwards_query_without_losing_user_id(self):
        status, body, headers = self.request("/api/me/registrations?user_id=test-user")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["data"]["requested_path"], "/api/me/registrations?user_id=test-user")
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_preserves_registration_body_and_created_status(self):
        payload = {"user_id": "user", "event_id": "event"}
        status, body, _ = self.request("/api/registrations", payload)
        self.assertEqual(status, 201)
        self.assertEqual(json.loads(body)["data"], payload)

    def test_preserves_conflict_message(self):
        status, body, _ = self.request("/api/registrations", {"event_id": "full"})
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["error"], "Event capacity has been reached")

    def test_does_not_serve_source_designs_or_parent_files(self):
        for path in ("/server.py", "/design/", "/../Backend/.env", "/tests/test_proxy.py"):
            self.assertEqual(self.request(path)[0], 404)


if __name__ == "__main__":
    unittest.main()
