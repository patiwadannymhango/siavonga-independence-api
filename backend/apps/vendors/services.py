from decimal import Decimal

from django.db import transaction

from .models import Vendor, VendorRegistration


@transaction.atomic
def create_vendor_registration(*, category, vendor_data, details, status=None):
    """
    Create the Vendor + VendorRegistration pair. If `status` isn't given
    explicitly (the public registration flow), a free category (e.g.
    "Official Sponsor", price 0) confirms immediately — there's nothing
    to pay, so there's no reason to make the vendor go through a payment
    step just to reach CONFIRMED. Admin-created registrations (walk-ins,
    cash taken in person) pass `status` explicitly instead.
    """

    vendor = Vendor.objects.create(
        business_name=vendor_data["business_name"],
        full_name=vendor_data["full_name"],
        email=vendor_data.get("email", ""),
        phone=vendor_data.get("phone", ""),
        business_location=vendor_data.get("business_location", ""),
    )

    if status is None:
        status = (
            VendorRegistration.Status.CONFIRMED
            if category.price <= Decimal("0")
            else VendorRegistration.Status.PENDING_PAYMENT
        )

    vendor_registration = VendorRegistration.objects.create(
        vendor=vendor,
        category=category,
        status=status,
        amount=category.price,
        currency=category.currency,
        products_services=details.get("products_services", ""),
        requirement=details.get("requirement", ""),
    )

    vendor_registration.notify_received()

    if status == VendorRegistration.Status.CONFIRMED:
        vendor_registration.notify_confirmed()

    return vendor_registration
