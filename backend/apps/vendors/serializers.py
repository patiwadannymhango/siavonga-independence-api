from rest_framework import serializers

from .models import Vendor, VendorCategory, VendorRegistration

# ---------------------------------------------------------------------------
# Public-facing
# ---------------------------------------------------------------------------


class VendorCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorCategory
        fields = ("id", "name", "code", "description", "price", "currency", "capacity")


def _map_status_for_frontend(vendor_registration):
    """Mirrors apps.registrations.serializers._map_status_for_frontend —
    same display-oriented status set, same backend lifecycle."""

    if vendor_registration.status == VendorRegistration.Status.CONFIRMED:
        return "confirmed"

    if vendor_registration.status in (
        VendorRegistration.Status.CANCELLED,
        VendorRegistration.Status.EXPIRED,
        VendorRegistration.Status.REFUNDED,
    ):
        return "failed"

    latest_payment = vendor_registration.payments.order_by("-created_at").first()
    if latest_payment and latest_payment.payment_method == "BANK_TRANSFER":
        return "pending-bank-transfer"

    return "processing"


class VendorDetailsSerializer(serializers.Serializer):
    businessName = serializers.CharField(source="vendor.business_name")
    contactPerson = serializers.CharField(source="vendor.full_name")
    email = serializers.EmailField(source="vendor.email")
    phone = serializers.CharField(source="vendor.phone")
    businessLocation = serializers.CharField(source="vendor.business_location")
    productsServices = serializers.CharField(source="products_services")
    category = serializers.CharField(source="category.code")
    requirement = serializers.CharField()


class VendorPaymentInfoSerializer(serializers.Serializer):
    method = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    phoneNumber = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    zipCode = serializers.SerializerMethodField()

    def _latest(self, vendor_registration):
        return vendor_registration.payments.order_by("-created_at").first()

    def get_method(self, vendor_registration):
        payment = self._latest(vendor_registration)
        if not payment:
            return ""
        return "card" if payment.payment_method == "CARD" else "mobile-money"

    def get_provider(self, vendor_registration):
        payment = self._latest(vendor_registration)
        return payment.payment_method if payment and payment.payment_method != "CARD" else ""

    def get_phoneNumber(self, vendor_registration):
        payment = self._latest(vendor_registration)
        return (payment.billing_details or {}).get("phone_number", "") if payment else ""

    def get_city(self, vendor_registration):
        payment = self._latest(vendor_registration)
        return (payment.billing_details or {}).get("city", "") if payment else ""

    def get_address(self, vendor_registration):
        payment = self._latest(vendor_registration)
        return (payment.billing_details or {}).get("address", "") if payment else ""

    def get_zipCode(self, vendor_registration):
        payment = self._latest(vendor_registration)
        return (payment.billing_details or {}).get("zip_code", "") if payment else ""


class VendorRegistrationRecordSerializer(serializers.Serializer):
    """Mirrors apps.registrations.serializers.RegistrationRecordSerializer."""

    reference = serializers.CharField(source="registration_number")
    details = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    submittedAt = serializers.DateTimeField(source="registered_at")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    currency = serializers.CharField()

    def get_details(self, vendor_registration):
        return VendorDetailsSerializer(vendor_registration).data

    def get_payment(self, vendor_registration):
        return VendorPaymentInfoSerializer(vendor_registration).data

    def get_status(self, vendor_registration):
        return _map_status_for_frontend(vendor_registration)


class PublicVendorRegistrationCreateSerializer(serializers.Serializer):
    businessName = serializers.CharField(max_length=200)
    contactPerson = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    businessLocation = serializers.CharField(max_length=255, required=False, allow_blank=True)
    productsServices = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField()
    requirement = serializers.ChoiceField(choices=VendorRegistration.Requirement.choices)

    def validate_category(self, value):
        try:
            return VendorCategory.objects.get(code=value, is_active=True)
        except VendorCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid vendor category.")

    def validate(self, attrs):
        category = attrs["category"]

        if category.capacity is not None:
            current_count = VendorRegistration.objects.filter(
                category=category,
                status__in=[
                    VendorRegistration.Status.PENDING_PAYMENT,
                    VendorRegistration.Status.PAYMENT_PROCESSING,
                    VendorRegistration.Status.CONFIRMED,
                ],
            ).count()

            if current_count >= category.capacity:
                raise serializers.ValidationError({"category": "This vendor category has reached capacity."})

        return attrs

    def to_registration_kwargs(self):
        data = self.validated_data
        return {
            "category": data["category"],
            "vendor_data": {
                "business_name": data["businessName"],
                "full_name": data["contactPerson"],
                "email": data["email"],
                "phone": data["phone"],
                "business_location": data.get("businessLocation", ""),
            },
            "details": {
                "products_services": data.get("productsServices", ""),
                "requirement": data["requirement"],
            },
        }


# ---------------------------------------------------------------------------
# Admin-facing
# ---------------------------------------------------------------------------


class AdminVendorCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorCategory
        fields = ("id", "name", "code", "description", "price", "currency", "capacity", "is_active")


class AdminVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ("id", "business_name", "full_name", "email", "phone", "business_location")


class AdminVendorRegistrationSerializer(serializers.ModelSerializer):
    vendor = AdminVendorSerializer(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = VendorRegistration
        fields = (
            "id",
            "registration_number",
            "status",
            "amount",
            "currency",
            "vendor",
            "category",
            "category_name",
            "products_services",
            "requirement",
            "registered_at",
            "updated_at",
        )


class AdminVendorRegistrationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=VendorRegistration.Status.choices)


class AdminManualVendorRegistrationSerializer(serializers.Serializer):
    """For the admin's "register a vendor" flow — walk-ins, phone
    sign-ups, etc. Defaults to CONFIRMED (payment taken in person)."""

    category_id = serializers.UUIDField()
    business_name = serializers.CharField(max_length=200)
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    business_location = serializers.CharField(max_length=255, required=False, allow_blank=True)
    products_services = serializers.CharField(required=False, allow_blank=True)
    requirement = serializers.ChoiceField(
        choices=VendorRegistration.Requirement.choices, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=VendorRegistration.Status.choices, default=VendorRegistration.Status.CONFIRMED
    )

    def validate_category_id(self, value):
        try:
            return VendorCategory.objects.get(id=value, is_active=True)
        except VendorCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid vendor category.")

    def to_registration_kwargs(self):
        data = self.validated_data
        return {
            "category": data["category_id"],
            "vendor_data": {
                "business_name": data["business_name"],
                "full_name": data["full_name"],
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "business_location": data.get("business_location", ""),
            },
            "details": {
                "products_services": data.get("products_services", ""),
                "requirement": data.get("requirement", ""),
            },
            "status": data["status"],
        }
