import csv
import os

from django.core.management.base import BaseCommand

from app1.models import State, District, Taluka


class Command(BaseCommand):
    help = "Import India States, Districts and Talukas"

    def handle(self, *args, **kwargs):

        base_path = os.path.join("app1", "data")

        states_file = os.path.join(base_path, "states.csv")
        districts_file = os.path.join(base_path, "districts.csv")
        talukas_file = os.path.join(base_path, "subdistricts.csv")

        self.stdout.write(self.style.SUCCESS("Importing States..."))

        State.objects.all().delete()

        with open(states_file, encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                State.objects.create(
                    state_code=int(row["state_code"]),
                    name=row["state_name_english"].strip(),
                )

        self.stdout.write(self.style.SUCCESS("States Imported"))

        self.stdout.write(self.style.SUCCESS("Importing Districts..."))

        District.objects.all().delete()

        with open(districts_file, encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:

                try:
                    state = State.objects.get(
                        state_code=int(row["state_code"])
                    )

                    District.objects.create(
                        district_code=int(row["district_code"]),
                        state=state,
                        name=row["district_name_english"].strip(),
                    )

                except State.DoesNotExist:
                    pass

        self.stdout.write(self.style.SUCCESS("Districts Imported"))

        self.stdout.write(self.style.SUCCESS("Importing Talukas..."))

        Taluka.objects.all().delete()

        with open(talukas_file, encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:

                try:
                    district = District.objects.get(
                        district_code=int(row["district_code"])
                    )

                    Taluka.objects.create(
                        subdistrict_code=int(row["subdistrict_code"]),
                        district=district,
                        name=row["subdistrict_name_english"].strip(),
                    )

                except District.DoesNotExist:
                    pass

        self.stdout.write(self.style.SUCCESS("Talukas Imported"))

        self.stdout.write(self.style.SUCCESS("================================"))
        self.stdout.write(self.style.SUCCESS("India Location Import Completed"))
        self.stdout.write(self.style.SUCCESS("================================"))

        self.stdout.write(f"States : {State.objects.count()}")
        self.stdout.write(f"Districts : {District.objects.count()}")
        self.stdout.write(f"Talukas : {Taluka.objects.count()}")