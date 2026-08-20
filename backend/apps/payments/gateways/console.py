"""
Local-development stand-in for a real payment gateway. No credentials
needed: a payment auto-settles SETTLE_AFTER_SECONDS after being created,
so the whole registration -> pay -> poll -> confirmed flow can be
exercised end-to-end (including the frontend's polling screen) before
Lipila sandbox/production keys exist. Switch to the real gateway with
PAYMENT_GATEWAY=lipila in backend/.env — see settings/base.py.
"""

from django.utils import timezone

SETTLE_AFTER_SECONDS = 5


class ConsoleGateway:
    def create_mobile_collection(self, *, payment, phone_number, callback_url):
        print(f"[console-gateway] mobile money prompt simulated -> {phone_number} for {payment.reference}")  # noqa: T201
        return {
            "provider_reference": f"CONSOLE-{payment.reference}",
            "status": "PROCESSING",
            "raw": {"backend": "console", "phone_number": phone_number},
        }

    def create_card_collection(self, *, payment, participant, city, address, zip_code, country, back_url, callback_url):
        print(f"[console-gateway] card checkout simulated for {payment.reference}")  # noqa: T201
        return {
            "provider_reference": f"CONSOLE-{payment.reference}",
            "status": "PROCESSING",
            # No real hosted checkout to redirect to — the frontend
            # simply keeps polling status instead of navigating away.
            "redirect_url": "",
            "raw": {"backend": "console"},
        }

    def get_collection_status(self, *, payment):
        elapsed = (timezone.now() - payment.created_at).total_seconds()

        if elapsed >= SETTLE_AFTER_SECONDS:
            return {"status": "SUCCESS", "raw": {"backend": "console", "elapsed_seconds": elapsed}}

        return {"status": "PROCESSING", "raw": {"backend": "console", "elapsed_seconds": elapsed}}
