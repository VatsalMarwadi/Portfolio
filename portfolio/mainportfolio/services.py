"""Business logic separated from views."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def build_email_context(request, inquiry):
    return {
        "name": inquiry.name,
        "email": inquiry.email,
        "subject": inquiry.subject,
        "message": inquiry.message,
        "portfolio_url": request.build_absolute_uri(reverse("mainportfolio:home")),
        "year": inquiry.created_at.year,
    }


def _email_configured():
    backend = settings.EMAIL_BACKEND
    if backend.endswith("console.EmailBackend"):
        return True
    return bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)


def send_inquiry_emails(request, inquiry):
    """
    Send confirmation to the user and notification to the admin.
    Never raises — callers should save the inquiry first.
    Returns {"user": bool, "admin": bool, "skipped": bool}.
    """
    if not _email_configured():
        logger.warning(
            "Email not configured; inquiry id=%s saved without sending mail",
            inquiry.pk,
        )
        return {"user": False, "admin": False, "skipped": True}

    context = build_email_context(request, inquiry)
    result = {"user": False, "admin": False, "skipped": False}

    user_html = render_to_string("portfolio/user_mail.html", context)
    user_email = EmailMultiAlternatives(
        subject="Thank You For Contacting Me",
        body=strip_tags(user_html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[inquiry.email],
    )
    user_email.attach_alternative(user_html, "text/html")
    try:
        user_email.send(fail_silently=False)
        result["user"] = True
    except Exception:
        logger.exception(
            "Failed to send user confirmation for inquiry id=%s", inquiry.pk
        )

    admin_html = render_to_string("portfolio/admin_mail.html", context)
    admin_email = EmailMultiAlternatives(
        subject=f"New Inquiry From {inquiry.name}",
        body=strip_tags(admin_html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_ADMIN_EMAIL],
    )
    admin_email.attach_alternative(admin_html, "text/html")
    try:
        admin_email.send(fail_silently=False)
        result["admin"] = True
    except Exception:
        logger.exception(
            "Failed to send admin notification for inquiry id=%s", inquiry.pk
        )

    if result["user"] or result["admin"]:
        logger.info(
            "Inquiry id=%s emails — user=%s admin=%s",
            inquiry.pk,
            result["user"],
            result["admin"],
        )

    return result
