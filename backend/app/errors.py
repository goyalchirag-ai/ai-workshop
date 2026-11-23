from flask import jsonify
from postgrest.exceptions import APIError


class ApiError(Exception):
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        payload = {"error": error.message}
        if error.details is not None:
            payload["details"] = error.details
        return jsonify(payload), error.status_code

    @app.errorhandler(APIError)
    def handle_supabase_error(error):
        app.logger.exception("Supabase request failed")
        return jsonify({"error": "Database operation failed"}), 502

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled application error", exc_info=error)
        return jsonify({"error": "Internal server error"}), 500
