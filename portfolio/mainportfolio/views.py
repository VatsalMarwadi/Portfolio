import logging
from collections import defaultdict

from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from django.conf import settings
from django.views.decorators.cache import never_cache

from .constants import SECTION_CONTACT, VALID_SECTIONS
from .forms import ContactForm
from .models import Education, Inquiry, Link, Projects, Skills
from .services import _email_transport, send_inquiry_emails
from .utils import client_ip

logger = logging.getLogger(__name__)

CONTACT_RATE_LIMIT = 5
CONTACT_RATE_WINDOW = 3600  # seconds


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _rate_limit_key(request):
    ip = client_ip(request)
    if ip:
        return f"contact:{ip}"
    if not request.session.session_key:
        request.session.create()
    return f"contact:session:{request.session.session_key}"


def _rate_limit_contact(request):
    key = _rate_limit_key(request)
    count = cache.get(key, 0)
    if count >= CONTACT_RATE_LIMIT:
        return False
    cache.set(key, count + 1, CONTACT_RATE_WINDOW)
    return True


def _active_section(request):
    section = request.GET.get("section", "").strip().lower()
    if section in VALID_SECTIONS:
        return section
    return ""


def _page_context(request, contact_form=None, active_section=""):
    skills = Skills.objects.all()
    grouped_skills = defaultdict(list)
    for skill in skills:
        grouped_skills[skill.category].append(skill)

    educations = Education.objects.filter(is_visible=True)
    education_completed_count = educations.filter(
        status=Education.Status.COMPLETED
    ).count()

    return {
        "grouped_skills": dict(grouped_skills),
        "projects": Projects.objects.filter(is_published=True),
        "links": Link.objects.filter(is_visible=True),
        "educations": educations,
        "education_completed_count": education_completed_count,
        "contact_form": contact_form or ContactForm(),
        "active_section": active_section,
        "home_url": reverse("mainportfolio:home"),
    }


def _json_errors(form):
    return {field: errors[0] for field, errors in form.errors.items()}


@require_http_methods(["GET", "POST"])
def home(request):
    active_section = _active_section(request)

    if request.method == "POST":
        return _handle_contact_post(request, active_section)

    return render(
        request,
        "portfolio/index.html",
        _page_context(request, active_section=active_section),
    )


def _handle_contact_post(request, active_section):
    form = ContactForm(request.POST)

    if not form.is_valid():
        if _is_ajax(request):
            return JsonResponse(
                {"success": False, "errors": _json_errors(form)},
                status=400,
            )
        messages.error(request, "Please correct the errors in the form.")
        ctx = _page_context(request, contact_form=form, active_section=active_section)
        return render(request, "portfolio/index.html", ctx, status=400)

    if not _rate_limit_contact(request):
        msg = "Too many messages sent. Please try again later."
        if _is_ajax(request):
            return JsonResponse({"success": False, "error": msg}, status=429)
        messages.error(request, msg)
        ctx = _page_context(request, contact_form=form, active_section=SECTION_CONTACT)
        return render(request, "portfolio/index.html", ctx, status=429)

    data = form.cleaned_data

    try:
        inquiry = Inquiry.objects.create(
            name=data["name"],
            email=data["email"],
            subject=data["subject"],
            message=data["message"],
            ip_address=client_ip(request),
        )
    except Exception:
        logger.exception("Inquiry save failed for %s", data.get("email"))
        if _is_ajax(request):
            return JsonResponse(
                {"success": False, "error": "Could not save your message. Please try again."},
                status=500,
            )
        messages.error(request, "Could not send your message. Please try again later.")
        ctx = _page_context(request, contact_form=form, active_section=SECTION_CONTACT)
        return render(request, "portfolio/index.html", ctx, status=500)

    portfolio_url = request.build_absolute_uri(reverse("mainportfolio:home"))
    email_result = send_inquiry_emails(inquiry, portfolio_url)

    if _is_ajax(request):
        if email_result.get("skipped"):
            message = (
                "Your message was saved, but email is not configured on the server yet."
            )
        elif email_result.get("user") and email_result.get("admin"):
            message = "Your message was sent successfully. We'll be in touch soon."
        elif email_result.get("admin"):
            message = (
                "Your message was received. If you don't see a confirmation email, "
                "please check Spam/Junk."
            )
        else:
            message = (
                "Your message was saved, but email delivery failed. "
                "We will still reply to you."
            )
        return JsonResponse(
            {
                "success": True,
                "message": message,
                "email": {
                    "user": bool(email_result.get("user")),
                    "admin": bool(email_result.get("admin")),
                    "skipped": bool(email_result.get("skipped")),
                },
            }
        )

    if email_result.get("skipped"):
        messages.warning(
            request,
            "Message saved, but email is not configured on the server yet.",
        )
    elif email_result.get("user") and email_result.get("admin"):
        messages.success(request, "Your message was sent successfully.")
    else:
        messages.warning(
            request,
            "Message saved, but email delivery failed. We will still reply to you.",
        )
    return redirect(reverse("mainportfolio:contact"))


@never_cache
def email_diag(request):
    """
    Diagnostic endpoint — only accessible to logged-in staff.
    Visit /email-diag/ on Render to confirm configuration.
    """
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Staff only.")

    transport = _email_transport()
    config = {
        "transport": transport,
        "EMAIL_BACKEND": settings.EMAIL_BACKEND,
        "EMAIL_HOST": settings.EMAIL_HOST,
        "EMAIL_PORT": settings.EMAIL_PORT,
        "EMAIL_USE_TLS": settings.EMAIL_USE_TLS,
        "EMAIL_HOST_USER": settings.EMAIL_HOST_USER,
        "EMAIL_HOST_PASSWORD_set": bool(settings.EMAIL_HOST_PASSWORD),
        "SENDGRID_API_KEY_set": bool(getattr(settings, "SENDGRID_API_KEY", "")),
        "BREVO_API_KEY_set": bool(getattr(settings, "BREVO_API_KEY", "")),
        "RESEND_API_KEY_set": bool(getattr(settings, "RESEND_API_KEY", "")),
        "DEFAULT_FROM_EMAIL": settings.DEFAULT_FROM_EMAIL,
        "CONTACT_ADMIN_EMAIL": settings.CONTACT_ADMIN_EMAIL,
        "DEBUG": settings.DEBUG,
    }

    if request.GET.get("send_test") == "1" and transport != "none":
        from .models import Inquiry as InquiryModel
        test_inq = InquiryModel(
            name="Diag Test",
            email=settings.CONTACT_ADMIN_EMAIL,
            subject="[DIAG] Email config test",
            message="This is a diagnostic test from /email-diag/.",
        )
        test_inq.save()
        result = send_inquiry_emails(
            test_inq,
            request.build_absolute_uri(reverse("mainportfolio:home")),
        )
        test_inq.delete()
        return JsonResponse({"config": config, "send_result": result})

    return JsonResponse({"config": config, "tip": "Add ?send_test=1 to send a test email."})


# Backwards-compatible alias
index = home
