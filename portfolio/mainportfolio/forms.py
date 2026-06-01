from django import forms

from .models import Education, Projects
from .validators import parse_comma_separated_list, validate_person_name


class CommaSeparatedArrayField(forms.CharField):
    """Admin-friendly comma-separated input for Postgres ArrayFields."""

    def prepare_value(self, value):
        if isinstance(value, list):
            return ", ".join(value)
        return value or ""

    def clean(self, value):
        return parse_comma_separated_list(super().clean(value))


class ContactForm(forms.Form):
    """Public contact form with honeypot anti-spam field."""

    name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "id": "fname",
                "placeholder": "John Doe",
                "autocomplete": "name",
            }
        ),
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "id": "femail",
                "placeholder": "john@example.com",
                "autocomplete": "email",
            }
        ),
    )
    subject = forms.CharField(
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "id": "fsubject",
                "placeholder": "Project Inquiry",
            }
        ),
    )
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                "class": "form-textarea",
                "id": "fmsg",
                "rows": 4,
                "placeholder": "Tell me about your project...",
            }
        ),
    )
    # Honeypot — hidden from users, must stay empty
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-honeypot",
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        validate_person_name(name)
        return name

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_subject(self):
        return self.cleaned_data["subject"].strip()

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError(
                "Please write at least 10 characters in your message."
            )
        return message

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Submission rejected.")
        return ""


class ProjectsAdminForm(forms.ModelForm):
    technology = CommaSeparatedArrayField(required=False)

    class Meta:
        model = Projects
        fields = "__all__"


class EducationAdminForm(forms.ModelForm):
    technologies = CommaSeparatedArrayField(
        required=False,
        help_text="Comma-separated list of skills or subjects.",
    )

    class Meta:
        model = Education
        fields = "__all__"
