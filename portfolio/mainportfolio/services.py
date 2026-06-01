"""Business logic separated from views."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def build_email_context(request, inquiry):
    from django.urls import reverse

    return {
        "name": inquiry.name,
        "email": inquiry.email,
        "subject": inquiry.subject,
        "message": inquiry.message,
        "portfolio_url": request.build_absolute_uri(reverse("mainportfolio:home")),
        "year": inquiry.created_at.year,
    }


def send_inquiry_emails(request, inquiry):
    """Send confirmation to user and notification to admin. Raises on failure."""
    context = build_email_context(request, inquiry)

    user_html = render_to_string("portfolio/user_mail.html", context)
    user_email = EmailMultiAlternatives(
        subject="Thank You For Contacting Me",
        body=strip_tags(user_html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[inquiry.email],
    )
    user_email.attach_alternative(user_html, "text/html")
    user_email.send(fail_silently=False)

    admin_html = render_to_string("portfolio/admin_mail.html", context)
    admin_email = EmailMultiAlternatives(
        subject=f"New Inquiry From {inquiry.name}",
        body=strip_tags(admin_html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_ADMIN_EMAIL],
    )
    admin_email.attach_alternative(admin_html, "text/html")
    admin_email.send(fail_silently=False)

    logger.info("Inquiry emails sent for inquiry id=%s", inquiry.pk)
