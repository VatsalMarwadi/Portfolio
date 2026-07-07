from django.urls import path
from django.views.generic import RedirectView

from . import views
from .constants import NAV_SECTIONS, SECTION_HERO

app_name = "mainportfolio"

urlpatterns = [
    path(
        "",
        RedirectView.as_view(pattern_name="mainportfolio:home", permanent=False),
        name="root",
    ),
    path("home/", views.home, name="home"),
    path(
        f"{SECTION_HERO}/",
        views.section,
        {"section_slug": SECTION_HERO},
        name=SECTION_HERO,
    ),
]

for section in NAV_SECTIONS:
    slug = section["slug"]
    urlpatterns.append(
        path(
            f"{slug}/",
            views.section,
            {"section_slug": slug},
            name=slug,
        ),
    )