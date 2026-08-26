from django.db import models

from apps.common.models import UUIDModel


class PaymentMethod(models.TextChoices):
    MTN_MONEY = "MTN_MONEY", "MTN Money"
    AIRTEL_MONEY = "AIRTEL_MONEY", "Airtel Money"
    ZAMTEL_KWACHA = "ZAMTEL_KWACHA", "Zamtel Kwacha"
    CARD = "CARD", "Card"
    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
    CASH = "CASH", "Cash"


class Payment(UUIDModel):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        PROCESSING = "PROCESSING", "Processing"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    # Exactly one of these two is set — see the constraint below. Two
    # nullable FKs rather than a GenericForeignKey: there are only ever
    # two kinds of payment target, so contenttypes machinery would be
    # more abstraction than the problem needs. `target` gives the
    # gateway/webhook/notification code a single thing to call
    # regardless of which one is set.
    registration = models.ForeignKey(
        "registrations.Registration", on_delete=models.PROTECT, related_name="payments", null=True, blank=True
    )
    vendor_registration = models.ForeignKey(
        "vendors.VendorRegistration", on_delete=models.PROTECT, related_name="payments", null=True, blank=True
    )

    reference = models.CharField(max_length=100, unique=True, db_index=True)
    provider_reference = models.CharField(max_length=255, blank=True, db_index=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ZMW")

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CREATED)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices)

    # Card billing / mobile money number entered at initiate time — kept
    # separate from provider_response so the "track your registration"
    # lookup can show it back without parsing a third-party payload shape.
    billing_details = models.JSONField(default=dict, blank=True)

    provider_response = models.JSONField(default=dict, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(registration__isnull=False, vendor_registration__isnull=True)
                    | models.Q(registration__isnull=True, vendor_registration__isnull=False)
                ),
                name="payment_exactly_one_target",
            )
        ]

    def __str__(self):
        return self.reference

    @property
    def target(self):
        """The Registration or VendorRegistration this payment is for."""
        return self.registration or self.vendor_registration
