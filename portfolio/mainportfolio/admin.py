from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.admin.sites import NotRegistered
from django.utils.html import format_html

from .forms import EducationAdminForm, ProjectsAdminForm, ProjectImageAdminForm
from .models import Education, Inquiry, Link, Projects, Skills, ProjectImage

try:
    admin.site.unregister(User)
except NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except NotRegistered:
    pass

# ── Inline for Project Images ──
class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    form = ProjectImageAdminForm
    extra = 1
    fields = ('image', 'caption', 'display_order')
    ordering = ('display_order',)
    max_num = 10
    classes = ('collapse',)
    verbose_name = "Gallery Image"
    verbose_name_plural = "Gallery Images"

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
    inlines = [ProjectImageInline]
    
    list_display = (
        "project_name",
        "category",
        "is_published",
        "display_order",
        "has_preview",
        "has_gallery_images",
        "updated_at",
    )
    list_filter = ("is_published", "category", "created_at")
    search_fields = ("project_name", "description", "full_description")
    ordering = ("-display_order", "-created_at")
    list_editable = ("is_published", "display_order")
    readonly_fields = ("created_at", "updated_at", "preview_preview")

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "project_name",
                "category",
                "description",
                "full_description",
                "is_published",
                "display_order",
            )
        }),
        ("Media & Links", {
            "fields": (
                "preview",
                "preview_preview",
                "github_url",
                "live_url",
            )
        }),
        ("Technologies", {
            "fields": ("technology",),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("project_year",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(boolean=True, description="Preview Image")
    def has_preview(self, obj):
        return bool(obj.preview)

    @admin.display(boolean=True, description="Has Gallery")
    def has_gallery_images(self, obj):
        return obj.images.exists()

    @admin.display(description="Preview")
    def preview_preview(self, obj):
        if obj.preview:
            return format_html(
                '<img src="{}" style="max-height: 150px; max-width: 200px; border-radius: 8px; object-fit: cover;" />',
                obj.preview.url
            )
        return "No preview image"


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


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "caption", "display_order", "created_at")
    list_filter = ("project", "created_at")
    search_fields = ("caption", "project__project_name")
    ordering = ("project", "display_order")
    list_editable = ("display_order",)
    raw_id_fields = ("project",)
    fields = ("project", "image", "caption", "display_order")