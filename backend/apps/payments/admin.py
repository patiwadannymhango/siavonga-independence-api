from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "registration",
        "vendor_registration",
        "amount",
        "currency",
        "status",
        "payment_method",
        "created_at",
    )
    list_filter = ("status", "payment_method")
    search_fields = (
        "reference",
        "provider_reference",
        "registration__registration_number",
        "vendor_registration__registration_number",
    )
    autocomplete_fields = ("registration", "vendor_registration")
    readonly_fields = ("reference", "provider_reference", "provider_response", "created_at", "updated_at")
