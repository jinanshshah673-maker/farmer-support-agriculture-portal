from django.contrib import admin
from .models import Student, GovernmentScheme, State, District, Taluka, Farmer, Notification, MandiPrice

admin.site.register(Student)
admin.site.register(GovernmentScheme)
admin.site.register(State)
admin.site.register(District)
admin.site.register(Taluka)
admin.site.register(Farmer)
admin.site.register(Notification)


@admin.register(MandiPrice)
class MandiPriceAdmin(admin.ModelAdmin):
    list_display = ("commodity", "market", "district", "modal_price", "min_price", "max_price", "arrival_date")
    list_filter = ("district", "arrival_date", "commodity")
    search_fields = ("commodity", "market", "district", "variety")
    date_hierarchy = "arrival_date"
    ordering = ("-arrival_date", "market", "commodity")