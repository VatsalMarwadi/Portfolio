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


def _email_transport():
    """Which delivery method is active (first match wins)."""
    if getattr(settings, "SENDGRID_API_KEY", ""):
        return "sendgrid"
    if getattr(settings, "BREVO_API_KEY", ""):
        return "brevo"
    if getattr(settings, "RESEND_API_KEY", ""):
        return "resend"
    backend = settings.EMAIL_BACKEND
    if backend.endswith("console.EmailBackend"):
        return "console"
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        return "smtp"
    return "none"


def _email_configured():
    return _email_transport() != "none"


def _http_post_json(url, payload, headers, timeout):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return 200 <= response.status < 300


def _send_via_sendgrid_api(*, to_email, subject, html_body):
    api_key = settings.SENDGRID_API_KEY
    from_email = _from_email_address()
    if not from_email:
        logger.error("DEFAULT_FROM_EMAIL is required for SendGrid")
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
    try:
        return _http_post_json(
            "https://api.sendgrid.com/v3/mail/send",
            payload,
            {"Authorization": f"Bearer {api_key}"},
            settings.EMAIL_TIMEOUT,
        )
    except urllib.error.HTTPError as exc:
        logger.error(
            "SendGrid API %s: %s",
            exc.code,
            exc.read().decode("utf-8", errors="replace"),
        )
    except Exception:
        logger.exception("SendGrid API failed for %s", to_email)
    return False


def _send_via_brevo_api(*, to_email, subject, html_body):
    api_key = settings.BREVO_API_KEY
    from_email = _from_email_address()
    if not from_email:
        logger.error("DEFAULT_FROM_EMAIL is required for Brevo")
        return False

    payload = {
        "sender": {"email": from_email, "name": "Portfolio"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": strip_tags(html_body),
    }
    try:
        return _http_post_json(
            "https://api.brevo.com/v3/smtp/email",
            payload,
            {"api-key": api_key},
            settings.EMAIL_TIMEOUT,
        )
    except urllib.error.HTTPError as exc:
        logger.error(
            "Brevo API %s: %s",
            exc.code,
            exc.read().decode("utf-8", errors="replace"),
        )
    except Exception:
        logger.exception("Brevo API failed for %s", to_email)
    return False


def _send_via_resend_api(*, to_email, subject, html_body):
    api_key = settings.RESEND_API_KEY
    from_email = settings.DEFAULT_FROM_EMAIL or _from_email_address()
    if not from_email:
        logger.error("DEFAULT_FROM_EMAIL is required for Resend")
        return False

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }
    try:
        return _http_post_json(
            "https://api.resend.com/emails",
            payload,
            {"Authorization": f"Bearer {api_key}"},
            settings.EMAIL_TIMEOUT,
        )
    except urllib.error.HTTPError as exc:
        logger.error(
            "Resend API %s: %s",
            exc.code,
            exc.read().decode("utf-8", errors="replace"),
        )
    except Exception:
        logger.exception("Resend API failed for %s", to_email)
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


def _send_via_console(*, to_email, subject, html_body):
    email = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send()
    return True


def _deliver_email(*, to_email, subject, html_body):
    transport = _email_transport()
    if transport == "sendgrid":
        return _send_via_sendgrid_api(
            to_email=to_email, subject=subject, html_body=html_body
        )
    if transport == "brevo":
        return _send_via_brevo_api(
            to_email=to_email, subject=subject, html_body=html_body
        )
    if transport == "resend":
        return _send_via_resend_api(
            to_email=to_email, subject=subject, html_body=html_body
        )
    if transport == "console":
        return _send_via_console(
            to_email=to_email, subject=subject, html_body=html_body
        )
    if transport == "smtp":
        return _send_via_smtp(
            to_email=to_email, subject=subject, html_body=html_body
        )
    return False


def send_inquiry_emails(inquiry, portfolio_url):
    """
    Send confirmation to the user and notification to the admin.
    Never raises. Returns {"user": bool, "admin": bool, "skipped": bool}.
    """
    transport = _email_transport()
    if transport == "none":
        logger.warning(
            "Email not configured; inquiry id=%s saved without sending mail",
            inquiry.pk,
        )
        return {"user": False, "admin": False, "skipped": True}

    if transport == "smtp" and not settings.DEBUG:
        logger.warning(
            "Using SMTP on production (inquiry id=%s). Gmail often fails on Render; "
            "set SENDGRID_API_KEY or BREVO_API_KEY for reliable delivery.",
            inquiry.pk,
        )

    try:
        context = build_email_context(inquiry, portfolio_url)
        user_html = render_to_string("portfolio/user_mail.html", context)
        admin_html = render_to_string("portfolio/admin_mail.html", context)
    except Exception:
        logger.exception(
            "Failed to render email templates for inquiry id=%s", inquiry.pk
        )
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
            "Inquiry id=%s emails via %s — user=%s admin=%s",
            inquiry.pk,
            transport,
            result["user"],
            result["admin"],
        )
    else:
        logger.error(
            "Inquiry id=%s: no emails delivered (transport=%s)",
            inquiry.pk,
            transport,
        )

    return result
