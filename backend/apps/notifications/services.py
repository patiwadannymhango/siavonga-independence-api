"""
High-level "tell the runner what just happened" functions — the rest of
the codebase (registration/payment services, webhooks, admin actions)
calls these; they compose the message and fire email + SMS where
appropriate.

Only one email goes out for the whole registration lifecycle: the
"registration confirmed" email in notify_payment_confirmed(), sent once
the registration actually succeeds (payment settles, or an admin marks it
CONFIRMED). notify_registration_received/notify_payment_failed
intentionally send SMS only — no "registration received" email while
payment is still pending, and no failure email — so a runner never
receives more than one email out of this flow.
"""

from django.conf import settings
from django.template.loader import render_to_string

from .email import send_email
from .models import Notification
from .sms import send_sms


def _participant_contact(registration):
    participant = registration.participant
    return participant.email, participant.phone


def notify_registration_received(registration):
    _, phone = _participant_contact(registration)
    participant = registration.participant

    text = (
        f"Hi {participant.full_name},\n\n"
        f"We've received your registration for {settings.EVENT_NAME}.\n"
        f"Reference: {registration.registration_number}\n"
        f"Category: {registration.category.name}\n"
        f"Amount due: {registration.currency} {registration.amount}\n\n"
        "Complete payment to confirm your place.\n"
    )

    if phone:
        send_sms(
            to=phone,
            message=text,
            registration=registration,
            notification_type=Notification.NotificationType.REGISTRATION_RECEIVED,
        )


def notify_payment_confirmed(registration):
    """The one email a runner gets: sent once the registration actually
    succeeds — a real payment settling, or an admin marking it CONFIRMED."""

    email, phone = _participant_contact(registration)
    participant = registration.participant

    subject = f"You're confirmed — {registration.registration_number}"
    text = (
        f"Hi {participant.full_name},\n\n"
        f"Your entry for {settings.EVENT_NAME} is confirmed and paid. This "
        "email is your proof of registration — keep it handy for race "
        "pack collection.\n\n"
        f"Reference: {registration.registration_number}\n"
        f"Race category: {registration.category.name}\n"
        f"Amount paid: {registration.currency} {registration.amount}\n"
        f"Event date: {settings.EVENT_DATE}\n"
        f"Venue: {settings.EVENT_LOCATION}\n\n"
        "On race day, bring a valid ID and this reference number to "
        "collect your race pack.\n\n"
        "See you at the start line.\n"
    )

    track_url = f"{settings.PUBLIC_SITE_URL}/#track" if settings.PUBLIC_SITE_URL else "#"

    html = render_to_string(
        "notifications/emails/registration_confirmed.html",
        {
            "first_name": participant.full_name.split(" ")[0] if participant.full_name else "",
            "event_name": settings.EVENT_NAME,
            "reference": registration.registration_number,
            "category_name": registration.category.name,
            "currency": registration.currency,
            "amount": registration.amount,
            "event_date": settings.EVENT_DATE,
            "event_location": settings.EVENT_LOCATION,
            "track_url": track_url,
            "contact_email": settings.EVENT_CONTACT_EMAIL or settings.DEFAULT_FROM_EMAIL,
            "contact_phone": settings.EVENT_CONTACT_PHONE,
        },
    )

    if email:
        send_email(
            to=email,
            subject=subject,
            text_body=text,
            html_body=html,
            registration=registration,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
        )

    if phone:
        send_sms(
            to=phone,
            message=text,
            registration=registration,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
        )


def notify_payment_failed(registration, *, reason=""):
    _, phone = _participant_contact(registration)
    participant = registration.participant

    text = (
        f"Hi {participant.full_name},\n\n"
        f"We couldn't confirm your payment for {settings.EVENT_NAME}"
        f"{f' ({reason})' if reason else ''}.\n"
        f"Reference: {registration.registration_number}\n\n"
        "Please try again, or contact us for help.\n"
    )

    if phone:
        send_sms(
            to=phone,
            message=text,
            registration=registration,
            notification_type=Notification.NotificationType.PAYMENT_FAILED,
        )
