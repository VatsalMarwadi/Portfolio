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
        RedirectView.as_view(url="/home/#hero", permanent=False),
        name=SECTION_HERO,
    ),
]

# Section shortcuts: /about/ → /home/#about (Django named URLs + browser hash)
for section in NAV_SECTIONS:
    slug = section["slug"]
    urlpatterns.append(
        path(
            f"{slug}/",
            RedirectView.as_view(url=f"/home/#{slug}", permanent=False),
            name=slug,
        ),
    )
