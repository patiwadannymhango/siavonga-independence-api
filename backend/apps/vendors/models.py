from django.db import models

from apps.common.models import BaseRegistration, UUIDModel


class VendorCategory(UUIDModel):
    """
    A vendor/exhibitor package — e.g. "Vendor Stall", "Food & Beverage
    Stall", "Official Sponsor". Priced independently of race categories;
    a price of 0 means the category confirms immediately with no payment
    step (see services.create_vendor_registration).
    """

    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ZMW")
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "vendor categories"
        ordering = ["price"]

    def __str__(self):
        return self.name


class Vendor(UUIDModel):
    """The business registering for a stall/exhibition space — the
    vendor-side equivalent of registrations.Participant."""

    business_name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200, help_text="Contact person's name.")
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    business_location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.business_name


class VendorRegistration(BaseRegistration):
    class Requirement(models.TextChoices):
        EXHIBITION_SPACE = "Exhibition Space", "Exhibition Space"
        VENDOR_STALL = "Vendor Stall", "Vendor Stall"
        FOOD_BEVERAGE_STALL = "Food & Beverage Stall", "Food & Beverage Stall"
        CORPORATE_ACTIVATION = "Corporate Activation", "Corporate Activation"
        BRANDING_PROMOTIONAL_SPACE = "Branding / Promotional Space", "Branding / Promotional Space"
        OTHER = "Other", "Other"

    REFERENCE_PREFIX = "SIV"

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="registrations")
    category = models.ForeignKey(VendorCategory, on_delete=models.PROTECT, related_name="registrations")

    products_services = models.TextField(blank=True)
    requirement = models.CharField(max_length=40, choices=Requirement.choices, blank=True)

    class Meta:
        ordering = ["-registered_at"]

    @property
    def contact(self):
        """The person to reach for this registration — generic name used
        by payment code shared with Registration."""
        return self.vendor

    def notify_received(self):
        from apps.notifications.services import notify_vendor_registration_received

        notify_vendor_registration_received(self)

    def notify_confirmed(self):
        from apps.notifications.services import notify_vendor_payment_confirmed

        notify_vendor_payment_confirmed(self)

    def notify_failed(self, *, reason=""):
        from apps.notifications.services import notify_vendor_payment_failed

        notify_vendor_payment_failed(self, reason=reason)
