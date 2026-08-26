from django.urls import path

from .views import (
    AdminVendorCategoryDetailView,
    AdminVendorCategoryListView,
    AdminVendorRegistrationCreateView,
    AdminVendorRegistrationDetailView,
    AdminVendorRegistrationExportView,
    AdminVendorRegistrationListView,
    PublicVendorCategoryListView,
    PublicVendorRegistrationCreateView,
    PublicVendorRegistrationLookupView,
)

urlpatterns = [
    # Public
    path("categories/", PublicVendorCategoryListView.as_view(), name="public-vendor-categories"),
    path("register/", PublicVendorRegistrationCreateView.as_view(), name="public-vendor-register"),
    path("lookup/", PublicVendorRegistrationLookupView.as_view(), name="public-vendor-lookup"),
    # Admin
    path("admin/categories/", AdminVendorCategoryListView.as_view(), name="admin-vendor-category-list"),
    path("admin/categories/<uuid:pk>/", AdminVendorCategoryDetailView.as_view(), name="admin-vendor-category-detail"),
    path("admin/registrations/", AdminVendorRegistrationListView.as_view(), name="admin-vendor-registration-list"),
    path(
        "admin/registrations/manual/",
        AdminVendorRegistrationCreateView.as_view(),
        name="admin-vendor-registration-create",
    ),
    path(
        "admin/registrations/export/",
        AdminVendorRegistrationExportView.as_view(),
        name="admin-vendor-registration-export",
    ),
    path(
        "admin/registrations/<uuid:pk>/",
        AdminVendorRegistrationDetailView.as_view(),
        name="admin-vendor-registration-detail",
    ),
]
