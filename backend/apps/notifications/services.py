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

    # No reference number yet — one is only assigned once the
    # registration is confirmed (see Registration.save()), so there's
    # nothing to quote here. The runner can still be found by email if
    # they need to look this up before then.
    text = (
        f"Hi {participant.full_name},\n\n"
        f"We've received your registration for {settings.EVENT_NAME}.\n"
        f"Category: {registration.category.name}\n"
        f"Amount due: {registration.currency} {registration.amount}\n\n"
        "Complete payment to confirm your place and receive your registration reference.\n"
    )

    if phone:
        send_sms(
            to=phone,
            message=text,
            target=registration,
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
            target=registration,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
        )

    if phone:
        send_sms(
            to=phone,
            message=text,
            target=registration,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
        )


def notify_payment_failed(registration, *, reason=""):
    _, phone = _participant_contact(registration)
    participant = registration.participant

    # A failed payment never reached CONFIRMED, so there's no reference
    # number to quote (see Registration.save()).
    text = (
        f"Hi {participant.full_name},\n\n"
        f"We couldn't confirm your payment for {settings.EVENT_NAME}"
        f"{f' ({reason})' if reason else ''}.\n\n"
        "Please try again, or contact us for help.\n"
    )

    if phone:
        send_sms(
            to=phone,
            message=text,
            target=registration,
            notification_type=Notification.NotificationType.PAYMENT_FAILED,
        )


# ---------------------------------------------------------------------------
# Vendor registrations — same lifecycle/notification shape as runners
# (see module docstring), different wording since there's no race
# category, t-shirt size, or bib collection involved.
# ---------------------------------------------------------------------------


def notify_vendor_registration_received(vendor_registration):
    vendor = vendor_registration.vendor

    # No reference number yet for a paid category — see
    # BaseRegistration.save(). A free category is confirmed immediately
    # by services.create_vendor_registration, so this and
    # notify_vendor_payment_confirmed both fire in that case.
    text = (
        f"Hi {vendor.full_name},\n\n"
        f"We've received {vendor.business_name}'s registration for {settings.EVENT_NAME}.\n"
        f"Category: {vendor_registration.category.name}\n"
        f"Amount due: {vendor_registration.currency} {vendor_registration.amount}\n\n"
        "Complete payment to confirm your spot and receive your registration reference.\n"
    )

    if vendor.phone:
        send_sms(
            to=vendor.phone,
            message=text,
            target=vendor_registration,
            notification_type=Notification.NotificationType.REGISTRATION_RECEIVED,
        )


def notify_vendor_payment_confirmed(vendor_registration):
    """The one email a vendor gets — mirrors notify_payment_confirmed."""

    vendor = vendor_registration.vendor

    subject = f"You're confirmed — {vendor_registration.registration_number}"
    text = (
        f"Hi {vendor.full_name},\n\n"
        f"{vendor.business_name}'s registration for {settings.EVENT_NAME} is confirmed"
        f"{' and paid' if vendor_registration.amount else ''}. This email is your proof of "
        "registration.\n\n"
        f"Reference: {vendor_registration.registration_number}\n"
        f"Category: {vendor_registration.category.name}\n"
        f"Amount: {vendor_registration.currency} {vendor_registration.amount}\n"
        f"Event date: {settings.EVENT_DATE}\n"
        f"Venue: {settings.EVENT_LOCATION}\n\n"
        "Our team will be in touch with setup details closer to the date.\n"
    )

    html = render_to_string(
        "notifications/emails/vendor_registration_confirmed.html",
        {
            "contact_name": vendor.full_name,
            "event_name": settings.EVENT_NAME,
            "reference": vendor_registration.registration_number,
            "business_name": vendor.business_name,
            "category_name": vendor_registration.category.name,
            "currency": vendor_registration.currency,
            "amount": vendor_registration.amount,
            "event_date": settings.EVENT_DATE,
            "event_location": settings.EVENT_LOCATION,
            "contact_email": settings.EVENT_CONTACT_EMAIL or settings.DEFAULT_FROM_EMAIL,
            "contact_phone": settings.EVENT_CONTACT_PHONE,
        },
    )

    if vendor.email:
        send_email(
            to=vendor.email,
            subject=subject,
            text_body=text,
            html_body=html,
            target=vendor_registration,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
        )

    if vendor.phone:
        send_sms(
            to=vendor.phone,
            message=text,
            target=vendor_registration,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
        )


def notify_vendor_payment_failed(vendor_registration, *, reason=""):
    vendor = vendor_registration.vendor

    text = (
        f"Hi {vendor.full_name},\n\n"
        f"We couldn't confirm payment for {vendor.business_name}'s registration for "
        f"{settings.EVENT_NAME}{f' ({reason})' if reason else ''}.\n\n"
        "Please try again, or contact us for help.\n"
    )

    if vendor.phone:
        send_sms(
            to=vendor.phone,
            message=text,
            target=vendor_registration,
            notification_type=Notification.NotificationType.PAYMENT_FAILED,
        )
