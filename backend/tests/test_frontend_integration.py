import unittest
import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from app import create_app


class FrontendIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def test_home_serves_gather_html(self):
        with self.client.get("/") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "text/html")
            self.assertIn(b'GATHER', response.data)

    def test_vercel_entrypoint_exports_complete_app(self):
        entry = Path(__file__).resolve().parents[2] / "server.py"
        deployed = runpy.run_path(str(entry))["app"]
        with deployed.test_client().get("/") as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "text/html")
        self.assertEqual(deployed.test_client().get("/health").status_code, 200)

    def test_frontend_assets_are_available_on_same_origin(self):
        for path in ("/app.js", "/styles.css"):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
        with self.client.get("/app.js") as response:
            self.assertIn(b'fetch(`/api${path}`', response.data)

    def test_api_metadata_remains_at_api(self):
        response = self.client.get("/api")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["endpoints"]), 5)

    def test_same_app_serves_backend_event_data(self):
        database = MagicMock()
        database.table.return_value.select.return_value.execute.return_value = SimpleNamespace(data=[{"id":"event", "title":"Connected event"}])
        self.app.extensions["supabase"] = database
        self.assertEqual(self.client.get("/api/events").json["data"][0]["title"], "Connected event")

    def test_private_and_source_files_are_not_public(self):
        for path in ("/.env", "/backend/.env", "/server.py", "/frontend/server.py", "/backend/app/config.py"):
            self.assertEqual(self.client.get(path).status_code, 404)
