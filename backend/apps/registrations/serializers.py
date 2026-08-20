from rest_framework import serializers

from .models import Participant, RaceCategory, Registration

# ---------------------------------------------------------------------------
# Public-facing
# ---------------------------------------------------------------------------


class RaceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RaceCategory
        fields = (
            "id",
            "name",
            "code",
            "description",
            "distance_label",
            "price",
            "currency",
            "capacity",
        )


def _map_status_for_frontend(registration):
    """
    The frontend's RegistrationStatus union is a small display-oriented
    set ('confirmed' | 'pending-bank-transfer' | 'processing' | 'failed'),
    narrower than the backend's full Registration.Status lifecycle — map
    down to it here rather than pushing that translation onto the client.
    """

    if registration.status == Registration.Status.CONFIRMED:
        return "confirmed"

    if registration.status in (Registration.Status.CANCELLED, Registration.Status.EXPIRED, Registration.Status.REFUNDED):
        return "failed"

    latest_payment = registration.payments.order_by("-created_at").first()
    if latest_payment and latest_payment.payment_method == "BANK_TRANSFER":
        return "pending-bank-transfer"

    return "processing"


class RegistrationDetailsSerializer(serializers.Serializer):
    """Mirrors the frontend's RegistrationDetails shape exactly."""

    fullName = serializers.CharField(source="participant.full_name")
    email = serializers.EmailField(source="participant.email")
    phone = serializers.CharField(source="participant.phone")
    gender = serializers.CharField(source="participant.gender")
    ageRange = serializers.CharField(source="participant.age_range")
    country = serializers.CharField(source="participant.country")
    tShirtSize = serializers.CharField(source="t_shirt_size")
    raceCategory = serializers.CharField(source="category.code")
    clubOrInstitution = serializers.CharField(source="club_or_institution")
    emergencyContactName = serializers.CharField(source="emergency_contact_name")
    emergencyContactPhone = serializers.CharField(source="emergency_contact_phone")
    medicalNotes = serializers.CharField(source="medical_notes")
    acceptedTerms = serializers.BooleanField(source="accepted_terms")


class PaymentInfoSerializer(serializers.Serializer):
    method = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    phoneNumber = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    zipCode = serializers.SerializerMethodField()

    def _latest(self, registration):
        return registration.payments.order_by("-created_at").first()

    def get_method(self, registration):
        payment = self._latest(registration)
        if not payment:
            return ""
        return "card" if payment.payment_method == "CARD" else "mobile-money"

    def get_provider(self, registration):
        payment = self._latest(registration)
        return payment.payment_method if payment and payment.payment_method != "CARD" else ""

    def get_phoneNumber(self, registration):
        payment = self._latest(registration)
        return (payment.billing_details or {}).get("phone_number", "") if payment else ""

    def get_city(self, registration):
        payment = self._latest(registration)
        return (payment.billing_details or {}).get("city", "") if payment else ""

    def get_address(self, registration):
        payment = self._latest(registration)
        return (payment.billing_details or {}).get("address", "") if payment else ""

    def get_zipCode(self, registration):
        payment = self._latest(registration)
        return (payment.billing_details or {}).get("zip_code", "") if payment else ""


class RegistrationRecordSerializer(serializers.Serializer):
    """Mirrors the frontend's RegistrationRecord shape exactly."""

    reference = serializers.CharField(source="registration_number")
    details = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    submittedAt = serializers.DateTimeField(source="registered_at")
    # coerce_to_string=False: a JSON number, not a decimal string — the
    # frontend calls .toFixed() on this directly (see receipt.ts).
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    currency = serializers.CharField()

    def get_details(self, registration):
        return RegistrationDetailsSerializer(registration).data

    def get_payment(self, registration):
        return PaymentInfoSerializer(registration).data

    def get_status(self, registration):
        return _map_status_for_frontend(registration)


class PublicRegistrationCreateSerializer(serializers.Serializer):
    """
    Accepts exactly the frontend's RegistrationDetails payload shape
    (camelCase field names) so no translation layer sits between this
    API and the site's registration form.
    """

    fullName = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30)
    gender = serializers.ChoiceField(choices=Participant.Gender.choices, required=False, allow_blank=True)
    ageRange = serializers.ChoiceField(choices=Participant.AgeRange.choices, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tShirtSize = serializers.ChoiceField(
        choices=Registration.TShirtSize.choices, required=False, allow_blank=True
    )
    raceCategory = serializers.CharField()
    clubOrInstitution = serializers.CharField(max_length=200, required=False, allow_blank=True)
    emergencyContactName = serializers.CharField(max_length=200, required=False, allow_blank=True)
    emergencyContactPhone = serializers.CharField(max_length=30)
    medicalNotes = serializers.CharField(required=False, allow_blank=True)
    acceptedTerms = serializers.BooleanField()

    def validate_acceptedTerms(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms and conditions.")
        return value

    def validate_raceCategory(self, value):
        try:
            return RaceCategory.objects.get(code=value, is_active=True)
        except RaceCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid race category.")

    def validate(self, attrs):
        category = attrs["raceCategory"]

        if category.capacity is not None:
            current_count = Registration.objects.filter(
                category=category,
                status__in=[
                    Registration.Status.PENDING_PAYMENT,
                    Registration.Status.PAYMENT_PROCESSING,
                    Registration.Status.CONFIRMED,
                ],
            ).count()

            if current_count >= category.capacity:
                raise serializers.ValidationError({"raceCategory": "This race category has reached capacity."})

        return attrs

    def to_registration_kwargs(self):
        data = self.validated_data
        return {
            "category": data["raceCategory"],
            "participant_data": {
                "full_name": data["fullName"],
                "email": data["email"],
                "phone": data["phone"],
                "gender": data.get("gender", ""),
                "age_range": data.get("ageRange", ""),
                "country": data.get("country", ""),
            },
            "details": {
                "t_shirt_size": data.get("tShirtSize", ""),
                "club_or_institution": data.get("clubOrInstitution", ""),
                "emergency_contact_name": data.get("emergencyContactName", ""),
                "emergency_contact_phone": data["emergencyContactPhone"],
                "medical_notes": data.get("medicalNotes", ""),
                "accepted_terms": data["acceptedTerms"],
            },
        }


# ---------------------------------------------------------------------------
# Admin-facing
# ---------------------------------------------------------------------------


class AdminParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ("id", "full_name", "email", "phone", "gender", "age_range", "country")


class AdminRegistrationSerializer(serializers.ModelSerializer):
    participant = AdminParticipantSerializer(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Registration
        fields = (
            "id",
            "registration_number",
            "status",
            "amount",
            "currency",
            "participant",
            "category",
            "category_name",
            "t_shirt_size",
            "club_or_institution",
            "emergency_contact_name",
            "emergency_contact_phone",
            "medical_notes",
            "registered_at",
            "updated_at",
        )


class AdminRegistrationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Registration.Status.choices)


class AdminManualRegistrationSerializer(serializers.Serializer):
    """
    For the admin's "register a participant" flow — walk-ins, phone
    registrations, etc. Defaults to CONFIRMED (cash taken in person).
    """

    category_id = serializers.UUIDField()
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    gender = serializers.ChoiceField(choices=Participant.Gender.choices, required=False, allow_blank=True)
    age_range = serializers.ChoiceField(choices=Participant.AgeRange.choices, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    t_shirt_size = serializers.ChoiceField(
        choices=Registration.TShirtSize.choices, required=False, allow_blank=True
    )
    club_or_institution = serializers.CharField(max_length=200, required=False, allow_blank=True)
    emergency_contact_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    emergency_contact_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    medical_notes = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Registration.Status.choices, default=Registration.Status.CONFIRMED)

    def validate_category_id(self, value):
        try:
            return RaceCategory.objects.get(id=value, is_active=True)
        except RaceCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid race category.")

    def to_registration_kwargs(self):
        data = self.validated_data
        return {
            "category": data["category_id"],
            "participant_data": {
                "full_name": data["full_name"],
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "gender": data.get("gender", ""),
                "age_range": data.get("age_range", ""),
                "country": data.get("country", ""),
            },
            "details": {
                "t_shirt_size": data.get("t_shirt_size", ""),
                "club_or_institution": data.get("club_or_institution", ""),
                "emergency_contact_name": data.get("emergency_contact_name", ""),
                "emergency_contact_phone": data.get("emergency_contact_phone", ""),
                "medical_notes": data.get("medical_notes", ""),
                "accepted_terms": True,
            },
            "status": data["status"],
        }
