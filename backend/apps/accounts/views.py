from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import IsAdminRole, IsStaffRole

from .models import User
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_205_RESET_CONTENT,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated."})


# ---------------------------------------------------------------------------
# Admin-facing views — user management. Both roles (ADMIN and VIEW) can
# see the account list; only ADMIN can create, edit, or deactivate one —
# a VIEW account granting itself or anyone else ADMIN would defeat the
# whole point of a read-only role. There is no self-registration or
# invite flow; the very first account is made with
# `python manage.py createsuperuser`.
# ---------------------------------------------------------------------------


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStaffRole]
    serializer_class = AdminUserSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email"]
    queryset = User.objects.all().order_by("-created_at")


class AdminUserCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    """
    GET    /api/v1/auth/admin/users/<user_id>/ — either role
    PATCH   /api/v1/auth/admin/users/<user_id>/ — ADMIN only
    DELETE /api/v1/auth/admin/users/<user_id>/ — ADMIN only, deactivates
    (is_active=False) rather than hard-deleting.
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsStaffRole()]
        return [IsAuthenticated(), IsAdminRole()]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        return Response(AdminUserSerializer(user).data)

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminUserSerializer(user).data)

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
