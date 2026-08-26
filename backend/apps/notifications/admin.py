from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "channel", "notification_type", "status", "created_at")
    list_filter = ("channel", "notification_type", "status")
    search_fields = ("recipient", "registration__registration_number", "vendor_registration__registration_number")
    readonly_fields = (
        "registration",
        "vendor_registration",
        "channel",
        "notification_type",
        "recipient",
        "subject",
        "body",
        "status",
        "error_message",
        "provider_response",
        "sent_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
