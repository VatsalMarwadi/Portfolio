from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.admin.sites import NotRegistered

from .forms import EducationAdminForm, ProjectsAdminForm
from .models import Education, Inquiry, Link, Projects, Skills

try:
    admin.site.unregister(User)
except NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


@admin.register(Skills)
class SkillsAdmin(admin.ModelAdmin):
    list_display = ("skill_name", "category", "display_order")
    list_filter = ("category",)
    search_fields = ("skill_name", "category")
    ordering = ("category", "-display_order", "skill_name")
    list_editable = ("display_order",)


@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    form = ProjectsAdminForm
    list_display = (
        "project_name",
        "is_published",
        "display_order",
        "has_preview",
        "updated_at",
    )
    list_filter = ("is_published", "created_at")
    search_fields = ("project_name", "description")
    ordering = ("-display_order", "-created_at")
    list_editable = ("is_published", "display_order")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("project_name", "description", "is_published", "display_order")}),
        ("Media & links", {"fields": ("preview", "github_url")}),
        ("Technologies", {"fields": ("technology",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(boolean=True, description="Preview")
    def has_preview(self, obj):
        return bool(obj.preview)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "ip_address")
    search_fields = ("name", "email", "subject", "message")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    readonly_fields = ("name", "email", "subject", "message", "ip_address", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("link_name", "url", "display_order", "is_visible")
    search_fields = ("link_name", "url")
    ordering = ("display_order", "link_name")
    list_editable = ("display_order", "is_visible")


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    form = EducationAdminForm
    list_display = (
        "degree_name",
        "university_name",
        "year_range_display",
        "status",
        "cgpa",
        "display_order",
        "is_visible",
    )
    list_filter = ("status", "is_visible", "state")
    search_fields = ("degree_name", "university_name", "city", "state")
    ordering = ("-display_order", "-start_year")
    list_editable = ("display_order", "is_visible")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "degree_name",
                    "university_name",
                    "city",
                    "state",
                    "status",
                    "is_visible",
                    "display_order",
                ),
            },
        ),
        ("Timeline", {"fields": ("start_year", "end_year", "duration_label")}),
        ("Details", {"fields": ("cgpa", "description", "technologies")}),
    )

    @admin.display(description="Year range")
    def year_range_display(self, obj):
        return obj.year_range
