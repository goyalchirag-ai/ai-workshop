from flask import Flask, jsonify

from app.config import Config
from app.errors import register_error_handlers
from app.routes.events import events_blueprint
from app.routes.registrations import registrations_blueprint


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    app.register_blueprint(events_blueprint)
    app.register_blueprint(registrations_blueprint)
    register_error_handlers(app)

    @app.get("/")
    @app.get("/api", strict_slashes=False)
    def api_index():
        return jsonify({
            "name": "Events API",
            "authentication_required": False,
            "health": "/health",
            "endpoints": [
                {"method": "GET", "path": "/api/events"},
                {"method": "GET", "path": "/api/events/{id}"},
                {
                    "method": "POST",
                    "path": "/api/registrations",
                    "json_body": {"user_id": "USER_UUID", "event_id": "EVENT_UUID"},
                },
                {"method": "GET", "path": "/api/me/registrations?user_id=USER_UUID"},
                {"method": "GET", "path": "/api/events/{id}/registrations"},
            ],
        })

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok"})

    return app
