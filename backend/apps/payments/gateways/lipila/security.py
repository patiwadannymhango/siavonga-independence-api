import base64
import hashlib
import hmac
import time

from django.conf import settings


class InvalidLipilaWebhook(Exception):
    pass


def verify_lipila_webhook(*, webhook_id, webhook_timestamp, webhook_signature, raw_body):
    if not all([webhook_id, webhook_timestamp, webhook_signature]):
        raise InvalidLipilaWebhook("Missing webhook security headers.")

    try:
        timestamp = int(webhook_timestamp)
    except ValueError:
        raise InvalidLipilaWebhook("Invalid webhook timestamp.")

    tolerance = 300  # seconds — guards against very old/replayed requests
    if abs(time.time() - timestamp) > tolerance:
        raise InvalidLipilaWebhook("Webhook timestamp is too old.")

    signed_payload = f"{webhook_id}.{webhook_timestamp}.".encode() + raw_body

    try:
        secret_bytes = base64.b64decode(settings.LIPILA_WEBHOOK_SECRET)
    except Exception:
        raise InvalidLipilaWebhook("Invalid webhook secret.")

    digest = hmac.new(secret_bytes, signed_payload, hashlib.sha256).digest()
    expected_signature = base64.b64encode(digest).decode()

    valid = False
    for signature in webhook_signature.split(" "):
        if not signature.startswith("v1,"):
            continue
        received_signature = signature.split(",", 1)[1]
        if hmac.compare_digest(received_signature, expected_signature):
            valid = True
            break

    if not valid:
        raise InvalidLipilaWebhook("Invalid webhook signature.")

    return True
