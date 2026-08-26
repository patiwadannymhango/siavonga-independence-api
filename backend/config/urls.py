from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Not "admin/" — in the single-origin deployment that path would sit
    # next to a future React admin dashboard at /dashboard and read as
    # the same thing. This is Django's own built-in admin site.
    path("django-admin/", admin.site.urls),
    path("api/v1/health/", health, name="health"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.registrations.urls")),
    path("api/v1/vendors/", include("apps.vendors.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
]
