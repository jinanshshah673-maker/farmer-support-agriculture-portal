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

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

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

        self.stdout.write(
            self.style.SUCCESS("Government Schemes Updated Successfully!")
        )