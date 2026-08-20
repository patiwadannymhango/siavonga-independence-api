from django.db import models

from apps.common.models import UUIDModel


class Notification(UUIDModel):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"

    class NotificationType(models.TextChoices):
        REGISTRATION_RECEIVED = "REGISTRATION_RECEIVED", "Registration Received"
        PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Payment Confirmed"
        PAYMENT_FAILED = "PAYMENT_FAILED", "Payment Failed"
        CUSTOM = "CUSTOM", "Custom"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    registration = models.ForeignKey(
        "registrations.Registration",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    channel = models.CharField(max_length=10, choices=Channel.choices)
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel} to {self.recipient} ({self.status})"
