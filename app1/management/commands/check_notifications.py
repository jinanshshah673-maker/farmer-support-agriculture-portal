from django.core.management.base import BaseCommand
from app1.models import Farmer, Notification, GovernmentScheme, MandiPrice
from app1.services import get_weather, get_best_mandi_prices, get_crop_advisory
from datetime import datetime
import json

class Command(BaseCommand):
    help = 'Checks for real updates and generates notifications for farmers.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting notification check...")
        
        farmers = Farmer.objects.select_related('district').all()
        today_str = datetime.now().strftime("%Y-%m-%d")
        week_num = datetime.now().isocalendar()[1]
        
        weather_created = 0
        scheme_created = 0
        market_created = 0
        advisory_created = 0

        latest_scheme = GovernmentScheme.objects.last()

        for farmer in farmers:
            # 1. WEATHER ALERTS
            if farmer.district:
                city = farmer.district.name
                weather_data = get_weather(city)
                if weather_data and weather_data.get("weather"):
                    w_info = weather_data["weather"]
                    condition = w_info.get("condition", "").lower()
                    description = w_info.get("description", "").lower()
                    
                    # Check if weather is dangerous
                    severe = False
                    if any(c in condition for c in ["rain", "storm", "thunder", "extreme"]):
                        severe = True
                    if "heavy" in description:
                        severe = True

                    if severe:
                        ref_id = f"weather_{farmer.id}_{today_str}"
                        if not Notification.objects.filter(reference_id=ref_id).exists():
                            Notification.objects.create(
                                farmer=farmer,
                                title=f"⚠️ Weather Alert: {w_info.get('condition')}",
                                message=f"Severe weather ({description}) is expected in {city}. Please take necessary precautions for your crops.",
                                notification_type="weather_alert",
                                reference_id=ref_id
                            )
                            weather_created += 1

            # 2. GOVERNMENT SCHEMES
            if latest_scheme:
                ref_id = f"scheme_{farmer.id}_{latest_scheme.id}"
                if not Notification.objects.filter(reference_id=ref_id).exists():
                    Notification.objects.create(
                        farmer=farmer,
                        title=f"New Government Scheme: {latest_scheme.scheme_name}",
                        message=f"A new scheme has been added in the {latest_scheme.category} category. Check the eligibility and benefits.",
                        notification_type="government_scheme",
                        reference_id=ref_id
                    )
                    scheme_created += 1

            # 3. MARKET PRICE
            if farmer.crop:
                market_data = get_best_mandi_prices(farmer.crop)
                if market_data and market_data.get("arrival_date"):
                    arr_date = market_data["arrival_date"]
                    ref_id = f"market_{farmer.id}_{farmer.crop}_{arr_date}"
                    if not Notification.objects.filter(reference_id=ref_id).exists():
                        highest = market_data.get("highest")
                        if highest:
                            Notification.objects.create(
                                farmer=farmer,
                                title=f"🌾 Market Update for {farmer.crop}",
                                message=f"New mandi prices are available for {farmer.crop}. Highest price is ₹{highest.modal_price} at {highest.market} APMC.",
                                notification_type="market_price",
                                reference_id=ref_id
                            )
                            market_created += 1

            # 4. CROP ADVISORY
            if farmer.crop:
                advisory, _ = get_crop_advisory(farmer.crop)
                if advisory:
                    ref_id = f"advisory_{farmer.id}_{farmer.crop}_{today_str}_{week_num}"
                    if not Notification.objects.filter(reference_id=ref_id).exists():
                        Notification.objects.create(
                            farmer=farmer,
                            title=f"🌱 Crop Advisory: {advisory.get('name')}",
                            message=f"Timely reminder: {advisory.get('irrigation', 'Ensure proper care for your crop this week.')}",
                            notification_type="crop_advisory",
                            reference_id=ref_id
                        )
                        advisory_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done! Created:\n"
            f"- {weather_created} weather alerts\n"
            f"- {scheme_created} scheme notifications\n"
            f"- {market_created} market notifications\n"
            f"- {advisory_created} crop advisories"
        ))
