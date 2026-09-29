from django.core.management.base import BaseCommand
from app1.services import fetch_and_update_gujarat_mandi_prices


class Command(BaseCommand):
    help = "Refresh agricultural mandi prices from official Government of India OGD (data.gov.in / Agmarknet)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--state",
            type=str,
            default="Gujarat",
            help="State to import mandi prices for (default: Gujarat)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=1000,
            help="Maximum records to fetch from OGD API (default: 1000)",
        )

    def handle(self, *args, **options):
        state = options["state"]
        limit = options["limit"]

        self.stdout.write(self.style.NOTICE(f"Connecting to official Government of India OGD data.gov.in API for State: {state}..."))
        result = fetch_and_update_gujarat_mandi_prices(state=state, limit=limit)

        if result.get("status") == "success":
            self.stdout.write(self.style.SUCCESS(
                f"Successfully updated Mandi Prices for {state}!\n"
                f" - Records Created: {result.get('imported', 0)}\n"
                f" - Records Updated: {result.get('updated', 0)}\n"
                f" - Total in Database: {result.get('total', 0)}\n"
                f" - Unique Mandis / Markets: {result.get('markets', 0)}\n"
                f" - Unique Commodities: {result.get('commodities', 0)}\n"
                f" - Latest Arrival Date: {result.get('latest_date', 'N/A')}"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Failed to update mandi prices: {result.get('message', 'Unknown error')}\n"
                f"Current total in database: {result.get('total', 0)}"
            ))
