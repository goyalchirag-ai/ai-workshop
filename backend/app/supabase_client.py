from flask import current_app
from supabase import Client, create_client

from app.errors import ApiError


def get_supabase() -> Client:
    client = current_app.extensions.get("supabase")
    if client is not None:
        return client

    url = current_app.config.get("SUPABASE_URL")
    server_key = current_app.config.get("SUPABASE_SECRET_KEY") or current_app.config.get(
        "SUPABASE_SERVICE_ROLE_KEY"
    )

    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not server_key:
        missing.append("SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY)")
    if missing:
        raise ApiError(
            "Server database configuration is missing",
            status_code=503,
            details={"missing": missing},
        )

    client = create_client(url, server_key)
    current_app.extensions["supabase"] = client
    return client
