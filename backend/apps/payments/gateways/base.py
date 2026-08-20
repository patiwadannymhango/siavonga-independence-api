"""
Every gateway (console, lipila, ...) exposes the same three methods, each
returning a plain dict:

    create_mobile_collection(*, payment, phone_number, callback_url)
        -> {"provider_reference": str, "status": str, "raw": dict}

    create_card_collection(*, payment, participant, city, address,
                            zip_code, country, back_url, callback_url)
        -> {"provider_reference": str, "status": str,
            "redirect_url": str, "raw": dict}

    get_collection_status(*, payment)
        -> {"status": str, "raw": dict}

`status` is one of "PROCESSING", "SUCCESS", "FAILED", "CANCELLED" —
apps.payments.services.apply_payment_outcome() maps this onto the
Payment/Registration state machine. This lets apps/payments/services.py
and apps/payments/views.py stay gateway-agnostic; the only place that
knows which gateway is active is get_gateway() below.
"""

from django.conf import settings


def get_gateway():
    if settings.PAYMENT_GATEWAY == "lipila":
        from .lipila.services import LipilaGateway

        return LipilaGateway()

    from .console import ConsoleGateway

    return ConsoleGateway()
