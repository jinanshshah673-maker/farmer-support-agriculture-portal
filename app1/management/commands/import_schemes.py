import json
from pathlib import Path

from django.core.management.base import BaseCommand
from app1.models import GovernmentScheme


class Command(BaseCommand):
    help = "Import Government Schemes from JSON"

    def handle(self, *args, **kwargs):

        file_path = (
            Path(__file__)
            .resolve()
            .parents[2]
            / "data"
            / "government_schemes.json"
        )

        with open(file_path, "r", encoding="utf-8") as f:
            schemes = json.load(f)

        GovernmentScheme.objects.all().delete()

        for scheme in schemes:

            GovernmentScheme.objects.create(
                scheme_name=scheme.get("scheme_name", ""),
                category=scheme.get("category", "Central"),
                description=scheme.get("description", ""),
                benefits=scheme.get("benefits", ""),
                eligibility=scheme.get("eligibility", ""),
                official_link=scheme.get("official_link", ""),
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {GovernmentScheme.objects.count()} schemes successfully."
            )
        )