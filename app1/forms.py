from django import forms
from .models import Farmer, State, District, Taluka, Notification


class FarmerRegistrationForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Create strong password"
        })
    )

    state = forms.ModelChoiceField(
        queryset=State.objects.all().order_by("name"),
        empty_label="Select State",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "state"
        })
    )

    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        empty_label="Select District",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "district"
        })
    )

    taluka = forms.ModelChoiceField(
        queryset=Taluka.objects.none(),
        empty_label="Select Taluka",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "taluka"
        })
    )

    class Meta:
        model = Farmer
        fields = [
            "name",
            "mobile",
            "email",
            "password",
            "state",
            "district",
            "taluka",
            "crop",
            "land_area",
            "soil_type",
            "language",
        ]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Farmer Full Name"
            }),
            "mobile": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "10-digit Mobile Number",
                "maxlength": "10"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "farmer@example.com"
            }),
            "crop": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Primary Crop (e.g. Wheat, Cotton, Rice)"
            }),
            "land_area": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Land Area in Acres",
                "step": "0.1",
                "min": "0.1"
            }),
            "soil_type": forms.Select(attrs={
                "class": "form-select"
            }),
            "language": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate districts dynamically if state is submitted in POST data
        if "state" in self.data:
            try:
                state_id = int(self.data.get("state"))
                self.fields["district"].queryset = District.objects.filter(
                    state_id=state_id
                ).order_by("name")
            except (ValueError, TypeError):
                self.fields["district"].queryset = District.objects.none()
        elif self.instance.pk and self.instance.state_id:
            self.fields["district"].queryset = self.instance.state.districts.order_by("name")

        # Populate talukas dynamically if district is submitted in POST data
        if "district" in self.data:
            try:
                district_id = int(self.data.get("district"))
                self.fields["taluka"].queryset = Taluka.objects.filter(
                    district_id=district_id
                ).order_by("name")
            except (ValueError, TypeError):
                self.fields["taluka"].queryset = Taluka.objects.none()
        elif self.instance.pk and self.instance.district_id:
            self.fields["taluka"].queryset = self.instance.district.talukas.order_by("name")

    def clean_mobile(self):
        mobile = self.cleaned_data.get("mobile", "").strip()
        if not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit mobile number.")
        if Farmer.objects.filter(mobile=mobile).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists():
            raise forms.ValidationError("A farmer with this mobile number is already registered.")
        return mobile

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if Farmer.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists():
            raise forms.ValidationError("A farmer with this email is already registered.")
        return email

    def clean_land_area(self):
        land_area = self.cleaned_data.get("land_area")
        if land_area is not None and land_area <= 0:
            raise forms.ValidationError("Land area must be greater than 0.")
        return land_area


class FarmingReminderForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ["title", "message", "notification_type"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., Sowing Window / First Irrigation"
            }),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter reminder details..."
            }),
            "notification_type": forms.Select(attrs={
                "class": "form-select"
            }),
        }