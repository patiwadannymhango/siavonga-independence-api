from rest_framework import serializers

from .models import Payment, PaymentMethod


class InitiatePaymentSerializer(serializers.Serializer):
    """Mirrors the frontend's InitiatePaymentParams shape exactly."""

    registrationId = serializers.UUIDField()
    paymentMethod = serializers.ChoiceField(choices=PaymentMethod.choices)

    phoneNumber = serializers.CharField(required=False, allow_blank=True)

    # Card only
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    zipCode = serializers.CharField(required=False, allow_blank=True, max_length=20)
    backUrl = serializers.URLField(required=False, allow_blank=True)

    # Bank transfer only
    payerName = serializers.CharField(required=False, allow_blank=True, max_length=150)
    transferReference = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate(self, attrs):
        method = attrs["paymentMethod"]

        if method in (PaymentMethod.MTN_MONEY, PaymentMethod.AIRTEL_MONEY, PaymentMethod.ZAMTEL_KWACHA):
            if not attrs.get("phoneNumber"):
                raise serializers.ValidationError(
                    {"phoneNumber": "Phone number is required for mobile money payments."}
                )

        if method == PaymentMethod.CARD:
            missing = {
                field: "This field is required for card payments."
                for field in ("city", "address", "zipCode")
                if not attrs.get(field)
            }
            if missing:
                raise serializers.ValidationError(missing)

        if method == PaymentMethod.BANK_TRANSFER and not attrs.get("payerName"):
            raise serializers.ValidationError(
                {"payerName": "Please provide the name the transfer will be made from."}
            )

        return attrs


class AdminPaymentSerializer(serializers.ModelSerializer):
    """Covers payments for either a runner or a vendor registration —
    see Payment.target."""

    target_type = serializers.SerializerMethodField()
    registration_number = serializers.CharField(source="target.registration_number", read_only=True)
    participant_name = serializers.CharField(source="target.contact.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "registration",
            "vendor_registration",
            "target_type",
            "registration_number",
            "participant_name",
            "reference",
            "provider_reference",
            "amount",
            "currency",
            "status",
            "payment_method",
            "paid_at",
            "created_at",
        )

    def get_target_type(self, obj):
        return "vendor" if obj.vendor_registration_id else "runner"
