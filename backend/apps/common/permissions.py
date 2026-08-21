from rest_framework.permissions import BasePermission

# Two admin roles, both signing in through the same JWT login — there is
# no separate "customer" account type on this backend (runners never
# authenticate). The role isn't a separate model field: ADMIN is simply
# is_superuser=True, VIEW is is_staff=True with is_superuser=False. See
# apps/accounts/serializers.py for where a role choice on user creation
# maps onto that pair of flags.


class IsStaffRole(BasePermission):
    """Either admin role (ADMIN or VIEW) — read access to admin endpoints."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAdminRole(BasePermission):
    """ADMIN only — required for anything that creates, changes, or deletes data."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
