"""Reusable validators for portfolio models and forms."""

import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone

CURRENT_YEAR = timezone.now().year
MIN_EDUCATION_YEAR = 1990
MAX_EDUCATION_YEAR = CURRENT_YEAR + 8
MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_TECHNOLOGY_ITEMS = 25
MAX_TECHNOLOGY_ITEM_LENGTH = 50

_url_validator = URLValidator(schemes=("http", "https", "mailto"))


def validate_education_year(value):
    if value < MIN_EDUCATION_YEAR or value > MAX_EDUCATION_YEAR:
        raise ValidationError(
            f"Year must be between {MIN_EDUCATION_YEAR} and {MAX_EDUCATION_YEAR}."
        )


def validate_cgpa(value):
    if value is not None and (value < 0 or value > 10):
        raise ValidationError("CGPA must be between 0 and 10.")


def validate_image_file_size(upload):
    if upload and upload.size > MAX_IMAGE_BYTES:
        raise ValidationError(
            f"Image must be {MAX_IMAGE_BYTES // (1024 * 1024)} MB or smaller."
        )


def validate_technology_list(values):
    if not values:
        return
    if len(values) > MAX_TECHNOLOGY_ITEMS:
        raise ValidationError(
            f"Maximum {MAX_TECHNOLOGY_ITEMS} technology tags allowed."
        )
    for item in values:
        if len(item) > MAX_TECHNOLOGY_ITEM_LENGTH:
            raise ValidationError(
                f"Each technology must be at most {MAX_TECHNOLOGY_ITEM_LENGTH} characters."
            )


def parse_comma_separated_list(raw):
    """Turn 'Python, Django' into ['Python', 'Django']."""
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if not raw:
        return []
    return [item.strip() for item in str(raw).split(",") if item.strip()]


def validate_safe_url(value):
    if not value:
        return
    if value.lower().startswith(("javascript:", "data:", "vbscript:")):
        raise ValidationError("Invalid URL scheme.")
    _url_validator(value)


def validate_person_name(value):
    value = (value or "").strip()
    if len(value) < 2:
        raise ValidationError("Name must be at least 2 characters.")
    if not re.match(r"^[\w\s.\-']+$", value, re.UNICODE):
        raise ValidationError("Name contains invalid characters.")
