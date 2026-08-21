from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.common.models import UUIDModel

from .managers import UserManager


class User(UUIDModel, AbstractBaseUser, PermissionsMixin):
    """
    Admin/organiser account. There is no self-registration — only an
    existing ADMIN can create accounts (see AdminUserCreateView).
    Runners never authenticate; the public registration/payment/lookup
    endpoints are AllowAny.
    """

    class Role(models.TextChoices):
        """
        Not a model field — is_superuser (ADMIN) / is_staff-only (VIEW)
        already captures the two states, so this just names them
        consistently everywhere instead of re-deriving "ADMIN"/"VIEW"
        strings by hand. See apps/common/permissions.py.
        """

        ADMIN = "ADMIN", "Admin"
        VIEW = "VIEW", "View only"

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
