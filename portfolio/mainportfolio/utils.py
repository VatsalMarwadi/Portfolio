"""Shared helpers for views and services."""

from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address


def client_ip(request):
    """Client IP for logging/rate limits; None if missing or invalid."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
    else:
        candidate = (request.META.get("REMOTE_ADDR") or "").strip()

    if not candidate or candidate.lower() == "unknown":
        return None

    try:
        validate_ipv46_address(candidate)
    except ValidationError:
        return None

    return candidate
