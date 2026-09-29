import json
from pathlib import Path

from django.core.management.base import BaseCommand
from app1.models import GovernmentScheme


class Command(BaseCommand):
    help = "Import Government Schemes from JSON"

    def handle(self, *args, **kwargs):

        file_path = (
            Path(__file__).resolve().parent.parent.parent
            / "data"
            / "government_schemes.json"
        )

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0

        for scheme in data:

            GovernmentScheme.objects.update_or_create(
                scheme_name=scheme["scheme_name"],
                defaults={
                    "category": scheme["category"],
                    "description": scheme["description"],
                    "benefits": scheme["benefits"],
                    "eligibility": scheme["eligibility"],
                    "official_link": scheme["official_link"],
                },
            )

            count += 1

        self.stdout.write(
            self.style.SUCCESS(f"{count} schemes imported successfully.")
        )