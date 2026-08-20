from django.contrib import admin

from .models import Participant, RaceCategory, Registration


@admin.register(RaceCategory)
class RaceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price", "currency", "capacity", "is_active")
    list_editable = ("price", "is_active")
    search_fields = ("name", "code")


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "gender", "age_range")
    search_fields = ("full_name", "email", "phone")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "participant",
        "category",
        "status",
        "amount",
        "currency",
        "registered_at",
    )
    list_filter = ("status", "category")
    search_fields = (
        "registration_number",
        "participant__full_name",
        "participant__email",
        "participant__phone",
    )
    autocomplete_fields = ("participant", "category")
    readonly_fields = ("registration_number", "registered_at", "updated_at")


admin.site.site_header = "Siavonga Independence Run 2026"
admin.site.site_title = "Siavonga Run Admin"
admin.site.index_title = "Event administration"
