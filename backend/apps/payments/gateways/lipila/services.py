from .client import LipilaClient
from .phone import normalize_zm_phone


class LipilaGateway:
    """
    Adapts Lipila's API to the common gateway interface documented in
    apps/payments/gateways/base.py. See that module's docstring — this
    is the "real" counterpart to gateways/console.py.
    """

    def __init__(self):
        self.client = LipilaClient()

    def create_mobile_collection(self, *, payment, phone_number, callback_url):
        payload = {
            "referenceId": payment.reference,
            "amount": float(payment.amount),
            "accountNumber": normalize_zm_phone(phone_number),
            "currency": payment.currency,
            # registration_number doesn't exist yet at this point — it's
            # only assigned once the registration is confirmed (see
            # Registration.save()). payment.reference (also sent as
            # referenceId) is stable from the moment payment starts, so
            # it's what identifies this payment everywhere, including
            # the webhook's fallback lookup.
            "narration": f"Siavonga Independence Run — {payment.reference}",
            "referenceData": payment.reference,
        }

        response = self.client.request(
            "POST", "/api/v1/collections/mobile-money", data=payload, callback_url=callback_url
        )

        return {
            "provider_reference": response.get("referenceId", ""),
            "status": "PROCESSING",
            "raw": response,
        }

    def create_card_collection(self, *, payment, participant, city, address, zip_code, country, back_url, callback_url):
        payload = {
            "customerInfo": {
                "firstName": participant.full_name,
                "lastName": "",
                "phoneNumber": normalize_zm_phone(participant.phone),
                "email": participant.email,
                "city": city,
                "country": country or "ZM",
                "address": address,
                "zip": zip_code,
            },
            "collectionRequest": {
                "referenceId": payment.reference,
                "amount": float(payment.amount),
                "currency": payment.currency,
                "accountNumber": normalize_zm_phone(participant.phone),
                "narration": f"Siavonga Independence Run {payment.registration.registration_number}",
                "backUrl": back_url or "",
                "referenceData": payment.registration.registration_number,
            },
        }

        response = self.client.request("POST", "/api/v1/collections/card", data=payload, callback_url=callback_url)

        return {
            "provider_reference": response.get("referenceId", ""),
            "status": "PROCESSING",
            "redirect_url": response.get("cardRedirectionUrl", ""),
            "raw": response,
        }

    def get_collection_status(self, *, payment):
        response = self.client.request(
            "GET", "/api/v1/collections/check-status", params={"referenceId": payment.reference}
        )

        return {"status": (response.get("status") or "").upper(), "raw": response}
