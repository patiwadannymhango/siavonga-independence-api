from django.urls import path

from .views import (
    AdminDashboardView,
    AdminRaceCategoryDetailView,
    AdminRaceCategoryListView,
    AdminRegistrationBulkUploadView,
    AdminRegistrationCreateView,
    AdminRegistrationDetailView,
    AdminRegistrationExportView,
    AdminRegistrationListView,
    PublicRaceCategoryListView,
    PublicRegistrationCreateView,
    PublicRegistrationLookupView,
)

urlpatterns = [
    # Public
    path("categories/", PublicRaceCategoryListView.as_view(), name="public-race-categories"),
    path("registrations/", PublicRegistrationCreateView.as_view(), name="public-registration-create"),
    path("registrations/lookup/", PublicRegistrationLookupView.as_view(), name="public-registration-lookup"),
    # Admin
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/categories/", AdminRaceCategoryListView.as_view(), name="admin-category-list"),
    path("admin/categories/<uuid:pk>/", AdminRaceCategoryDetailView.as_view(), name="admin-category-detail"),
    path("admin/registrations/", AdminRegistrationListView.as_view(), name="admin-registration-list"),
    path("admin/registrations/manual/", AdminRegistrationCreateView.as_view(), name="admin-registration-create"),
    path(
        "admin/registrations/bulk-upload/",
        AdminRegistrationBulkUploadView.as_view(),
        name="admin-registration-bulk-upload",
    ),
    path("admin/registrations/export/", AdminRegistrationExportView.as_view(), name="admin-registration-export"),
    path("admin/registrations/<uuid:pk>/", AdminRegistrationDetailView.as_view(), name="admin-registration-detail"),
]
