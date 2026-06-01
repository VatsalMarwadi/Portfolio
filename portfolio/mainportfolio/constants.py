"""Site-wide constants for URLs and navigation."""

from django.urls import reverse

# Single-page section anchors (must match template id attributes)
SECTION_HERO = "hero"
SECTION_ABOUT = "about"
SECTION_EDUCATION = "education"
SECTION_PROJECTS = "projects"
SECTION_CONTACT = "contact"

VALID_SECTIONS = frozenset({
    SECTION_HERO,
    SECTION_ABOUT,
    SECTION_EDUCATION,
    SECTION_PROJECTS,
    SECTION_CONTACT,
})

# Navigation sections exposed in the header (excludes hero)
NAV_SECTIONS = (
    {"slug": SECTION_ABOUT, "label": "About"},
    {"slug": SECTION_EDUCATION, "label": "Education"},
    {"slug": SECTION_PROJECTS, "label": "Projects"},
    {"slug": SECTION_CONTACT, "label": "Contact"},
)


def section_url(slug):
    """Named URL for a section (redirects to /home/#slug)."""
    return reverse(f"mainportfolio:{slug}")


def home_section_url(slug):
    """Direct home URL with hash fragment (no redirect)."""
    return f"{reverse('mainportfolio:home')}#{slug}"
