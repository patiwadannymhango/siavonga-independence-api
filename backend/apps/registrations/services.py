from django.db import transaction

from .models import Participant, Registration


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

    registration.notify_received()

    return registration
