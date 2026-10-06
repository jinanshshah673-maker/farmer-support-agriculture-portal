from django.db import models
from django.contrib.auth.models import User


# ----------------------------
# Student Model (Legacy)
# ----------------------------

class Student(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField()
    course = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.name


# ----------------------------
# Government Schemes
# ----------------------------

class GovernmentScheme(models.Model):

    CATEGORY = [
        ("Central", "Central"),
        ("Gujarat", "Gujarat"),
    ]

    scheme_name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY,
        default="Central"
    )

    description = models.TextField(default="")
    benefits = models.TextField(default="")
    eligibility = models.TextField(default="")
    official_link = models.URLField(default="")

    def __str__(self):
        return self.scheme_name


# ----------------------------
# India Location Models
# ----------------------------

class State(models.Model):

    state_code = models.IntegerField(unique=True)

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class District(models.Model):

    district_code = models.IntegerField(unique=True)

    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="districts"
    )

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Taluka(models.Model):

    subdistrict_code = models.IntegerField(unique=True)

    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="talukas"
    )

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


# ----------------------------
# Farmer Model
# ----------------------------

class Farmer(models.Model):

    SOIL_CHOICES = [
        ("Black", "Black"),
        ("Red", "Red"),
        ("Alluvial", "Alluvial"),
        ("Clay", "Clay"),
        ("Sandy", "Sandy"),
        ("Loamy", "Loamy"),
    ]

    LANGUAGE_CHOICES = [
        ("English", "English"),
        ("Gujarati", "Gujarati"),
        ("Hindi", "Hindi"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="farmer_profile"
    )

    name = models.CharField(max_length=100)

    mobile = models.CharField(
        max_length=10,
        unique=True
    )

    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=128
    )

    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE
    )

    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE
    )

    taluka = models.ForeignKey(
        Taluka,
        on_delete=models.CASCADE
    )

    crop = models.CharField(max_length=100)

    land_area = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    soil_type = models.CharField(
        max_length=30,
        choices=SOIL_CHOICES
    )

    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default="English"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# ----------------------------
# Notification Model
# ----------------------------

class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ("sowing", "Crop Sowing"),
        ("irrigation", "Irrigation Reminder"),
        ("fertilizer", "Fertilizer Application"),
        ("crop_care", "General Crop Care"),
        ("harvesting", "Harvesting Reminder"),
        ("weather_alert", "Weather Alert"),
        ("government_scheme", "Government Scheme"),
        ("market_price", "Market Price"),
        ("crop_advisory", "Crop Advisory"),
        ("system", "System"),
    ]

    farmer = models.ForeignKey(
        Farmer,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default="crop_care"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_read = models.BooleanField(
        default=False
    )
    
    reference_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.farmer.name} - {self.title}"


# ----------------------------
# Mandi Price Model (Official OGD / Agmarknet)
# ----------------------------

class MandiPrice(models.Model):
    state = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=100, db_index=True)
    market = models.CharField(max_length=150, db_index=True)
    commodity = models.CharField(max_length=150, db_index=True)
    variety = models.CharField(max_length=100, blank=True, default="Other")
    grade = models.CharField(max_length=50, blank=True, default="FAQ")
    arrival_date = models.DateField(db_index=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    modal_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=50, default="₹/Quintal")
    source = models.CharField(max_length=150, default="data.gov.in / Agmarknet")
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-arrival_date", "market", "commodity"]
        indexes = [
            models.Index(fields=["state", "district"]),
            models.Index(fields=["commodity", "modal_price"]),
            models.Index(fields=["arrival_date", "market"]),
        ]
        unique_together = ["state", "district", "market", "commodity", "variety", "arrival_date"]

    def __str__(self):
        return f"{self.market} - {self.commodity} ({self.modal_price} {self.unit}) [{self.arrival_date}]"
