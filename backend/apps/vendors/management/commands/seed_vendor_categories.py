from django.core.management.base import BaseCommand

from apps.vendors.models import VendorCategory

# Placeholder pricing — nobody has told this backend what Siavonga Run
# 2026 actually wants to charge vendors. Review/adjust via
# /django-admin/ or PATCH /api/v1/vendors/admin/categories/<id>/ before
# going live.
CATEGORIES = [
    {
        "code": "vendor-stall",
        "name": "Vendor Stall",
        "price": "500.00",
        "description": "A standard stall for selling goods at the event.",
    },
    {
        "code": "food-beverage-stall",
        "name": "Food & Beverage Stall",
        "price": "700.00",
        "description": "A stall for food or drink vendors.",
    },
    {
        "code": "corporate-activation",
        "name": "Corporate Activation",
        "price": "1500.00",
        "description": "Branded activation space for corporate exhibitors.",
    },
    {
        "code": "official-sponsor",
        "name": "Official Sponsor",
        "price": "0.00",
        "description": "For confirmed event sponsors — registration confirms immediately, no payment required.",
    },
]


class Command(BaseCommand):
    help = "Seed placeholder Siavonga Independence Run 2026 vendor categories (idempotent)."

    def handle(self, *args, **options):
        for data in CATEGORIES:
            category, created = VendorCategory.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "price": data["price"],
                    "description": data["description"],
                    "currency": "ZMW",
                    "is_active": True,
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{verb} vendor category: {category.name} ({category.code})"))

        self.stdout.write(
            self.style.WARNING(
                "Vendor category prices are placeholders — review and adjust them before going live."
            )
        )
