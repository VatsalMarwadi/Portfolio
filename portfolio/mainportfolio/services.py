"""Business logic separated from views."""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def build_email_context(inquiry, portfolio_url):
    return {
        "name": inquiry.name,
        "email": inquiry.email,
        "subject": inquiry.subject,
        "message": inquiry.message,
        "portfolio_url": portfolio_url,
        "year": inquiry.created_at.year,
    }


def _from_email_address():
    """Extract bare email from DEFAULT_FROM_EMAIL (may include a display name)."""
    raw = settings.DEFAULT_FROM_EMAIL or ""
    if "<" in raw and ">" in raw:
        return raw.split("<", 1)[1].split(">", 1)[0].strip()
    return raw.strip()


def _email_configured():
    if getattr(settings, "SENDGRID_API_KEY", ""):
        return True
    backend = settings.EMAIL_BACKEND
    if backend.endswith("console.EmailBackend"):
        return True
    return bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)


def _send_via_sendgrid_api(*, to_email, subject, html_body):
    api_key = getattr(settings, "SENDGRID_API_KEY", "")
    if not api_key:
        return False

    from_email = _from_email_address()
    if not from_email:
        logger.error("DEFAULT_FROM_EMAIL is not set for SendGrid")
        return False

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": strip_tags(html_body)},
            {"type": "text/html", "value": html_body},
        ],
    }
    request = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("SendGrid API %s: %s", exc.code, body)
    except Exception:
        logger.exception("SendGrid API request failed for %s", to_email)
    return False


def _send_via_smtp(*, to_email, subject, html_body):
    email = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)
    return True


def _deliver_email(*, to_email, subject, html_body):
    if getattr(settings, "SENDGRID_API_KEY", ""):
        return _send_via_sendgrid_api(
            to_email=to_email, subject=subject, html_body=html_body
        )
    return _send_via_smtp(to_email=to_email, subject=subject, html_body=html_body)


def send_inquiry_emails(inquiry, portfolio_url):
    """
    Send confirmation to the user and notification to the admin.
    Never raises. Returns {"user": bool, "admin": bool, "skipped": bool}.
    """
    if not _email_configured():
        logger.warning(
            "Email not configured; inquiry id=%s saved without sending mail",
            inquiry.pk,
        )
        return {"user": False, "admin": False, "skipped": True}

    try:
        context = build_email_context(inquiry, portfolio_url)
        user_html = render_to_string("portfolio/user_mail.html", context)
        admin_html = render_to_string("portfolio/admin_mail.html", context)
    except Exception:
        logger.exception("Failed to render email templates for inquiry id=%s", inquiry.pk)
        return {"user": False, "admin": False, "skipped": False}

    result = {"user": False, "admin": False, "skipped": False}

    try:
        result["user"] = _deliver_email(
            to_email=inquiry.email,
            subject="Thank You For Contacting Me",
            html_body=user_html,
        )
    except Exception:
        logger.exception(
            "Failed to send user confirmation for inquiry id=%s", inquiry.pk
        )

    try:
        result["admin"] = _deliver_email(
            to_email=settings.CONTACT_ADMIN_EMAIL,
            subject=f"New Inquiry From {inquiry.name}",
            html_body=admin_html,
        )
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


def dispatch_inquiry_emails(inquiry_id, portfolio_url):
    """Background worker: load inquiry and send mail (safe to run in a thread)."""
    from .models import Inquiry

    try:
        inquiry = Inquiry.objects.get(pk=inquiry_id)
        send_inquiry_emails(inquiry, portfolio_url)
    except Inquiry.DoesNotExist:
        logger.error("Inquiry id=%s not found for email dispatch", inquiry_id)
    except Exception:
        logger.exception("Email dispatch failed for inquiry id=%s", inquiry_id)
