from django.urls import path

from .views import (
    AdminPaymentListView,
    InitiatePaymentView,
    LipilaWebhookView,
    PublicBankDetailsView,
    PublicPaymentStatusView,
)

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="initiate-payment"),
    path("bank-details/", PublicBankDetailsView.as_view(), name="public-bank-details"),
    path("<uuid:payment_id>/status/", PublicPaymentStatusView.as_view(), name="public-payment-status"),
    path("webhooks/lipila/", LipilaWebhookView.as_view(), name="lipila-webhook"),
    path("admin/payments/", AdminPaymentListView.as_view(), name="admin-payment-list"),
]
