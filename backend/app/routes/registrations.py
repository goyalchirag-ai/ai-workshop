from datetime import datetime, timezone
from uuid import uuid4

from flask import Blueprint, jsonify
from postgrest.exceptions import APIError

from app.errors import ApiError
from app.supabase_client import get_supabase
from app.validation import require_json_object, require_query_uuid, validate_uuid


registrations_blueprint = Blueprint("registrations", __name__, url_prefix="/api")


@registrations_blueprint.post("/registrations")
def create_registration():
    payload = require_json_object()
    allowed_fields = {"user_id", "event_id"}
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        raise ApiError("Unknown fields in request body", details=unknown_fields)

    user_id = validate_uuid(payload.get("user_id"), "user_id")
    event_id = validate_uuid(payload.get("event_id"), "event_id")
    client = get_supabase()

    user_response = (
        client.table("users").select("id").eq("id", user_id).limit(1).execute()
    )
    if not user_response.data:
        raise ApiError("User not found", status_code=404)

    event_response = (
        client.table("events")
        .select("id,capacity")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not event_response.data:
        raise ApiError("Event not found", status_code=404)

    duplicate_response = (
        client.table("registrations")
        .select("id")
        .eq("user_id", user_id)
        .eq("event_id", event_id)
        .limit(1)
        .execute()
    )
    if duplicate_response.data:
        raise ApiError("User is already registered for this event", status_code=409)

    capacity = event_response.data[0].get("capacity")
    if capacity is not None:
        count_response = (
            client.table("registrations")
            .select("id", count="exact", head=True)
            .eq("event_id", event_id)
            .execute()
        )
        if count_response.count is not None and count_response.count >= capacity:
            raise ApiError("Event capacity has been reached", status_code=409)

    registration = {
        "id": str(uuid4()),
        "user_id": user_id,
        "event_id": event_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = client.table("registrations").insert(registration).execute()
    except APIError as error:
        if getattr(error, "code", None) == "23505":
            raise ApiError(
                "User is already registered for this event", status_code=409
            ) from error
        raise

    created = response.data[0] if response.data else registration
    return jsonify({"data": created}), 201


@registrations_blueprint.get("/me/registrations")
def list_user_registrations():
    user_id = require_query_uuid("user_id")
    response = (
        get_supabase()
        .table("registrations")
        .select(
            "id,user_id,event_id,created_at,"
            "events(id,organizer_id,title,capacity,status)"
        )
        .eq("user_id", user_id)
        .execute()
    )
    return jsonify({"data": response.data})
