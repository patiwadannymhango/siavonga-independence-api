"""
Pluggable SMS sending. No SMS provider credentials have been configured
yet, so this defaults to a "console" backend that just logs the message
via the Notification model (status=SENT, provider_response={"backend":
"console"}) without actually dispatching anything — the rest of the
notification pipeline works end-to-end today, and switching to a real
provider is a single settings change.

To go live with real SMS:
  1. Create an account with an SMS provider (Africa's Talking is the
     common choice for Zambia).
  2. Set AFRICASTALKING_USERNAME / AFRICASTALKING_API_KEY in .env.
  3. Set SMS_BACKEND=africastalking in .env.
  4. `pip install africastalking` and uncomment the implementation below.
"""

from django.utils import timezone

from .models import Notification


def _send_console(*, to, message):
    print(f"[SMS -> {to}] {message}")  # noqa: T201 — intentional dev stand-in
    return {"backend": "console"}


def _send_africastalking(*, to, message):
    # TODO(sms): install `africastalking` and uncomment once credentials
    # are configured. Left commented out (rather than raising) so the
    # console backend keeps working if this function is ever selected
    # before credentials are ready.
    #
    # import africastalking
    # africastalking.initialize(
    #     settings.AFRICASTALKING_USERNAME,
    #     settings.AFRICASTALKING_API_KEY,
    # )
    # sms = africastalking.SMS
    # response = sms.send(message, [to], sender_id=settings.SMS_SENDER_ID)
    # return response
    raise NotImplementedError(
        "Africa's Talking credentials are not configured yet. "
        "Set AFRICASTALKING_USERNAME / AFRICASTALKING_API_KEY and "
        "uncomment the implementation in apps/notifications/sms.py."
    )


BACKENDS = {
    "console": _send_console,
    "africastalking": _send_africastalking,
}


def send_sms(*, to, message, target=None, notification_type=Notification.NotificationType.CUSTOM):
    from django.conf import settings

    from apps.registrations.models import Registration
    from apps.vendors.models import VendorRegistration

    notification = Notification.objects.create(
        registration=target if isinstance(target, Registration) else None,
        vendor_registration=target if isinstance(target, VendorRegistration) else None,
        channel=Notification.Channel.SMS,
        notification_type=notification_type,
        recipient=to,
        body=message,
        status=Notification.Status.PENDING,
    )

    backend = BACKENDS.get(settings.SMS_BACKEND, _send_console)

    try:
        response = backend(to=to, message=message)

        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.provider_response = response if isinstance(response, dict) else {"raw": str(response)}
        notification.save(update_fields=["status", "sent_at", "provider_response", "updated_at"])

    except Exception as exc:  # noqa: BLE001
        notification.status = Notification.Status.FAILED
        notification.error_message = str(exc)
        notification.save(update_fields=["status", "error_message", "updated_at"])

    return notification
