from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxLengthValidator
from django.db import models
from django.utils import timezone

from .validators import (
    validate_cgpa,
    validate_education_year,
    validate_image_file_size,
    validate_safe_url,
    validate_technology_list,
)

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]


class Skills(models.Model):
    skill_name = models.CharField(
        max_length=50,
        validators=[MaxLengthValidator(50)],
    )
    category = models.CharField(
        max_length=30,
        validators=[MaxLengthValidator(30)],
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Higher numbers appear first within a category.",
    )

    class Meta:
        ordering = ["category", "-display_order", "skill_name"]
        verbose_name_plural = "Skills"
        indexes = [
            models.Index(fields=["category", "-display_order"]),
        ]

    def __str__(self):
        return f"{self.skill_name} ({self.category})"


class Projects(models.Model):
    project_name = models.CharField(max_length=120)
    description = models.TextField(
        validators=[MaxLengthValidator(2000)],
    )
    technology = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
    )
    preview = models.ImageField(
        upload_to="projects/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(IMAGE_EXTENSIONS),
            validate_image_file_size,
        ],
    )
    github_url = models.URLField(blank=True, default="")
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Higher numbers appear first.",
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Uncheck to hide from the public site.",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-display_order", "-created_at"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        indexes = [
            models.Index(fields=["-display_order", "is_published"]),
        ]

    def __str__(self):
        return self.project_name

    def clean(self):
        validate_technology_list(self.technology)
        if self.github_url:
            validate_safe_url(self.github_url)


class Inquiry(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=120)
    message = models.TextField(validators=[MaxLengthValidator(5000)])
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.subject}"


class Link(models.Model):
    link_name = models.CharField(max_length=50)
    url = models.URLField(max_length=500)
    display_order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "link_name"]
        indexes = [
            models.Index(fields=["display_order", "is_visible"]),
        ]

    def __str__(self):
        return self.link_name

    def clean(self):
        if self.url:
            validate_safe_url(self.url)

    @property
    def href(self):
        """URL safe for use in templates."""
        return self.url


class Education(models.Model):
    class Status(models.TextChoices):
        PURSUING = "pursuing", "Pursuing"
        COMPLETED = "completed", "Completed"

    degree_name = models.CharField(max_length=120)
    university_name = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    start_year = models.PositiveIntegerField(validators=[validate_education_year])
    end_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[validate_education_year],
    )
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[validate_cgpa],
    )
    description = models.TextField(validators=[MaxLengthValidator(2000)])
    technologies = ArrayField(
        models.CharField(max_length=50),
        blank=True,
        default=list,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
    )
    display_order = models.PositiveIntegerField(default=0)
    duration_label = models.CharField(max_length=40, blank=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-display_order", "-start_year"]
        verbose_name_plural = "Education"
        indexes = [
            models.Index(fields=["is_visible", "-display_order"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.degree_name} — {self.university_name}"

    def clean(self):
        validate_technology_list(self.technologies)
        if self.end_year and self.start_year and self.end_year < self.start_year:
            raise ValidationError(
                {"end_year": "End year cannot be before start year."}
            )
        if self.status == self.Status.COMPLETED and not self.end_year:
            raise ValidationError(
                {"end_year": "Completed education requires an end year."}
            )

    @property
    def year_range(self):
        if self.status == self.Status.PURSUING or not self.end_year:
            return f"{self.start_year} — Present"
        return f"{self.start_year} — {self.end_year}"

    @property
    def school_line(self):
        return f"{self.university_name} · {self.city}, {self.state}"

    @property
    def duration_display(self):
        if self.duration_label:
            return self.duration_label
        if self.status == self.Status.PURSUING:
            return "Ongoing"
        if self.end_year and self.start_year:
            years = self.end_year - self.start_year
            if years <= 0:
                return "1 Year"
            return f"{years} Year{'s' if years != 1 else ''}"
        return ""

    @property
    def status_pill_class(self):
        return "active" if self.status == self.Status.PURSUING else "completed"

    @property
    def status_label(self):
        if self.status == self.Status.PURSUING:
            return "● Pursuing"
        return "Completed"
