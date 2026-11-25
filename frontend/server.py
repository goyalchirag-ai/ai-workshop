"""Local frontend server with a same-origin proxy to the existing Flask API."""
import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
STATIC_FILES = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}


class Handler(SimpleHTTPRequestHandler):
    backend = "http://127.0.0.1:5000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy()
        elif self.path.split("?", 1)[0] in STATIC_FILES:
            self.path = "/" + STATIC_FILES[self.path.split("?", 1)[0]]
            super().do_GET()
        else:
            self.send_error(404)

    def do_HEAD(self):
        if self.path.split("?", 1)[0] not in STATIC_FILES:
            self.send_error(404)
            return
        self.path = "/" + STATIC_FILES[self.path.split("?", 1)[0]]
        super().do_HEAD()

    def do_POST(self):
        if self.path == "/api/registrations":
            self.proxy()
        else:
            self.send_error(404)

    def proxy(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 16384:
                self.send_error(413)
                return
            payload = self.rfile.read(length) if self.command == "POST" else None
            request = Request(self.backend + self.path, data=payload, method=self.command,
                              headers={"Content-Type": "application/json", "Accept": "application/json"})
            try:
                with urlopen(request, timeout=30) as response:
                    status, body = response.status, response.read()
            except HTTPError as error:
                with error:
                    status, body = error.code, error.read()
        except (URLError, TimeoutError, OSError):
            status, body = 502, json.dumps({"error": "Cannot reach the events backend. Start Flask or check the configured backend URL."}).encode()
        except ValueError:
            status, body = 400, b'{"error":"Invalid request length"}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--backend", default="http://127.0.0.1:5000")
    args = parser.parse_args()
    if not args.backend.startswith(("http://", "https://")):
        parser.error("--backend must be an HTTP or HTTPS URL")
    Handler.backend = args.backend.rstrip("/")
    print(f"Gather frontend: http://127.0.0.1:{args.port}", flush=True)
    print(f"API proxy: {Handler.backend}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
