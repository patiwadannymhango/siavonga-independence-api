"""
Email sending, using Django's built-in SMTP backend configured in
settings (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD — a Gmail App Password
works well). In development EMAIL_BACKEND defaults to the console
backend, so emails just print instead of needing real credentials.

Every send is logged to the Notification model regardless of success or
failure, so delivery status per registration is visible in the admin.
"""

from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .models import Notification


def send_email(*, to, subject, text_body, html_body=None, registration=None, notification_type=Notification.NotificationType.CUSTOM):
    notification = Notification.objects.create(
        registration=registration,
        channel=Notification.Channel.EMAIL,
        notification_type=notification_type,
        recipient=to,
        subject=subject,
        body=text_body,
        status=Notification.Status.PENDING,
    )

    try:
        message = EmailMultiAlternatives(subject=subject, body=text_body, to=[to])

        if html_body:
            message.attach_alternative(html_body, "text/html")

        message.send(fail_silently=False)

        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "updated_at"])

    except Exception as exc:  # noqa: BLE001 — log any failure rather than crash the caller
        notification.status = Notification.Status.FAILED
        notification.error_message = str(exc)
        notification.save(update_fields=["status", "error_message", "updated_at"])

    return notification
