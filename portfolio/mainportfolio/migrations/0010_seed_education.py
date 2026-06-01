from django.db import migrations


def seed_education(apps, schema_editor):
    Education = apps.get_model("mainportfolio", "Education")
    if Education.objects.exists():
        return

    Education.objects.create(
        degree_name="Master of Computer Applications",
        university_name="CHARUSAT University",
        city="Anand",
        state="Gujarat",
        start_year=2024,
        end_year=None,
        cgpa=8.70,
        description=(
            "Specialising in Full Stack Development, DevOps pipelines, Cloud "
            "infrastructure and applied Data Science. Emphasis on production-grade "
            "systems and architectural thinking."
        ),
        technologies=[
            "Full Stack",
            "DevOps",
            "Cloud",
            "Data Science",
            "PostgreSQL",
        ],
        status="pursuing",
        display_order=2,
        duration_label="Ongoing",
        is_visible=True,
    )

    Education.objects.create(
        degree_name="Bachelor of Computer Applications",
        university_name="Your University",
        city="City",
        state="Gujarat",
        start_year=2021,
        end_year=2024,
        cgpa=8.20,
        description=(
            "Core foundations in programming, algorithms, database systems and "
            "software engineering. Built a strong problem-solving mindset through "
            "project-based learning."
        ),
        technologies=["Python", "Java", "SQL", "DSA", "Web Dev"],
        status="completed",
        display_order=1,
        duration_label="",
        is_visible=True,
    )


def unseed_education(apps, schema_editor):
    Education = apps.get_model("mainportfolio", "Education")
    Education.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("mainportfolio", "0009_education"),
    ]

    operations = [
        migrations.RunPython(seed_education, unseed_education),
    ]
