from flask import Blueprint, jsonify

from app.errors import ApiError
from app.supabase_client import get_supabase
from app.validation import validate_uuid


events_blueprint = Blueprint("events", __name__, url_prefix="/api/events")
EVENT_COLUMNS = "id,organizer_id,title,capacity,status"


@events_blueprint.get("")
def list_events():
    response = get_supabase().table("events").select(EVENT_COLUMNS).execute()
    return jsonify({"data": response.data})


@events_blueprint.get("/<event_id>")
def get_event(event_id):
    event_id = validate_uuid(event_id, "id")
    response = (
        get_supabase()
        .table("events")
        .select(EVENT_COLUMNS)
        .eq("id", event_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ApiError("Event not found", status_code=404)
    return jsonify({"data": response.data[0]})


@events_blueprint.get("/<event_id>/registrations")
def list_event_registrations(event_id):
    event_id = validate_uuid(event_id, "id")
    client = get_supabase()

    event_response = (
        client.table("events")
        .select("id")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not event_response.data:
        raise ApiError("Event not found", status_code=404)
    registrations_response = (
        client.table("registrations")
        .select("id,user_id,event_id,created_at,users(id,email,role)")
        .eq("event_id", event_id)
        .execute()
    )
    return jsonify({"data": registrations_response.data})
