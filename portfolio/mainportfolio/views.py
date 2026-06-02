import logging
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .constants import SECTION_CONTACT, VALID_SECTIONS
from .forms import ContactForm
from .models import Education, Inquiry, Link, Projects, Skills
from .services import send_inquiry_emails

logger = logging.getLogger(__name__)

CONTACT_RATE_LIMIT = 5
CONTACT_RATE_WINDOW = 3600  # seconds


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _rate_limit_contact(request):
    key = f"contact:{_client_ip(request)}"
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
        with transaction.atomic():
            inquiry = Inquiry.objects.create(
                name=data["name"],
                email=data["email"],
                subject=data["subject"],
                message=data["message"],
                ip_address=_client_ip(request),
            )
            # send_inquiry_emails(request, inquiry)
    except Exception:
        logger.exception("Contact form failed for %s", data.get("email"))
        if _is_ajax(request):
            return JsonResponse(
                {"success": False, "error": "Could not send message. Please try again."},
                status=500,
            )
        messages.error(request, "Could not send your message. Please try again later.")
        ctx = _page_context(request, contact_form=form, active_section=SECTION_CONTACT)
        return render(request, "portfolio/index.html", ctx, status=500)

    if _is_ajax(request):
        return JsonResponse({"success": True})

    messages.success(request, "Your message was sent successfully.")
    return redirect(reverse("mainportfolio:contact"))


# Backwards-compatible alias
index = home
