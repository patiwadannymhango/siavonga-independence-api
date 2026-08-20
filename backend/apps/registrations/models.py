from django.db import models

from apps.common.models import UUIDModel


class RaceCategory(UUIDModel):
    """
    A race distance/category a runner can enter — e.g. "10KM Competitive
    Run" or "5KM Fun Run & Walk". `code` is the stable identifier the
    frontend sends (matches its RaceCategory union type), `name` is what's
    displayed.
    """

    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    distance_label = models.CharField(max_length=50, blank=True, help_text="e.g. '10 KM'")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ZMW")
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "race categories"
        ordering = ["price"]

    def __str__(self):
        return self.name


class Participant(UUIDModel):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    class AgeRange(models.TextChoices):
        UNDER_18 = "Under 18", "Under 18"
        AGE_18_29 = "18-29", "18-29"
        AGE_30_39 = "30-39", "30-39"
        AGE_40_49 = "40-49", "40-49"
        AGE_50_59 = "50-59", "50-59"
        AGE_60_PLUS = "60+", "60+"

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    age_range = models.CharField(max_length=20, choices=AgeRange.choices, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.full_name


class Registration(UUIDModel):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "PENDING_PAYMENT", "Pending Payment"
        PAYMENT_PROCESSING = "PAYMENT_PROCESSING", "Payment Processing"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"
        REFUNDED = "REFUNDED", "Refunded"

    class TShirtSize(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"
        XXXL = "3XL", "3XL"
        XXXXL = "4XL", "4XL"
        XXXXXL = "5XL", "5XL"

    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="registrations")
    category = models.ForeignKey(RaceCategory, on_delete=models.PROTECT, related_name="registrations")

    registration_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING_PAYMENT)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ZMW")

    t_shirt_size = models.CharField(max_length=10, choices=TShirtSize.choices, blank=True)
    club_or_institution = models.CharField(max_length=200, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    medical_notes = models.TextField(blank=True)
    accepted_terms = models.BooleanField(default=False)

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-registered_at"]

    def __str__(self):
        return self.registration_number

    @property
    def full_name(self):
        return self.participant.full_name
