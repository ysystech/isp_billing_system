from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.customers.models import Customer
from apps.lcp.models import LCP, Splitter, NAP


@login_required
def test_geolocation(request):
    """Test page to verify geo-location features"""
    context = {
        'customers_with_coords': Customer.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True),
        'customers_without_coords': Customer.objects.filter(latitude__isnull=True),
        'lcps_with_coords': LCP.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True),
        'naps_with_coords': NAP.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True),
        'splitters_with_coords': Splitter.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True),
    }
    return render(request, 'test_geolocation.html', context)
