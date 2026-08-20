from django.core.management.base import BaseCommand

from apps.registrations.models import RaceCategory

CATEGORIES = [
    {
        "code": "10k",
        "name": "10KM Competitive Run",
        "distance_label": "10 KM",
        "price": "300.00",
        "description": "Timed competitive race with finisher certificate.",
    },
    {
        "code": "5k-fun-run",
        "name": "5KM Fun Run & Walk",
        "distance_label": "5 KM",
        "price": "250.00",
        "description": "Untimed fun run/walk, open to all ages and fitness levels.",
    },
]


class Command(BaseCommand):
    help = "Seed the Siavonga Independence Run 2026 race categories (idempotent)."

    def handle(self, *args, **options):
        for data in CATEGORIES:
            category, created = RaceCategory.objects.update_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "distance_label": data["distance_label"],
                    "price": data["price"],
                    "description": data["description"],
                    "currency": "ZMW",
                    "is_active": True,
                },
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{verb} category: {category.name} ({category.code})"))
