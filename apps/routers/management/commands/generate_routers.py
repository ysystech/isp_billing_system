import random
from django.core.management.base import BaseCommand
from apps.routers.models import Router


class Command(BaseCommand):
    help = "Generate sample router data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of routers to create"
        )

    def handle(self, *args, **options):
        count = options["count"]
        
        # Router brands and models
        router_data = [
            ("TP-Link", ["Archer C6", "Archer C7", "Archer AX10", "Archer AX50", ""]),
            ("Mikrotik", ["RB750", "RB941", "hAP ac2", "hAP ax2", ""]),
            ("Ubiquiti", ["UniFi AC Lite", "UniFi AC LR", "UniFi AC Pro", ""]),
            ("Tenda", ["AC10", "AC1200", "N301", "F3", ""]),
        ]
        
        created_count = 0
        
        for i in range(count):
            # Random brand and model
            brand, models = random.choice(router_data)
            model = random.choice(models)
            
            # Generate unique serial
            serial_number = f"{brand[:2].upper()}{random.randint(100000, 999999)}"
            
            # Sometimes add notes
            notes = ""
            if random.random() > 0.7:  # 30% chance to have notes
                notes_options = [
                    "Working perfectly",
                    "Installed in customer premises",
                    "Spare unit",
                    "New purchase",
                    "Replacement unit",
                ]
                notes = random.choice(notes_options)
            
            # Create router
            router = Router(
                brand=brand,
                model=model,
                serial_number=serial_number,
                notes=notes,
            )
            
            try:
                router.save()
                created_count += 1
                self.stdout.write(f"Created router: {router}")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to create router: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} routers")
        )
