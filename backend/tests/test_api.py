import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from postgrest.exceptions import APIError

from app import create_app
from app.supabase_client import get_supabase


USER_ID = "11111111-1111-4111-8111-111111111111"
ORGANIZER_ID = "22222222-2222-4222-8222-222222222222"
EVENT_ID = "33333333-3333-4333-8333-333333333333"


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()
        self.supabase = MagicMock()
        self.app.extensions["supabase"] = self.supabase

    def query(self, *responses):
        builder = MagicMock()
        builder.select.return_value = builder
        builder.eq.return_value = builder
        builder.limit.return_value = builder
        builder.insert.return_value = builder
        builder.execute.side_effect = responses
        self.supabase.table.return_value = builder
        return builder

    def response(self, data, count=None):
        return SimpleNamespace(data=data, count=count)

    def test_list_events(self):
        self.query(self.response([{"id": EVENT_ID, "title": "Workshop"}]))
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"][0]["id"], EVENT_ID)

    def test_event_not_found(self):
        self.query(self.response([]))
        response = self.client.get(f"/api/events/{EVENT_ID}")
        self.assertEqual(response.status_code, 404)

    def test_get_event(self):
        self.query(self.response([{"id": EVENT_ID, "title": "Workshop"}]))
        response = self.client.get(f"/api/events/{EVENT_ID}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["id"], EVENT_ID)

    def test_create_registration(self):
        builder = self.query(
            self.response([{"id": USER_ID}]),
            self.response([{"id": EVENT_ID, "capacity": 10}]),
            self.response([]),
            self.response([], count=2),
            self.response([]),
        )
        response = self.client.post(
            "/api/registrations",
            json={"user_id": USER_ID, "event_id": EVENT_ID},
        )
        self.assertEqual(response.status_code, 201)
        builder.select.assert_any_call("id", count="exact", head=True)
        builder.insert.assert_called_once()

    def test_registration_at_capacity_returns_conflict(self):
        builder = self.query(
            self.response([{"id": USER_ID}]),
            self.response([{"id": EVENT_ID, "capacity": 2}]),
            self.response([]),
            self.response([], count=2),
        )
        response = self.client.post(
            "/api/registrations",
            json={"user_id": USER_ID, "event_id": EVENT_ID},
        )
        self.assertEqual(response.status_code, 409)
        builder.insert.assert_not_called()

    def test_duplicate_registration_returns_conflict(self):
        self.query(
            self.response([{"id": USER_ID}]),
            self.response([{"id": EVENT_ID, "capacity": 10}]),
            self.response([{"id": "44444444-4444-4444-8444-444444444444"}]),
        )
        response = self.client.post(
            "/api/registrations",
            json={"user_id": USER_ID, "event_id": EVENT_ID},
        )
        self.assertEqual(response.status_code, 409)

    def test_list_user_registrations_requires_user_id(self):
        response = self.client.get("/api/me/registrations")
        self.assertEqual(response.status_code, 400)

    def test_list_user_registrations(self):
        self.query(
            self.response(
                [{"id": "55555555-5555-4555-8555-555555555555", "user_id": USER_ID}]
            )
        )
        response = self.client.get(f"/api/me/registrations?user_id={USER_ID}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"][0]["user_id"], USER_ID)

    def test_list_event_registrations_without_authentication(self):
        builder = self.query(
            self.response([{"id": EVENT_ID, "organizer_id": ORGANIZER_ID}]),
            self.response([{"id": "55555555-5555-4555-8555-555555555555"}]),
        )
        response = self.client.get(
            f"/api/events/{EVENT_ID}/registrations"
        )
        self.assertEqual(response.status_code, 200)
        builder.eq.assert_any_call("event_id", EVENT_ID)
        builder.select.assert_any_call(
            "id,user_id,event_id,created_at,users(id,email,role)"
        )

    def test_empty_event_attendees(self):
        self.query(
            self.response([{"id": EVENT_ID}]), self.response([])
        )
        response = self.client.get(f"/api/events/{EVENT_ID}/registrations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"data": []})

    def test_attendees_event_not_found(self):
        self.query(self.response([]))
        response = self.client.get(f"/api/events/{EVENT_ID}/registrations")
        self.assertEqual(response.status_code, 404)

    def test_invalid_event_ids_do_not_query_database(self):
        for path in ("/api/events/not-a-uuid", "/api/events/not-a-uuid/registrations"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 400)
        self.supabase.table.assert_not_called()

    def test_invalid_registration_bodies_do_not_query_database(self):
        for payload in (
            {}, [], None,
            {"user_id": "invalid", "event_id": EVENT_ID},
            {"user_id": USER_ID, "event_id": "invalid"},
            {"user_id": USER_ID, "event_id": EVENT_ID, "role": "admin"},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/registrations", json=payload,
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)
        self.supabase.table.assert_not_called()

    def test_registration_requires_json_content_type(self):
        response = self.client.post("/api/registrations", data="not JSON")
        self.assertEqual(response.status_code, 415)
        self.supabase.table.assert_not_called()

    def test_registration_rejects_malformed_json(self):
        response = self.client.post(
            "/api/registrations", data="{", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.supabase.table.assert_not_called()

    def test_registration_user_not_found(self):
        builder = self.query(self.response([]))
        response = self.client.post(
            "/api/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID}
        )
        self.assertEqual(response.status_code, 404)
        builder.insert.assert_not_called()

    def test_registration_event_not_found(self):
        builder = self.query(self.response([{"id": USER_ID}]), self.response([]))
        response = self.client.post(
            "/api/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID}
        )
        self.assertEqual(response.status_code, 404)
        builder.insert.assert_not_called()

    def test_registration_with_unlimited_capacity(self):
        builder = self.query(
            self.response([{"id": USER_ID}]),
            self.response([{"id": EVENT_ID, "capacity": None}]),
            self.response([]),
            self.response([]),
        )
        response = self.client.post(
            "/api/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["data"]["user_id"], USER_ID)
        self.assertEqual(response.get_json()["data"]["event_id"], EVENT_ID)
        builder.insert.assert_called_once()

    def test_database_duplicate_returns_conflict(self):
        self.query(
            self.response([{"id": USER_ID}]),
            self.response([{"id": EVENT_ID, "capacity": None}]),
            self.response([]),
            APIError({"code": "23505", "message": "duplicate key",
                      "details": None, "hint": None}),
        )
        response = self.client.post(
            "/api/registrations", json={"user_id": USER_ID, "event_id": EVENT_ID}
        )
        self.assertEqual(response.status_code, 409)

    def test_user_registrations_are_filtered_by_user(self):
        builder = self.query(self.response([]))
        response = self.client.get(
            f"/api/me/registrations?user_id={USER_ID}"
        )
        self.assertEqual(response.status_code, 200)
        builder.eq.assert_called_once_with("user_id", USER_ID)

    def test_database_errors_do_not_expose_details(self):
        self.query(APIError({"code": "42501", "message": "private database detail",
                             "details": None, "hint": None}))
        with self.assertLogs(self.app.logger, level="ERROR"):
            response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json(), {"error": "Database operation failed"})

    def test_missing_database_configuration(self):
        del self.app.extensions["supabase"]
        self.app.config.update(
            SUPABASE_URL="", SUPABASE_SECRET_KEY="", SUPABASE_SERVICE_ROLE_KEY=""
        )
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 503)
        self.assertIn("SUPABASE_URL", response.get_json()["details"]["missing"])

    def test_server_key_configuration_and_client_reuse(self):
        for secret, legacy, expected in (
            ("test-secret", "test-legacy", "test-secret"),
            ("", "test-legacy", "test-legacy"),
        ):
            with self.subTest(secret=bool(secret)):
                self.app.extensions.pop("supabase", None)
                self.app.config.update(
                    SUPABASE_URL="https://example.supabase.co",
                    SUPABASE_SECRET_KEY=secret,
                    SUPABASE_SERVICE_ROLE_KEY=legacy,
                )
                with patch("app.supabase_client.create_client") as factory:
                    with self.app.app_context():
                        self.assertIs(get_supabase(), factory.return_value)
                        self.assertIs(get_supabase(), factory.return_value)
                    factory.assert_called_once_with(
                        "https://example.supabase.co", expected
                    )

    def test_publishable_key_does_not_replace_server_key(self):
        self.app.extensions.pop("supabase", None)
        self.app.config.update(
            SUPABASE_URL="https://example.supabase.co",
            SUPABASE_SECRET_KEY="", SUPABASE_SERVICE_ROLE_KEY="",
            SUPABASE_PUBLISHABLE_KEY="test-publishable",
        )
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["details"]["missing"],
                         ["SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY)"])

    def test_health_does_not_require_database(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        self.supabase.table.assert_not_called()


if __name__ == "__main__":
    unittest.main()
