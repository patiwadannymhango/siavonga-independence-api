import uuid

from django.db import transaction

from .gateways.base import get_gateway
from .models import Payment


def create_payment(*, registration, payment_method):
    return Payment.objects.create(
        registration=registration,
        reference=f"PAY-{uuid.uuid4().hex[:16].upper()}",
        amount=registration.amount,
        currency=registration.currency,
        payment_method=payment_method,
        status=Payment.Status.CREATED,
    )


def initiate_mobile_payment(*, payment, phone_number, callback_url):
    gateway = get_gateway()

    result = gateway.create_mobile_collection(payment=payment, phone_number=phone_number, callback_url=callback_url)

    payment.billing_details = {**payment.billing_details, "phone_number": phone_number}
    payment.provider_reference = result.get("provider_reference", "")
    payment.provider_response = {**payment.provider_response, "initiate": result.get("raw", {})}
    payment.status = Payment.Status.PROCESSING
    payment.save(update_fields=["billing_details", "provider_reference", "provider_response", "status", "updated_at"])

    return payment


def initiate_card_payment(*, payment, participant, city, address, zip_code, country, callback_url, back_url):
    gateway = get_gateway()

    result = gateway.create_card_collection(
        payment=payment,
        participant=participant,
        city=city,
        address=address,
        zip_code=zip_code,
        country=country,
        back_url=back_url,
        callback_url=callback_url,
    )

    payment.billing_details = {
        **payment.billing_details,
        "city": city,
        "address": address,
        "zip_code": zip_code,
    }
    payment.provider_reference = result.get("provider_reference", "")
    payment.provider_response = {**payment.provider_response, "initiate": result.get("raw", {})}
    payment.status = Payment.Status.PROCESSING
    payment.save(update_fields=["billing_details", "provider_reference", "provider_response", "status", "updated_at"])

    return payment, result.get("redirect_url", "")


SUCCESS_STATES = {"SUCCESS", "SUCCESSFUL", "COMPLETED", "PAID"}
FAILED_STATES = {"FAILED", "FAILURE", "CANCELLED", "DECLINED"}


def apply_payment_outcome(*, payment, provider_status, raw_response=None, response_key="provider_check"):
    """
    Shared success/failure transition for a Payment, driven by whatever
    the gateway reports — used by both the webhook (push) and
    sync_payment_status (pull, called while the frontend is polling), so
    a missed or delayed webhook doesn't leave a payment stuck on
    PROCESSING forever even though the gateway already settled it.
    """

    if raw_response is not None:
        payment.provider_response = {**payment.provider_response, response_key: raw_response}
        payment.save(update_fields=["provider_response", "updated_at"])

    settled_states = (Payment.Status.SUCCESS, Payment.Status.FAILED, Payment.Status.REFUNDED, Payment.Status.CANCELLED)

    if payment.status in settled_states:
        # Already settled — never re-process. Guards against the webhook
        # and an active poll-time check both resolving around the same
        # moment.
        return payment

    provider_status = (provider_status or "").upper()

    if provider_status in SUCCESS_STATES:
        from django.utils import timezone

        from apps.registrations.models import Registration

        with transaction.atomic():
            payment.status = Payment.Status.SUCCESS
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at", "updated_at"])

            registration = payment.registration
            registration.status = Registration.Status.CONFIRMED
            registration.save(update_fields=["status", "updated_at"])

        from apps.notifications.services import notify_payment_confirmed

        notify_payment_confirmed(payment.registration)

    elif provider_status in FAILED_STATES:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])

        from apps.notifications.services import notify_payment_failed

        notify_payment_failed(payment.registration, reason=provider_status)

    # Anything else (still processing on the gateway's side) is left
    # exactly as-is: no status flip, no notification, until a definitive
    # outcome arrives.

    return payment


def sync_payment_status(payment):
    """
    Actively re-check a still-in-flight payment against the gateway
    instead of only waiting on its webhook. Called from the status-
    polling endpoint the frontend hits while showing the "waiting"
    screen. Safe to call on every poll: a no-op once settled, and any
    gateway failure here is swallowed so a flaky provider call never
    breaks the poll itself.
    """

    if payment.status != Payment.Status.PROCESSING:
        # CREATED means no collection exists yet to check (or this is a
        # bank transfer/cash payment, which never goes through a
        # gateway at all — those are reconciled manually). Anything else
        # is already settled.
        return payment

    gateway = get_gateway()

    try:
        response = gateway.get_collection_status(payment=payment)
    except Exception:  # noqa: BLE001 — a flaky status check must never break polling
        return payment

    return apply_payment_outcome(
        payment=payment,
        provider_status=response.get("status", ""),
        raw_response=response.get("raw", response),
        response_key="status_check",
    )
