from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


def _role_for(user):
    """Read-only "ADMIN" | "VIEW" derived from is_superuser — see apps/common/permissions.py."""
    return User.Role.ADMIN if user.is_superuser else User.Role.VIEW


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        return _role_for(obj)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
            "is_superuser",
            "is_staff",
        )


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        return token


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = RefreshToken(attrs["refresh"])
        return attrs

    def save(self, **kwargs):
        self.token.blacklist()


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone")


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        return _role_for(obj)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "is_active",
            "role",
            "is_superuser",
            "is_staff",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    # Required, not defaulted — every account must be explicitly given
    # one role or the other at creation time.
    role = serializers.ChoiceField(choices=User.Role.choices, write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "role",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role")
        return User.objects.create_user(
            password=password,
            # Every admin account created here is staff by definition —
            # there's no separate "customer" account type on this backend.
            is_staff=True,
            is_superuser=(role == User.Role.ADMIN),
            **validated_data,
        )


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    # Optional on update (partial=True) — omit to leave the role
    # unchanged.
    role = serializers.ChoiceField(choices=User.Role.choices, write_only=True, required=False)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "is_active", "role")

    def update(self, instance, validated_data):
        role = validated_data.pop("role", None)
        if role is not None:
            instance.is_superuser = role == User.Role.ADMIN
        return super().update(instance, validated_data)
