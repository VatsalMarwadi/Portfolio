from django.urls import reverse

from .constants import NAV_SECTIONS


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
                "home_hash_url": f"{home_url}#{slug}",
            }
        )
    return {
        "nav_sections": sections,
        "home_url": home_url,
        "site_name": "vm.dev",
    }
