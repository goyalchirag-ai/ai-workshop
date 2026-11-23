from uuid import UUID

from flask import request

from app.errors import ApiError


def validate_uuid(value, field_name):
    if not value:
        raise ApiError(f"{field_name} is required")

    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as error:
        raise ApiError(f"{field_name} must be a valid UUID") from error


def require_query_uuid(field_name):
    return validate_uuid(request.args.get(field_name), field_name)


def require_json_object():
    if not request.is_json:
        raise ApiError("Content-Type must be application/json", status_code=415)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object")
    return payload
