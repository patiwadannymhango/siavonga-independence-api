from django.db import transaction

from .models import Participant, Registration

REFERENCE_PREFIX = "SIR"


@transaction.atomic
def create_registration(
    *,
    category,
    participant_data,
    details,
    status=Registration.Status.PENDING_PAYMENT,
):
    """
    Create the Participant + Registration pair. `details` holds the
    registration-specific fields (t-shirt size, club, emergency contact,
    medical notes, accepted_terms) that live on Registration rather than
    Participant.
    """

    participant = Participant.objects.create(
        full_name=participant_data["full_name"],
        email=participant_data.get("email", ""),
        phone=participant_data.get("phone", ""),
        gender=participant_data.get("gender", ""),
        age_range=participant_data.get("age_range", ""),
        country=participant_data.get("country", ""),
    )

    registration = Registration.objects.create(
        participant=participant,
        category=category,
        registration_number=generate_registration_number(),
        status=status,
        amount=category.price,
        currency=category.currency,
        t_shirt_size=details.get("t_shirt_size", ""),
        club_or_institution=details.get("club_or_institution", ""),
        emergency_contact_name=details.get("emergency_contact_name", ""),
        emergency_contact_phone=details.get("emergency_contact_phone", ""),
        medical_notes=details.get("medical_notes", ""),
        accepted_terms=details.get("accepted_terms", False),
    )

    from apps.notifications.services import notify_registration_received

    notify_registration_received(registration)

    return registration


def generate_registration_number():
    """
    Scanning every existing number for the max (rather than trusting the
    most-recently-registered row) means a single malformed/blank
    registration_number can't get "stuck" as the reference point and
    keep producing the same already-taken number on every subsequent
    attempt.
    """

    last_number = 0

    existing_numbers = Registration.objects.exclude(registration_number="").values_list(
        "registration_number", flat=True
    )

    for registration_number in existing_numbers:
        try:
            number = int(registration_number.rsplit("-", 1)[-1])
        except (ValueError, IndexError):
            continue
        last_number = max(last_number, number)

    next_number = last_number + 1

    return f"{REFERENCE_PREFIX}-{next_number:05d}"
