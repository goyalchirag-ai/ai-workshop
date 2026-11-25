from pathlib import Path

from flask import Flask, jsonify, send_from_directory

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

    frontend = Path(__file__).resolve().parents[2] / "frontend"

    @app.get("/")
    def frontend_index():
        if (frontend / "index.html").is_file():
            return send_from_directory(frontend, "index.html")
        return api_index()

    # Local Flask serves these files; Vercel serves the built public/ copies.
    @app.get("/app.js")
    def frontend_script():
        return send_from_directory(frontend, "app.js")

    @app.get("/styles.css")
    def frontend_styles():
        return send_from_directory(frontend, "styles.css")

    return app
