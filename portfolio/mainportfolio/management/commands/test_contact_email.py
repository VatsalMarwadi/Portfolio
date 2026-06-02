"""Send a test contact email (user + admin). Usage: python manage.py test_contact_email"""

from django.conf import settings
from django.core.management.base import BaseCommand

from mainportfolio.models import Inquiry
from mainportfolio.services import _email_transport, send_inquiry_emails


class Command(BaseCommand):
    help = "Send test inquiry emails using the configured provider."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            default=settings.CONTACT_ADMIN_EMAIL,
            help="Recipient for the user confirmation test (default: CONTACT_ADMIN_EMAIL)",
        )

    def handle(self, *args, **options):
        transport = _email_transport()
        self.stdout.write(f"Email transport: {transport}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"CONTACT_ADMIN_EMAIL: {settings.CONTACT_ADMIN_EMAIL}")

        if transport == "none":
            self.stderr.write(
                self.style.ERROR(
                    "No email provider configured. Set SENDGRID_API_KEY, BREVO_API_KEY, "
                    "RESEND_API_KEY, or SMTP credentials in the environment."
                )
            )
            return

        inquiry = Inquiry(
            name="Test User",
            email=options["to"],
            subject="Test contact form email",
            message="This is a test message from manage.py test_contact_email.",
        )
        inquiry.save()

        result = send_inquiry_emails(inquiry, portfolio_url="https://example.com/home/")
        inquiry.delete()

        if result.get("user") and result.get("admin"):
            self.stdout.write(self.style.SUCCESS("Both emails sent successfully."))
        else:
            self.stderr.write(
                self.style.ERROR(
                    f"Email result: user={result.get('user')} admin={result.get('admin')} "
                    f"skipped={result.get('skipped')}. Check server logs for API errors."
                )
            )
