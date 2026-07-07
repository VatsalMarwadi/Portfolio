from django.urls import reverse

from .constants import NAV_SECTIONS, SECTION_HERO


def navigation(request):
    """Global nav links using Django URL names."""
    home_url = reverse("mainportfolio:home")
    sections = []
    for item in NAV_SECTIONS:
        slug = item["slug"]
        sections.append(
            {
                "slug": slug,
                "label": item["label"],
                "url": reverse(f"mainportfolio:{slug}"),
            }
        )
    return {
        "nav_sections": sections,
        "home_url": home_url,
        "hero_url": reverse(f"mainportfolio:{SECTION_HERO}"),
        "projects_url": reverse("mainportfolio:projects"),
        "contact_url": reverse("mainportfolio:contact"),
        "site_name": "vm.dev",
    }
