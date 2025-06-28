from django.core.management.base import BaseCommand
from django.db import transaction
from apps.barangays.models import Barangay
from apps.lcp.models import LCP, Splitter, NAP


class Command(BaseCommand):
    help = 'Generate sample LCP data with splitters and NAPs'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample LCP data...')
        
        # Get barangays for LCP assignment
        barangays = list(Barangay.objects.filter(is_active=True)[:2])
        if len(barangays) < 2:
            self.stdout.write(self.style.ERROR(
                'Need at least 2 active barangays. Please run: python manage.py generate_barangays'
            ))
            return
        
        # Create first LCP with mixed splitter types
        lcp1 = LCP.objects.create(
            name="Carmen Central LCP",
            code="LCP-001",
            location="Near Carmen Basketball Court, beside Barangay Hall",
            barangay=barangays[0],
            notes="Main distribution point for Carmen area"
        )
        
        # Add splitters to LCP-001
        splitter1_1 = Splitter.objects.create(
            lcp=lcp1,
            code="SP-01A",
            type="1:8",
            location="Cabinet A, Upper Shelf"
        )
        
        splitter1_2 = Splitter.objects.create(
            lcp=lcp1,
            code="SP-01B",
            type="1:16",
            location="Cabinet A, Lower Shelf"
        )
        
        # Add NAPs to first 1:8 splitter (using 5 of 8 ports)
        nap_data_1 = [
            (1, "NAP-001", "Carmen St. Corner", "Electric post near #123 Carmen St.", 8),
            (2, "NAP-002", "Rosario Junction", "Post at Rosario-Carmen intersection", 8),
            (3, "NAP-003", "School Gate NAP", "Post outside Carmen Elementary School", 16),
            (5, "NAP-004", "Market Area", "Post near Carmen Public Market entrance", 8),
            (7, "NAP-005", "Chapel NAP", "Post beside San Roque Chapel", 8),
        ]
        
        for port, code, name, location, capacity in nap_data_1:
            NAP.objects.create(
                splitter=splitter1_1,
                splitter_port=port,
                code=code,
                name=name,
                location=location,
                port_capacity=capacity
            )
        
        # Add NAPs to 1:16 splitter (using 8 of 16 ports)
        nap_data_2 = [
            (1, "NAP-006", "Subdivision Entry", "Main gate of Villa Carmen Subdivision", 8),
            (3, "NAP-007", "Basketball Court", "Post at covered court area", 8),
            (4, "NAP-008", "Health Center", "Near Carmen Health Center", 8),
            (7, "NAP-009", "Rivera St. NAP", "Corner of Rivera-Santos Streets", 8),
            (9, "NAP-010", "Park NAP", "Carmen Memorial Park entrance", 8),
            (11, "NAP-011", "Highway Junction", "Near national highway intersection", 16),
            (14, "NAP-012", "Riverside NAP", "Post along Carmen River road", 8),
            (16, "NAP-013", "Hill Top", "Upper Carmen residential area", 8),
        ]
        
        for port, code, name, location, capacity in nap_data_2:
            NAP.objects.create(
                splitter=splitter1_2,
                splitter_port=port,
                code=code,
                name=name,
                location=location,
                port_capacity=capacity
            )
        
        # Create second LCP with different configuration
        lcp2 = LCP.objects.create(
            name="Lapasan Highway LCP",
            code="LCP-002",
            location="Along National Highway, near Lapasan Bridge",
            barangay=barangays[1],
            notes="Serves highway commercial area and nearby residential"
        )
        
        # Add splitters to LCP-002
        splitter2_1 = Splitter.objects.create(
            lcp=lcp2,
            code="SP-02A",
            type="1:32",
            location="Main Cabinet"
        )
        
        splitter2_2 = Splitter.objects.create(
            lcp=lcp2,
            code="SP-02B",
            type="1:8",
            location="Expansion Cabinet"
        )
        
        # Add NAPs to 1:32 splitter (using 12 of 32 ports - sparse deployment)
        nap_data_3 = [
            (1, "NAP-014", "Highway Commercial 1", "Near Gaisano Mall entrance", 16),
            (4, "NAP-015", "Gas Station NAP", "Post at Phoenix Gas Station", 8),
            (8, "NAP-016", "Bridge Approach", "Before Lapasan Bridge northbound", 8),
            (10, "NAP-017", "Residential Phase 1", "Entrance to Phase 1 subdivision", 8),
            (15, "NAP-018", "Residential Phase 2", "Phase 2 subdivision main road", 8),
            (18, "NAP-019", "Commercial Block A", "Post near BDO branch", 8),
            (20, "NAP-020", "Commercial Block B", "Post near Mercury Drug", 8),
            (23, "NAP-021", "Food Court Area", "Behind highway food court", 16),
            (25, "NAP-022", "Transport Terminal", "Lapasan Transport Terminal", 8),
            (28, "NAP-023", "Church NAP", "Post outside Lapasan Church", 8),
            (30, "NAP-024", "School NAP 2", "Lapasan National High School gate", 16),
            (32, "NAP-025", "Bridge Exit", "After Lapasan Bridge southbound", 8),
        ]
        
        for port, code, name, location, capacity in nap_data_3:
            NAP.objects.create(
                splitter=splitter2_1,
                splitter_port=port,
                code=code,
                name=name,
                location=location,
                port_capacity=capacity
            )
        
        # Add NAPs to 1:8 splitter (using 3 of 8 ports - room for expansion)
        nap_data_4 = [
            (1, "NAP-026", "Industrial Area", "Lapasan Industrial Zone entrance", 16),
            (3, "NAP-027", "Warehouse District", "Post near logistics warehouses", 8),
            (6, "NAP-028", "Future Development", "Reserved for upcoming mall", 16),
        ]
        
        for port, code, name, location, capacity in nap_data_4:
            NAP.objects.create(
                splitter=splitter2_2,
                splitter_port=port,
                code=code,
                name=name,
                location=location,
                port_capacity=capacity
            )
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\nSample LCP data created successfully!'))
        self.stdout.write('\nSummary:')
        self.stdout.write(f'- LCP-001 ({lcp1.name}):')
        self.stdout.write(f'  - Splitters: {lcp1.splitters.count()}')
        self.stdout.write(f'  - Total NAPs: {NAP.objects.filter(splitter__lcp=lcp1).count()}')
        self.stdout.write(f'  - SP-01A (1:8): {splitter1_1.used_ports}/{splitter1_1.port_capacity} ports used')
        self.stdout.write(f'  - SP-01B (1:16): {splitter1_2.used_ports}/{splitter1_2.port_capacity} ports used')
        
        self.stdout.write(f'\n- LCP-002 ({lcp2.name}):')
        self.stdout.write(f'  - Splitters: {lcp2.splitters.count()}')
        self.stdout.write(f'  - Total NAPs: {NAP.objects.filter(splitter__lcp=lcp2).count()}')
        self.stdout.write(f'  - SP-02A (1:32): {splitter2_1.used_ports}/{splitter2_1.port_capacity} ports used')
        self.stdout.write(f'  - SP-02B (1:8): {splitter2_2.used_ports}/{splitter2_2.port_capacity} ports used')
