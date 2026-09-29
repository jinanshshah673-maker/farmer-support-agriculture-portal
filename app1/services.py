import os
import json
from datetime import datetime, date
from decimal import Decimal
import requests
from django.conf import settings
from django.db.models import Max, Min, Avg, Count
from app1.models import GovernmentScheme, Notification, MandiPrice

# ==============================================================================
# WEATHER SERVICE (OpenWeatherMap API)
# ==============================================================================

API_KEY = "4ec30f81ad80fa7df09f1eeaa5eb7dfc"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_weather(city="Ahmedabad"):
    """
    Fetches live weather and 5-day forecast from OpenWeatherMap.
    Returns structured weather dictionary or fallback info.
    """
    if not city:
        city = "Ahmedabad"

    try:
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"
        }

        response = requests.get(WEATHER_URL, params=params, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        weather = {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", "IN"),
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"].get("feels_like", data["main"]["temp"]), 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind": round(data["wind"]["speed"], 1),
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"].capitalize(),
            "icon": data["weather"][0]["icon"],
        }

        forecast = []
        forecast_response = requests.get(FORECAST_URL, params=params, timeout=10)

        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            # Step every 8 items (approx 24h interval)
            for item in forecast_data.get("list", [])[::8]:
                forecast.append({
                    "date": item["dt_txt"][:10],
                    "temperature": round(item["main"]["temp"], 1),
                    "condition": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"].capitalize(),
                    "humidity": item["main"].get("humidity", "--"),
                    "icon": item["weather"][0]["icon"],
                })

        return {
            "weather": weather,
            "forecast": forecast
        }

    except Exception:
        return None


# ==============================================================================
# CROP ADVISORY KNOWLEDGE BASE (Safe, educational guidance)
# ==============================================================================

CROP_ADVISORY_DATA = {
    "Wheat": {
        "name": "Wheat (Gahu)",
        "category": "Cereal",
        "season": "Rabi (Winter season, Oct - Dec sowing)",
        "climate": "Cool winter (15°C - 22°C) during vegetative growth, warm during ripening",
        "soil": "Well-drained fertile loamy, clay-loam or alluvial soil",
        "seed_rate": "40 - 50 kg per acre",
        "cultivation": "Plough the field 2-3 times to achieve fine tilth. Sow in rows with 20-22 cm row-to-row spacing and 4-5 cm depth. Ensure adequate soil moisture at sowing.",
        "irrigation": "4 to 6 irrigations at critical growth stages: Crown Root Initiation (CRI at 20-25 days), Tillering (40-45 days), Late Jointing (60-65 days), Flowering (80-85 days), and Milking/Dough stage (100-105 days).",
        "fertilizer": "Balanced N:P:K ratio (50:25:20 kg/acre). Apply all Phosphorus and Potash with 1/3rd Nitrogen as basal dose. Top dress remaining Nitrogen in two splits at 1st and 2nd irrigation.",
        "harvesting": "Harvest when straw turns golden yellow and grains become hard with less than 12-14% moisture. Store in clean, dry godowns.",
    },
    "Rice": {
        "name": "Rice / Paddy (Dangar)",
        "category": "Cereal",
        "season": "Kharif (Monsoon, June - July) & Summer (Zaid)",
        "climate": "Warm and humid (22°C - 32°C), requires abundant sunshine and water",
        "soil": "Clayey, clay loam or heavy alluvial soil with good water retention capacity",
        "seed_rate": "15 - 20 kg per acre for transplanted paddy",
        "cultivation": "Raise seedlings in nursery for 21-25 days. Puddle main field thoroughly to reduce water percolation. Transplant 2-3 seedlings per hill at 20x15 cm spacing.",
        "irrigation": "Keep 2-5 cm standing water during transplanting up to grain filling stage. Drain water 10-14 days before harvest.",
        "fertilizer": "Apply 40-50 kg Nitrogen, 20 kg P2O5, 20 kg K2O per acre. Incorporate well-decomposed FYM (4-5 tonnes/acre) during puddle preparation.",
        "harvesting": "Harvest when 80-85% of panicles turn straw yellow. Dry grains under sun to bring moisture down to 13-14% before storage.",
    },
    "Cotton": {
        "name": "Cotton (Kapas)",
        "category": "Cash Crop / Fiber",
        "season": "Kharif (May - June sowing)",
        "climate": "Semi-arid to tropical climate (21°C - 30°C) with at least 180-200 frost-free days",
        "soil": "Deep black soils (Regur) or medium-textured fertile loamy soils with good drainage",
        "seed_rate": "1.5 - 2.0 kg per acre (Bt / Hybrid cotton)",
        "cultivation": "Deep ploughing followed by harrowing. Maintain spacing of 90x60 cm or 120x45 cm depending on hybrid variety. Avoid water stagnation.",
        "irrigation": "Critical irrigation stages: Squaring (35-40 DAS), Flowering (60-70 DAS), and Boll development (85-100 DAS). Avoid excessive irrigation which causes vegetative overgrowth.",
        "fertilizer": "Balanced application of 48 kg N, 24 kg P2O5, 24 kg K2O per acre. Split nitrogen into 3 doses (basal, square formation, and peak flowering).",
        "harvesting": "Pick clean, fully opened bolls in the morning hours after dew has dried. Store seed cotton in dry, moisture-proof rooms.",
    },
    "Groundnut": {
        "name": "Groundnut (Magfali)",
        "category": "Oilseed / Legume",
        "season": "Kharif (June - July) & Summer (Jan - Feb)",
        "climate": "Warm, sunny climate (25°C - 30°C)",
        "soil": "Light sandy loam, well-drained loamy soil with neutral pH (6.0 - 7.5)",
        "seed_rate": "40 - 50 kg kernels per acre for bunch varieties",
        "cultivation": "Prepare friable loose seedbed. Treat seeds with Rhizobium culture. Maintain spacing of 30x10 cm. Hoeing and weeding must stop once pegging begins.",
        "irrigation": "Critical stages: Flowering, Pegging (30-45 DAS), and Pod formation (55-75 DAS). Light frequent irrigations are beneficial.",
        "fertilizer": "Apply 10 kg N, 20 kg P2O5, and 15 kg K2O per acre along with Gypsum (100 kg/acre) at flowering for calcium and sulfur supply.",
        "harvesting": "Harvest when leaves turn yellow and inner pod shell shows dark blackish discoloration. Dry pods under sun for 5-7 days.",
    },
    "Maize": {
        "name": "Maize / Corn (Makai)",
        "category": "Cereal / Coarse Grain",
        "season": "Kharif (June - July) & Rabi (Oct - Nov)",
        "climate": "Warm temperate to tropical (18°C - 30°C)",
        "soil": "Deep fertile loamy soil rich in organic matter with excellent drainage",
        "seed_rate": "8 - 10 kg per acre",
        "cultivation": "Plough 2-3 times. Form ridges and furrows. Sow seeds at 60x20 cm spacing and 3-4 cm depth.",
        "irrigation": "Tasseling, Silking, and Grain filling are the most critical irrigation stages. Water stress at flowering can reduce yield significantly.",
        "fertilizer": "Apply 48 kg N, 24 kg P2O5, 20 kg K2O per acre. Split Nitrogen into basal, knee-high stage, and tasseling stage.",
        "harvesting": "Harvest when outer cob husk dries and turns brownish paper-like. Grain moisture should be under 14% for storage.",
    },
    "Mustard": {
        "name": "Mustard / Rapeseed (Rai / Sarson)",
        "category": "Oilseed",
        "season": "Rabi (Oct - Nov sowing)",
        "climate": "Cool, dry climate with bright sunshine during flowering and pod development",
        "soil": "Sandy loam to clay loam soils with good drainage",
        "seed_rate": "1.5 - 2.0 kg per acre",
        "cultivation": "Fine, firm seedbed with conserved moisture. Sow in rows 30 cm apart, thin plants to maintain 10-12 cm spacing.",
        "irrigation": "Usually requires 2-3 irrigations: at rosette stage (25-30 DAS) and pod filling stage (55-60 DAS). Avoid waterlogging.",
        "fertilizer": "Apply 25-30 kg N, 15 kg P2O5, 10 kg K2O, and 10 kg Sulphur per acre. Sulphur is essential for oil percentage enhancement.",
        "harvesting": "Harvest as soon as 75% of siliquae (pods) turn golden yellow to prevent pod shattering. Thresh after sun drying.",
    },
    "Sugarcane": {
        "name": "Sugarcane (Sherdi)",
        "category": "Cash Crop",
        "season": "Autumn (Oct - Nov), Spring (Feb - March), or Adsali (July - Aug)",
        "climate": "Warm and humid (25°C - 35°C)",
        "soil": "Deep, well-drained loamy to heavy clay loam soil",
        "seed_rate": "12,000 - 15,000 two-budded setts per acre",
        "cultivation": "Trench or furrow planting at 90-120 cm row spacing. Treat setts with biofertilizers before planting.",
        "irrigation": "High water requirement. Provide regular irrigation every 8-12 days during formative and elongation stages.",
        "fertilizer": "High nutrient feeder. Apply 100 kg N, 40 kg P2O5, 50 kg K2O per acre in split doses during earthing up.",
        "harvesting": "Harvest when brix reading (sugar content) reaches 18-20% and lower leaves dry completely. Cut flush with ground level.",
    },
    "Soybean": {
        "name": "Soybean (Soyabean)",
        "category": "Oilseed / Legume",
        "season": "Kharif (June - July)",
        "climate": "Warm and moist (24°C - 30°C)",
        "soil": "Well-drained fertile black clay soils or sandy loams",
        "seed_rate": "25 - 30 kg per acre",
        "cultivation": "Sow on ridges or broad bed furrows at 45x10 cm spacing. Inoculate seeds with Bradyrhizobium culture.",
        "irrigation": "Primarily a rainfed crop, but supplemental irrigation at flowering and pod development prevents severe yield drop.",
        "fertilizer": "Apply 10-12 kg N (starter dose), 24 kg P2O5, and 16 kg K2O per acre.",
        "harvesting": "Harvest when pods turn brown/yellow and leaves drop naturally. Avoid delayed harvest to minimize shattering.",
    },
    "Potato": {
        "name": "Potato (Batata / Aloo)",
        "category": "Vegetable / Tuber",
        "season": "Rabi (Oct - Nov)",
        "climate": "Cool weather (15°C - 20°C for tuberization)",
        "soil": "Loose, friable, well-aerated sandy loam rich in organic matter",
        "seed_rate": "800 - 1000 kg seed tubers per acre",
        "cultivation": "Plant healthy certified seed tubers on ridges at 50-60 cm row distance and 15-20 cm plant spacing. Perform earthing up at 30-35 DAS.",
        "irrigation": "Light and frequent irrigations every 7-10 days. Stop irrigation 10 days before harvesting.",
        "fertilizer": "Apply 60 kg N, 35 kg P2O5, 50 kg K2O per acre. Incorporate 8-10 tonnes of FYM during land preparation.",
        "harvesting": "Dehaulm (cut foliage) 10-12 days prior to digging. Cure tubers in shade for 7-10 days before cold storage.",
    },
    "Tomato": {
        "name": "Tomato (Tameta)",
        "category": "Vegetable / Horticulture",
        "season": "Kharif (June - July), Rabi (Oct - Nov), and Summer (Jan - Feb)",
        "climate": "Mild climate (20°C - 28°C). Sensitive to frost and extreme heat",
        "soil": "Well-drained loamy or sandy loam soils with pH 6.0 - 7.0",
        "seed_rate": "60 - 80 grams per acre (hybrid seeds)",
        "cultivation": "Raise nursery for 25-30 days. Transplant on raised beds with drip irrigation and staking support. Spacing: 90x45 cm.",
        "irrigation": "Drip irrigation is highly recommended to maintain uniform soil moisture and prevent blossom end rot.",
        "fertilizer": "Apply 40 kg N, 25 kg P2O5, 35 kg K2O per acre. Use water-soluble fertilizers in drip fertigation.",
        "harvesting": "Harvest at breaker or pink stage for distant markets, and fully ripe red stage for local consumption.",
    },
    "Onion": {
        "name": "Onion (Dungri / Pyaz)",
        "category": "Vegetable / Bulb",
        "season": "Kharif (June - July) & Late Kharif / Rabi (Nov - Dec)",
        "climate": "Cool early vegetative phase (13°C - 24°C) and warm bulb maturity phase (25°C - 35°C)",
        "soil": "Fertile friable sandy loam to clay loam rich in humus",
        "seed_rate": "3.5 - 4.0 kg per acre",
        "cultivation": "Transplant 6-7 week old seedlings at 15x10 cm spacing on flat or raised beds.",
        "irrigation": "Frequent light irrigations every 6-8 days. Withhold water 10-15 days before harvesting to improve shelf life.",
        "fertilizer": "Apply 40 kg N, 20 kg P2O5, 20 kg K2O, and 15 kg Sulphur per acre.",
        "harvesting": "Harvest when 50% of the plant tops fall over (neck fall). Cure bulbs in field and shade for 10 days.",
    },
}


def get_crop_advisory(crop_name=""):
    """
    Returns advisory details for a given crop name, with intelligent matching.
    """
    if not crop_name:
        return None, list(CROP_ADVISORY_DATA.keys())

    crop_name_clean = crop_name.strip().title()

    # Exact match
    if crop_name_clean in CROP_ADVISORY_DATA:
        return CROP_ADVISORY_DATA[crop_name_clean], list(CROP_ADVISORY_DATA.keys())

    # Partial match
    for key, data in CROP_ADVISORY_DATA.items():
        if key.lower() in crop_name.lower() or crop_name.lower() in key.lower():
            return data, list(CROP_ADVISORY_DATA.keys())

    # Fallback to Wheat
    return CROP_ADVISORY_DATA.get("Wheat"), list(CROP_ADVISORY_DATA.keys())


# ==============================================================================
# FERTILIZER & NUTRIENT RECOMMENDATIONS (Educational & Safe)
# ==============================================================================

FERTILIZER_GUIDELINES = {
    "Black": {
        "characteristic": "High clay content, rich in calcium and magnesium, high water holding capacity, prone to cracking when dry.",
        "soil_care": "Avoid over-irrigation to prevent waterlogging. Apply organic manure and gypsum to improve aeration and drainage.",
        "npk_modifier": "Black soil is naturally adequate in Potassium (K) but deficient in Nitrogen (N) and Phosphorus (P).",
    },
    "Red": {
        "characteristic": "Rich in iron, porous and crumbly structure, low water holding capacity, deficient in nitrogen, phosphorus, and humus.",
        "soil_care": "Incorporate generous farmyard manure (FYM) or vermicompost to increase humus and moisture retention. Use split fertilizer doses.",
        "npk_modifier": "Requires higher basal dose of organic compost, balanced N and P supplements.",
    },
    "Alluvial": {
        "characteristic": "Highly fertile, balanced silt and loam texture, ideal for most crops, responsive to fertilizer applications.",
        "soil_care": "Maintain soil health by rotating legume crops and practicing green manuring.",
        "npk_modifier": "Generally rich in Potash and Lime, moderate in Phosphorus, responds well to balanced N-P-K.",
    },
    "Clay": {
        "characteristic": "Fine particles, heavy texture, poor internal drainage, compacts easily.",
        "soil_care": "Incorporate coarse organic material, straw, and well-rotted compost to lighten the soil texture.",
        "npk_modifier": "Nutrients leach slowly, avoid heavy single fertilizer applications.",
    },
    "Sandy": {
        "characteristic": "Coarse texture, high permeability, low nutrient retention, prone to rapid leaching.",
        "soil_care": "Add green manures, biochar, or vermicompost. Mulch heavily to conserve moisture.",
        "npk_modifier": "Apply Nitrogen and Potassium in 3 to 4 smaller split doses rather than large basal doses to prevent leaching.",
    },
    "Loamy": {
        "characteristic": "Ideal balanced agricultural soil with good drainage, aeration, and moisture retention.",
        "soil_care": "Standard organic maintenance and crop rotation maintain optimum fertility.",
        "npk_modifier": "Standard recommended N-P-K doses perform excellently.",
    },
}

CROP_FERTILIZER_DOSES = {
    "Wheat": {"N": 50, "P": 25, "K": 20, "organic": "4 - 5 tonnes FYM/acre", "bio": "Azotobacter + PSB culture"},
    "Rice": {"N": 45, "P": 20, "K": 20, "organic": "5 tonnes well-decomposed FYM/acre", "bio": "Blue Green Algae (BGA) or Azospirillum"},
    "Cotton": {"N": 48, "P": 24, "K": 24, "organic": "5 - 6 tonnes FYM + 250 kg Neem Cake/acre", "bio": "Azotobacter + PSB"},
    "Groundnut": {"N": 10, "P": 20, "K": 15, "organic": "3 - 4 tonnes FYM + 100 kg Gypsum/acre", "bio": "Rhizobium + PSB"},
    "Maize": {"N": 48, "P": 24, "K": 20, "organic": "4 tonnes FYM/acre", "bio": "Azotobacter"},
    "Mustard": {"N": 30, "P": 15, "K": 10, "organic": "3 tonnes FYM + 15 kg Elemental Sulphur/acre", "bio": "Azotobacter + PSB"},
    "Sugarcane": {"N": 100, "P": 40, "K": 50, "organic": "10 tonnes FYM or Pressmud/acre", "bio": "Gluconacetobacter + PSB"},
    "Soybean": {"N": 12, "P": 24, "K": 16, "organic": "3 tonnes FYM/acre", "bio": "Bradyrhizobium + PSB"},
    "Potato": {"N": 60, "P": 35, "K": 50, "organic": "8 tonnes FYM/acre", "bio": "Azotobacter + PSB"},
    "Tomato": {"N": 40, "P": 25, "K": 35, "organic": "6 tonnes Vermicompost/acre", "bio": "Azospirillum + Trichoderma"},
    "Onion": {"N": 40, "P": 20, "K": 20, "organic": "5 tonnes FYM + 15 kg Sulphur/acre", "bio": "Azospirillum + PSB"},
}


def get_fertilizer_recommendation(crop="Wheat", soil_type="Loamy"):
    """
    Returns tailored, educational nutrient recommendation for crop and soil type.
    """
    crop_clean = crop.strip().title()
    crop_dose = CROP_FERTILIZER_DOSES.get(crop_clean)

    if not crop_dose:
        # Fallback to closest or default
        crop_clean = "Wheat"
        crop_dose = CROP_FERTILIZER_DOSES["Wheat"]

    soil_info = FERTILIZER_GUIDELINES.get(soil_type, FERTILIZER_GUIDELINES["Loamy"])

    # Calculate splits
    is_sandy = soil_type == "Sandy"
    splits = [
        {
            "stage": "Basal Application (At Sowing / Transplanting)",
            "guidance": f"Apply 100% of organic compost ({crop_dose['organic']}), 100% Phosphorus (P2O5: {crop_dose['P']} kg/acre), 100% Potash (K2O: {crop_dose['K']} kg/acre), and {'25%' if is_sandy else '33%'} of Nitrogen (N)."
        },
        {
            "stage": "First Top Dressing (Vegetative / Tillering Stage)",
            "guidance": f"Apply {'25%' if is_sandy else '33%'} Nitrogen after weeding and first irrigation."
        },
        {
            "stage": "Second Top Dressing (Flowering / Booting Stage)",
            "guidance": f"Apply remaining Nitrogen {'25%' if is_sandy else '33%'} before peak flowering."
        },
    ]

    if is_sandy:
        splits.append({
            "stage": "Third Light Top Dressing (Grain / Boll Development)",
            "guidance": "Apply the final 25% Nitrogen split to avoid leaching loss in sandy soils."
        })

    return {
        "crop": crop_clean,
        "soil_type": soil_type,
        "crop_dose": crop_dose,
        "soil_info": soil_info,
        "splits": splits,
        "available_crops": list(CROP_FERTILIZER_DOSES.keys()),
        "available_soils": list(FERTILIZER_GUIDELINES.keys()),
    }


# ==============================================================================
# COMPOST INFORMATION MODULE
# ==============================================================================

def get_compost_guide():
    """
    Provides comprehensive educational material on farm composting methods.
    """
    return {
        "methods": [
            {
                "name": "Heap / Windrow Method",
                "tag": "Low Cost & High Volume",
                "description": "Ideal for open fields and large farm areas. Agricultural waste is stacked in long, above-ground heaps (4-5 ft high and 6-8 ft wide) allowing easy turning.",
                "duration": "8 - 12 Weeks",
            },
            {
                "name": "Pit Composting (Indore Method)",
                "tag": "Moisture Conserving",
                "description": "Pits of dimensions 10x6x3 ft are excavated. Layers of carbon-rich and nitrogen-rich materials are stacked alternately. Ideal for dry and windy zones.",
                "duration": "12 - 16 Weeks",
            },
            {
                "name": "Vermicomposting",
                "tag": "Premium Organic Biofertilizer",
                "description": "Uses specialized earthworms (Eisenia fetida) to convert agricultural bio-waste into nutrient-rich vermicast with beneficial soil microbes.",
                "duration": "6 - 8 Weeks",
            },
        ],
        "browns_vs_greens": {
            "browns": [
                "Dry leaves and garden trimmings",
                "Wheat / Paddy straw & stubble",
                "Crushed dry maize stalks & sugarcane trash",
                "Sawdust & wood shavings",
                "Dry cotton stalks (shredded)",
            ],
            "greens": [
                "Fresh cow dung & cattle slurry",
                "Fresh green crop residues & weeds (before seeding)",
                "Vegetable market leftovers",
                "Green leaves & grass clippings",
                "Pulse / Legume crop residues",
            ],
            "ratio": "Aim for a 30:1 Carbon-to-Nitrogen ratio (approx. 2 to 3 parts dry Browns for 1 part fresh Greens).",
        },
        "steps": [
            {
                "step": 1,
                "title": "Site Selection & Preparation",
                "text": "Select a well-drained, elevated spot shaded from direct afternoon sun and rain wash. Dig pit or demarcate heap area.",
            },
            {
                "step": 2,
                "title": "Layering the Bio-Waste",
                "text": "Base layer: 6-8 inches of coarse twigs/straw for aeration. Alternate 6 inches of green waste followed by 6 inches of brown waste. Sprinkle thin slurry of cow dung and fertile topsoil between layers.",
            },
            {
                "step": 3,
                "title": "Moisture Regulation",
                "text": "Maintain moisture around 50-60% (like a damp, squeezed sponge). Never allow waterlogging or complete drying.",
            },
            {
                "step": 4,
                "title": "Aeration & Periodic Turning",
                "text": "Turn the pile at Day 15, Day 30, and Day 45. Turning introduces fresh oxygen, regulates temperature (55-65°C kills pathogens/weed seeds), and speeds up decomposition.",
            },
            {
                "step": 5,
                "title": "Curing and Maturity Check",
                "text": "Compost is ready when it turns dark brown/black, smells like sweet forest earth, has a crumbly texture, and pile temperature drops to ambient levels.",
            },
        ],
        "benefits": [
            "Increases soil organic carbon and revitalizes beneficial soil microflora.",
            "Improves water holding capacity by up to 30%, reducing irrigation needs.",
            "Buffers soil pH and enhances nutrient availability (NPK + micronutrients).",
            "Saves fertilizer costs while eliminating open crop residue burning.",
        ],
        "precautions": [
            "DO NOT add diseased plant parts, weed plants with mature seeds, or plastic/synthetic materials.",
            "DO NOT add meat, oils, dairy, or dog/cat feces to avoid attracting pests or pathogens.",
            "Avoid excessive water addition, as anaerobic conditions cause foul odors and nutrient loss.",
            "Keep the pile covered with gunny bags or straw thatch to conserve moisture and beneficial earthworms.",
        ],
    }


# ==============================================================================
# FARMING NOTIFICATIONS & REMINDERS GENERATOR
# ==============================================================================

def generate_initial_farmer_notifications(farmer):
    """
    Populates initial contextual farming activity reminders for a newly registered
    farmer based on their registered crop and location.
    """
    crop = farmer.crop or "Crop"

    reminders = [
        {
            "title": f"{crop} Sowing Preparation Window",
            "message": f"Prepare seedbed with 2-3 deep ploughings for your {farmer.land_area} acres. Treat seeds with bio-fertilizers (Rhizobium/Azotobacter) before sowing to boost germination.",
            "notification_type": "sowing",
        },
        {
            "title": "Scheduled First Irrigation Reminder",
            "message": f"Ensure your first critical irrigation for {crop} is planned 20-25 days after sowing (Crown Root Initiation stage). Avoid water stagnation.",
            "notification_type": "irrigation",
        },
        {
            "title": "Basal Organic & Balanced Fertilizer Application",
            "message": f"Apply well-decomposed FYM or compost along with your basal Phosphorus and Potash dose according to your {farmer.soil_type} soil requirements.",
            "notification_type": "fertilizer",
        },
        {
            "title": "Regular Field Monitoring & Crop Health",
            "message": "Inspect your field weekly in morning hours for natural beneficial insects and early moisture deficiency symptoms. Practice clean weeding.",
            "notification_type": "crop_care",
        },
        {
            "title": "Weather Awareness for Farming Operations",
            "message": f"Check your local {farmer.district.name} weather forecast on the portal before applying top-dress fertilizer or scheduling heavy irrigations.",
            "notification_type": "weather_alert",
        },
        {
            "title": "Harvest Planning & Storage Preparation",
            "message": f"When {crop} reaches physiological maturity (golden straw color), stop irrigation 10 days in advance and prepare clean, moisture-free storage bags.",
            "notification_type": "harvesting",
        },
    ]

    for item in reminders:
        Notification.objects.create(
            farmer=farmer,
            title=item["title"],
            message=item["message"],
            notification_type=item["notification_type"],
        )


# ==============================================================================
# TEMPORARY & LEGACY HELPERS
# ==============================================================================

def get_pm_kisan_data():
    """PM-Kisan data helper."""
    return []


# ==============================================================================
# OFFICIAL GUJARAT MANDI PRICE SERVICE (data.gov.in / Agmarknet)
# ==============================================================================

def parse_mandi_date(date_str):
    """
    Safely parses arrival date strings from data.gov.in.
    Handles 'DD/MM/YYYY', 'DD-MM-YYYY', 'YYYY-MM-DD', etc.
    """
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_mandi_price(val):
    """Safely converts price strings or numbers into Decimal or None."""
    if val is None:
        return None
    val_str = str(val).strip().replace(",", "")
    if not val_str or val_str.lower() in ("na", "nan", "nil", "--", "-"):
        return None
    try:
        return Decimal(val_str)
    except Exception:
        try:
            return Decimal(str(round(float(val_str), 2)))
        except Exception:
            return None


def fetch_and_update_gujarat_mandi_prices(state="Gujarat", limit=1000):
    """
    Fetches official current daily mandi prices from data.gov.in / Agmarknet
    specifically for the state of Gujarat (and optionally other states).
    Saves records to MandiPrice model, preventing duplicates.
    Also creates a local backup snapshot in app1/data/gujarat_mandi_prices.json.
    """
    api_key = getattr(
        settings,
        "DATA_GOV_API_KEY",
        "579b464db66ec23bdd000001cdc3b564546246a772a26393094f5645"
    )
    resource_id = getattr(
        settings,
        "DATA_GOV_MANDI_RESOURCE_ID",
        "9ef84268-d588-465a-a308-a864a43d0070"
    )
    url = f"https://api.data.gov.in/resource/{resource_id}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    params = {
        "api-key": api_key,
        "format": "json",
        "limit": limit,
        "filters[state.keyword]": state,
    }

    records = []
    fetch_error = None
    backup_file = os.path.join(settings.BASE_DIR, "app1", "data", "gujarat_mandi_prices.json")

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            records = data.get("records", [])
            # If state.keyword returned empty, try filters[state]
            if not records:
                params["filters[state]"] = state
                params.pop("filters[state.keyword]", None)
                r2 = requests.get(url, params=params, headers=headers, timeout=25)
                if r2.status_code == 200:
                    records = r2.json().get("records", [])

            # If records were successfully fetched, save a local backup copy
            if records:
                os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
        else:
            fetch_error = f"API returned HTTP status {resp.status_code}"
    except Exception as exc:
        fetch_error = str(exc)

    # Fallback to local backup snapshot if live API was unreachable and DB is empty
    if not records and os.path.exists(backup_file):
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            pass

    if not records:
        return {
            "status": "error",
            "message": fetch_error or "No records returned from data.gov.in",
            "imported": 0,
            "updated": 0,
            "total": MandiPrice.objects.filter(state__iexact=state).count(),
        }

    created_count = 0
    updated_count = 0

    for rec in records:
        rec_state = (rec.get("state") or state).strip()
        rec_district = (rec.get("district") or "Other").strip()
        rec_market = (rec.get("market") or "Unknown Mandi").strip()
        rec_commodity = (rec.get("commodity") or "").strip()
        rec_variety = (rec.get("variety") or "Other").strip()
        rec_grade = (rec.get("grade") or "FAQ").strip()

        arr_date = parse_mandi_date(rec.get("arrival_date"))
        if not arr_date or not rec_commodity:
            continue

        min_p = parse_mandi_price(rec.get("min_price"))
        max_p = parse_mandi_price(rec.get("max_price"))
        modal_p = parse_mandi_price(rec.get("modal_price"))

        # Deduplication using update_or_create
        obj, created = MandiPrice.objects.update_or_create(
            state=rec_state,
            district=rec_district,
            market=rec_market,
            commodity=rec_commodity,
            variety=rec_variety,
            arrival_date=arr_date,
            defaults={
                "grade": rec_grade,
                "min_price": min_p,
                "max_price": max_p,
                "modal_price": modal_p,
                "unit": "₹/Quintal",
                "source": "data.gov.in / Agmarknet",
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    total_in_db = MandiPrice.objects.filter(state__iexact=state).count()
    markets_count = MandiPrice.objects.filter(state__iexact=state).values("market").distinct().count()
    commodities_count = MandiPrice.objects.filter(state__iexact=state).values("commodity").distinct().count()
    latest_arr = MandiPrice.objects.filter(state__iexact=state).aggregate(Max("arrival_date"))["arrival_date__max"]

    return {
        "status": "success",
        "imported": created_count,
        "updated": updated_count,
        "total": total_in_db,
        "markets": markets_count,
        "commodities": commodities_count,
        "latest_date": str(latest_arr) if latest_arr else None,
    }


def get_gujarat_mandi_summary():
    """
    Returns summary analytics for the Gujarat mandi prices in database.
    """
    qs = MandiPrice.objects.filter(state__iexact="Gujarat")
    total_records = qs.count()

    if total_records == 0:
        return {
            "has_data": False,
            "markets_count": 0,
            "commodities_count": 0,
            "districts_count": 0,
            "records_count": 0,
            "latest_arrival_date": None,
            "latest_fetch_time": None,
        }

    markets_count = qs.values("market").distinct().count()
    commodities_count = qs.values("commodity").distinct().count()
    districts_count = qs.values("district").distinct().count()
    latest_arr = qs.aggregate(Max("arrival_date"))["arrival_date__max"]
    latest_fetch = qs.aggregate(Max("fetched_at"))["fetched_at__max"]

    return {
        "has_data": True,
        "markets_count": markets_count,
        "commodities_count": commodities_count,
        "districts_count": districts_count,
        "records_count": total_records,
        "latest_arrival_date": latest_arr,
        "latest_fetch_time": latest_fetch,
    }


def get_best_mandi_prices(commodity_name):
    """
    Finds the highest and lowest modal price mandis in Gujarat for a commodity,
    along with the price spread and average modal price.
    """
    if not commodity_name:
        return None

    qs = MandiPrice.objects.filter(
        state__iexact="Gujarat",
        commodity__iexact=commodity_name,
        modal_price__isnull=False
    ).exclude(modal_price=0)

    if not qs.exists():
        # Try icontains
        qs = MandiPrice.objects.filter(
            state__iexact="Gujarat",
            commodity__icontains=commodity_name,
            modal_price__isnull=False
        ).exclude(modal_price=0)

    if not qs.exists():
        return None

    # Get latest date available for this commodity to compare fairly
    latest_date = qs.aggregate(Max("arrival_date"))["arrival_date__max"]
    if latest_date:
        date_qs = qs.filter(arrival_date=latest_date)
        if not date_qs.exists():
            date_qs = qs
    else:
        date_qs = qs

    highest = date_qs.order_by("-modal_price", "-max_price").first()
    lowest = date_qs.order_by("modal_price", "min_price").first()
    stats = date_qs.aggregate(avg_price=Avg("modal_price"), count=Count("id"))

    spread = None
    if highest and lowest and highest.modal_price and lowest.modal_price:
        spread = highest.modal_price - lowest.modal_price

    return {
        "commodity": commodity_name,
        "highest": highest,
        "lowest": lowest,
        "avg_price": round(stats.get("avg_price") or 0, 1),
        "reporting_mandis": stats.get("count") or 0,
        "spread": spread,
        "arrival_date": latest_date,
    }


def get_commodity_chart_data(commodity_name):
    """
    Returns Chart.js compatible payload comparing modal prices
    for the selected commodity across Gujarat mandis.
    """
    if not commodity_name:
        return None

    qs = MandiPrice.objects.filter(
        state__iexact="Gujarat",
        commodity__iexact=commodity_name,
        modal_price__isnull=False
    ).exclude(modal_price=0)

    if not qs.exists():
        qs = MandiPrice.objects.filter(
            state__iexact="Gujarat",
            commodity__icontains=commodity_name,
            modal_price__isnull=False
        ).exclude(modal_price=0)

    if not qs.exists():
        return None

    # Filter to latest arrival date for consistency
    latest_date = qs.aggregate(Max("arrival_date"))["arrival_date__max"]
    if latest_date:
        qs = qs.filter(arrival_date=latest_date)

    # Order by modal price descending, take top 15 mandis
    top_records = qs.order_by("-modal_price")[:15]

    labels = []
    modal_prices = []
    min_prices = []
    max_prices = []

    for r in top_records:
        # shorten mandi name for readability on charts
        short_market = r.market.replace(" APMC", "").replace(" Market", "").strip()
        labels.append(f"{short_market} ({r.district})")
        modal_prices.append(float(r.modal_price))
        min_prices.append(float(r.min_price) if r.min_price else float(r.modal_price))
        max_prices.append(float(r.max_price) if r.max_price else float(r.modal_price))

    return {
        "commodity": commodity_name,
        "date": str(latest_date) if latest_date else "",
        "labels": labels,
        "modal_prices": modal_prices,
        "min_prices": min_prices,
        "max_prices": max_prices,
    }


def get_district_mandi_tree():
    """
    Builds a hierarchical summary:
    Gujarat -> District -> list of Markets.
    Used for district-wise browsing.
    """
    records = MandiPrice.objects.filter(state__iexact="Gujarat").values("district", "market").distinct().order_by("district", "market")
    tree = {}
    for r in records:
        dist = r["district"]
        mkt = r["market"]
        if dist not in tree:
            tree[dist] = []
        if mkt not in tree[dist]:
            tree[dist].append(mkt)
    return tree