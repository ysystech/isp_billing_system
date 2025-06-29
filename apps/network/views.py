from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from apps.customers.models import Customer
from apps.lcp.models import LCP, Splitter, NAP
from apps.customer_installations.models import CustomerInstallation
import json
from apps.tenants.mixins import tenant_required


@login_required
@tenant_required
def network_map(request):
    """Display all infrastructure and customers on an interactive map"""
    context = {
        'page_title': 'Network Infrastructure Map',
        'active_tab': 'network_map',
    }
    return render(request, 'network/map.html', context)


@login_required 
def network_map_data(request):
    """API endpoint to get network data for the map"""
    
    # Get filter parameters
    show_lcps = request.GET.get('show_lcps', 'true') == 'true'
    show_splitters = request.GET.get('show_splitters', 'true') == 'true'
    show_naps = request.GET.get('show_naps', 'true') == 'true'
    show_customers = request.GET.get('show_customers', 'true') == 'true'
    show_installations = request.GET.get('show_installations', 'true') == 'true'
    
    data = {
        'lcps': [],
        'splitters': [],
        'naps': [],
        'customers': [],
        'installations': []
    }
    
    # Get LCPs with coordinates
    if show_lcps:
        lcps = LCP.objects.filter(tenant=request.tenant, 
            latitude__isnull=False,
            longitude__isnull=False,
            is_active=True
        .annotate(
            splitter_count=Count('splitters'),
            nap_count=Count('splitters__naps', distinct=True)
        )
        
        for lcp in lcps:
            data['lcps'].append({
                'id': lcp.id,
                'code': lcp.code,
                'name': lcp.name,
                'lat': float(lcp.latitude),
                'lng': float(lcp.longitude),
                'location': lcp.location,
                'barangay': lcp.barangay.name,
                'coverage_radius': lcp.coverage_radius_meters,
                'splitter_count': lcp.splitter_count,
                'nap_count': lcp.nap_count,
            })
    
    # Get Splitters with coordinates
    if show_splitters:
        splitters = Splitter.objects.filter(tenant=request.tenant, 
            latitude__isnull=False,
            longitude__isnull=False,
            is_active=True
        .select_related('lcp').annotate(
            nap_count=Count('naps')
        )
        
        for splitter in splitters:
            data['splitters'].append({
                'id': splitter.id,
                'code': splitter.code,
                'type': splitter.type,
                'lat': float(splitter.latitude),
                'lng': float(splitter.longitude),
                'location': splitter.location,
                'lcp_code': splitter.lcp.code,
                'lcp_id': splitter.lcp.id,
                'port_capacity': splitter.port_capacity,
                'used_ports': splitter.used_ports,
                'nap_count': splitter.nap_count,
            })
    
    # Get NAPs with coordinates  
    if show_naps:
        naps = NAP.objects.filter(tenant=request.tenant, 
            latitude__isnull=False,
            longitude__isnull=False,
            is_active=True
        .select_related('splitter__lcp')
        
        for nap in naps:
            data['naps'].append({
                'id': nap.id,
                'code': nap.code,
                'name': nap.name,
                'lat': float(nap.latitude),
                'lng': float(nap.longitude),
                'location': nap.location,
                'splitter_code': nap.splitter.code,
                'splitter_id': nap.splitter.id,
                'lcp_code': nap.splitter.lcp.code,
                'port_capacity': nap.port_capacity,
                'max_distance': nap.max_distance_meters,
            })
    
    # Get Customers with coordinates
    if show_customers:
        customers = Customer.objects.filter(tenant=request.tenant, 
            latitude__isnull=False,
            longitude__isnull=False,
            status='active'
        .select_related('barangay')
        
        for customer in customers:
            data['customers'].append({
                'id': customer.id,
                'name': customer.get_full_name(),
                'lat': float(customer.latitude),
                'lng': float(customer.longitude),
                'address': customer.get_complete_address(),
                'barangay': customer.barangay.name,
            })
    
    return JsonResponse(data)
    
    # Get Installations with coordinates
    if show_installations:
        installations = CustomerInstallation.objects.filter(tenant=request.tenant, 
            latitude__isnull=False,
            longitude__isnull=False,
            status='ACTIVE'
        .select_related('customer__barangay', 'router')
        
        for installation in installations:
            data['installations'].append({
                'id': installation.id,
                'customer_name': installation.customer.get_full_name(),
                'customer_id': installation.customer.id,
                'lat': float(installation.latitude),
                'lng': float(installation.longitude),
                'address': installation.customer.get_complete_address(),
                'barangay': installation.customer.barangay.name,
                'router': installation.router.name if installation.router else 'No router',
                'installation_date': installation.installation_date.strftime('%Y-%m-%d'),
            })
    
    return JsonResponse(data)


@login_required
@tenant_required
def network_hierarchy(request):
    """Display network hierarchy visualization"""
    context = {
        'page_title': 'Network Hierarchy',
        'active_tab': 'network_hierarchy',
    }
    return render(request, 'network/hierarchy.html', context)
