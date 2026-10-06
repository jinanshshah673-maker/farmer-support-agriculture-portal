from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.core.paginator import Paginator
import json
from django.db.models import Q
import os
from django.core.management import call_command

from .forms import FarmerRegistrationForm, FarmingReminderForm
from .models import (
    GovernmentScheme,
    State,
    District,
    Taluka,
    Farmer,
    Notification,
    MandiPrice,
)
from .services import (
    get_weather,
    get_crop_advisory,
    get_fertilizer_recommendation,
    get_compost_guide,
    generate_initial_farmer_notifications,
    get_gujarat_mandi_summary,
    get_best_mandi_prices,
    get_commodity_chart_data,
)


def get_current_farmer(user):
    """Helper to retrieve Farmer profile for authenticated user."""
    if not user.is_authenticated:
        return None
    farmer = Farmer.objects.filter(user=user).select_related('state', 'district', 'taluka').first()
    if not farmer:
        farmer = Farmer.objects.filter(
            Q(email__iexact=user.email) | Q(mobile=user.username)
        ).select_related('state', 'district', 'taluka').first()
    return farmer


# ------------------------------------------------------------------------------
# HOME
# ------------------------------------------------------------------------------

def home(request):
    schemes_count = GovernmentScheme.objects.count()
    states_count = State.objects.count()
    districts_count = District.objects.count()
    talukas_count = Taluka.objects.count()

    farmer = get_current_farmer(request.user)

    context = {
        "schemes_count": schemes_count,
        "states_count": states_count,
        "districts_count": districts_count,
        "talukas_count": talukas_count,
        "farmer": farmer,
    }
    return render(request, "home.html", context)


# ------------------------------------------------------------------------------
# AUTHENTICATION: REGISTER, LOGIN, LOGOUT
# ------------------------------------------------------------------------------

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = FarmerRegistrationForm(request.POST)

        if form.is_valid():
            raw_password = form.cleaned_data["password"]
            mobile = form.cleaned_data["mobile"]
            email = form.cleaned_data["email"]
            name = form.cleaned_data["name"]

            # Create or update associated Django User
            user = User.objects.filter(username=mobile).first()
            if not user:
                user = User.objects.create_user(
                    username=mobile,
                    email=email,
                    password=raw_password,
                    first_name=name
                )
            else:
                user.set_password(raw_password)
                user.email = email
                user.first_name = name
                user.save()

            farmer = form.save(commit=False)
            farmer.user = user
            farmer.password = make_password(raw_password)
            farmer.save()

            # Seed initial personalized farming reminders
            generate_initial_farmer_notifications(farmer)

            # Automatically log the farmer in
            authenticated_user = authenticate(request, username=mobile, password=raw_password)
            if authenticated_user:
                auth_login(request, authenticated_user)
                messages.success(request, f"Welcome to Farmer Support Portal, {farmer.name}! Your account was registered successfully.")
                return redirect("dashboard")

            messages.success(request, "Registration successful! Please login with your mobile number and password.")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors in the form below.")

    else:
        form = FarmerRegistrationForm()

    states = State.objects.all().order_by("name")

    return render(
        request,
        "register.html",
        {
            "form": form,
            "states": states,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        login_input = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        resolved_username = None

        # Check if login_input is a mobile number matching a Farmer
        farmer = Farmer.objects.filter(mobile=login_input).first()
        if farmer and farmer.user:
            resolved_username = farmer.user.username

        # Check if login_input is an email matching a User or Farmer
        if not resolved_username:
            user_by_email = User.objects.filter(email__iexact=login_input).first()
            if user_by_email:
                resolved_username = user_by_email.username

        # Otherwise try direct username
        if not resolved_username:
            resolved_username = login_input

        user = authenticate(request, username=resolved_username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get("next") or "dashboard"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid mobile/username or password. Please try again.")

    return render(request, "login.html")


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("home")


# ------------------------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------------------------

@login_required(login_url="login")
def dashboard(request):
    farmer = get_current_farmer(request.user)

    # If farmer profile doesn't exist for superuser/admin, handle gracefully
    notifications = []
    unread_notifications_count = 0
    if farmer:
        notifications = Notification.objects.filter(farmer=farmer)[:5]
        unread_notifications_count = Notification.objects.filter(farmer=farmer, is_read=False).count()

    # Weather preview for farmer's city / district
    city = "Ahmedabad"
    if farmer and farmer.district:
        city = farmer.district.name

    weather_data = get_weather(city)

    schemes_count = GovernmentScheme.objects.count()

    context = {
        "farmer": farmer,
        "notifications": notifications,
        "unread_notifications_count": unread_notifications_count,
        "weather": weather_data.get("weather") if weather_data else None,
        "schemes_count": schemes_count,
        "city": city,
    }
    return render(request, "dashboard.html", context)


# ------------------------------------------------------------------------------
# GOVERNMENT SCHEMES
# ------------------------------------------------------------------------------

def government_schemes(request):
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()

    schemes = GovernmentScheme.objects.all().order_by("scheme_name")

    if search:
        schemes = schemes.filter(
            Q(scheme_name__icontains=search) |
            Q(description__icontains=search) |
            Q(benefits__icontains=search)
        )

    if category in ["Central", "Gujarat"]:
        schemes = schemes.filter(category=category)

    farmer = get_current_farmer(request.user)

    return render(
        request,
        "government_schemes.html",
        {
            "schemes": schemes,
            "search": search,
            "category": category,
            "farmer": farmer,
        },
    )


# ------------------------------------------------------------------------------
# WEATHER FORECAST
# ------------------------------------------------------------------------------

def weather(request):
    farmer = get_current_farmer(request.user)

    default_city = "Ahmedabad"
    if farmer and farmer.district:
        default_city = farmer.district.name

    city = request.GET.get("city", default_city).strip() or default_city

    result = get_weather(city)

    weather_info = None
    forecast = []

    if result:
        weather_info = result.get("weather")
        forecast = result.get("forecast", [])

    return render(
        request,
        "weather.html",
        {
            "weather": weather_info,
            "forecast": forecast,
            "city": city,
            "farmer": farmer,
        },
    )


# ------------------------------------------------------------------------------
# CROP ADVISORY
# ------------------------------------------------------------------------------

def crop_advisory(request):
    farmer = get_current_farmer(request.user)

    default_crop = "Wheat"
    if farmer and farmer.crop:
        default_crop = farmer.crop

    selected_crop = request.GET.get("crop", default_crop).strip() or default_crop

    advisory, available_crops = get_crop_advisory(selected_crop)

    return render(
        request,
        "crop_advisory.html",
        {
            "advisory": advisory,
            "available_crops": available_crops,
            "selected_crop": selected_crop,
            "farmer": farmer,
        },
    )


# ------------------------------------------------------------------------------
# FERTILIZER RECOMMENDATIONS
# ------------------------------------------------------------------------------

def fertilizer(request):
    farmer = get_current_farmer(request.user)

    default_crop = "Wheat"
    default_soil = "Loamy"

    if farmer:
        if farmer.crop:
            default_crop = farmer.crop
        if farmer.soil_type:
            default_soil = farmer.soil_type

    crop = request.GET.get("crop", default_crop).strip() or default_crop
    soil = request.GET.get("soil", default_soil).strip() or default_soil

    rec = get_fertilizer_recommendation(crop, soil)

    return render(
        request,
        "fertilizer.html",
        {
            "rec": rec,
            "crop": crop,
            "soil": soil,
            "farmer": farmer,
        },
    )


# ------------------------------------------------------------------------------
# COMPOST INFORMATION MODULE
# ------------------------------------------------------------------------------

def compost(request):
    farmer = get_current_farmer(request.user)
    guide = get_compost_guide()
    return render(
        request,
        "compost.html",
        {
            "guide": guide,
            "farmer": farmer,
        },
    )


# ------------------------------------------------------------------------------
# MARKET PRICE MODULE
# ------------------------------------------------------------------------------

def market_price(request):
    farmer = get_current_farmer(request.user)

    selected_state = request.GET.get("state", "Gujarat")
    selected_commodity = request.GET.get("commodity", "")
    selected_market = request.GET.get("market", "")

    # Get distinct commodities from the database
    commodities = MandiPrice.objects.filter(state__iexact="Gujarat").values_list("commodity", flat=True).distinct().order_by("commodity")

    qs = MandiPrice.objects.filter(state__iexact="Gujarat")

    if selected_commodity:
        qs = qs.filter(commodity__icontains=selected_commodity)
    if selected_market:
        qs = qs.filter(Q(market__icontains=selected_market) | Q(district__icontains=selected_market))
        
    qs = qs.order_by("-arrival_date", "-modal_price")
    
    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    summary = get_gujarat_mandi_summary()
    
    best_prices = None
    chart_data = None
    
    # Default chart/insights to Wheat or the selected commodity
    target_commodity = selected_commodity if selected_commodity else "Wheat"
    if summary.get("has_data"):
        best_prices = get_best_mandi_prices(target_commodity)
        chart_data = get_commodity_chart_data(target_commodity)

    return render(
        request,
        "market_price.html",
        {
            "selected_state": selected_state,
            "selected_commodity": selected_commodity,
            "selected_market": selected_market,
            "commodities": commodities,
            "page_obj": page_obj,
            "summary": summary,
            "best_prices": best_prices,
            "chart_data": json.dumps(chart_data) if chart_data else None,
            "target_commodity": target_commodity,
            "farmer": farmer,
        },
    )


# ------------------------------------------------------------------------------
# FARMER NOTIFICATIONS & REMINDERS
# ------------------------------------------------------------------------------

@login_required(login_url="login")
def notifications_view(request):
    farmer = get_current_farmer(request.user)

    if not farmer:
        messages.warning(request, "Farmer profile not found. Please complete your registration.")
        return redirect("dashboard")

    # Add new reminder form
    if request.method == "POST" and "add_reminder" in request.POST:
        reminder_form = FarmingReminderForm(request.POST)
        if reminder_form.is_valid():
            reminder = reminder_form.save(commit=False)
            reminder.farmer = farmer
            reminder.save()
            messages.success(request, "Farming activity reminder created successfully!")
            return redirect("notifications")
    else:
        reminder_form = FarmingReminderForm()

    # Filters
    filter_type = request.GET.get("type", "")
    filter_status = request.GET.get("status", "")

    notifications_qs = Notification.objects.filter(farmer=farmer)

    if filter_type:
        notifications_qs = notifications_qs.filter(notification_type=filter_type)

    if filter_status == "unread":
        notifications_qs = notifications_qs.filter(is_read=False)
    elif filter_status == "read":
        notifications_qs = notifications_qs.filter(is_read=True)

    unread_count = Notification.objects.filter(farmer=farmer, is_read=False).count()

    return render(
        request,
        "notifications.html",
        {
            "farmer": farmer,
            "notifications": notifications_qs,
            "unread_count": unread_count,
            "filter_type": filter_type,
            "filter_status": filter_status,
            "reminder_form": reminder_form,
        },
    )


@login_required(login_url="login")
def mark_notification_read(request, pk):
    farmer = get_current_farmer(request.user)
    if not farmer:
        return JsonResponse({"status": "error", "message": "Unauthorized"}, status=403)

    notification = get_object_or_404(Notification, id=pk, farmer=farmer)
    notification.is_read = True
    notification.save()

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("ajax"):
        return JsonResponse({"status": "success", "id": pk})

    return redirect("notifications")


@login_required(login_url="login")
def mark_all_notifications_read(request):
    farmer = get_current_farmer(request.user)
    if farmer:
        Notification.objects.filter(farmer=farmer, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
    return redirect("notifications")


# ------------------------------------------------------------------------------
# AJAX LOCATION API
# ------------------------------------------------------------------------------

def load_districts(request):
    state_id = request.GET.get("state")
    if not state_id:
        return JsonResponse([], safe=False)

    districts = District.objects.filter(
        state_id=state_id
    ).order_by("name")

    data = list(districts.values("id", "name"))
    return JsonResponse(data, safe=False)


def load_talukas(request):
    district_id = request.GET.get("district")
    if not district_id:
        return JsonResponse([], safe=False)

    talukas = Taluka.objects.filter(
        district_id=district_id
    ).order_by("name")

    data = list(talukas.values("id", "name"))
    return JsonResponse(data, safe=False)

# ------------------------------------------------------------------------------
# CRON JOB ENDPOINT FOR VERCEL
# ------------------------------------------------------------------------------

def check_notifications_cron(request):
    """
    Secure endpoint to be triggered by Vercel Cron to generate notifications.
    """
    auth_header = request.headers.get("Authorization")
    cron_secret = os.environ.get("CRON_SECRET", "dev-secret")
    
    # Check either Authorization header or GET parameter for secret
    if auth_header != f"Bearer {cron_secret}" and request.GET.get("secret") != cron_secret:
        return JsonResponse({"error": "Unauthorized"}, status=401)
        
    try:
        call_command("check_notifications")
        return JsonResponse({"status": "success", "message": "Notifications generated"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)