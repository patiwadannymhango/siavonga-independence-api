from django.contrib import admin

from .models import Vendor, VendorCategory, VendorRegistration


@admin.register(VendorCategory)
class VendorCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price", "currency", "capacity", "is_active")
    list_editable = ("price", "is_active")
    search_fields = ("name", "code")


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("business_name", "full_name", "email", "phone", "business_location")
    search_fields = ("business_name", "full_name", "email", "phone")


@admin.register(VendorRegistration)
class VendorRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "vendor",
        "category",
        "status",
        "amount",
        "currency",
        "registered_at",
    )
    list_filter = ("status", "category")
    search_fields = (
        "registration_number",
        "vendor__business_name",
        "vendor__full_name",
        "vendor__email",
        "vendor__phone",
    )
    autocomplete_fields = ("vendor", "category")
    readonly_fields = ("registration_number", "registered_at", "updated_at")
