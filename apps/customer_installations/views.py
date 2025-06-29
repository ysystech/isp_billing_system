from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Count, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.http import JsonResponse

from .models import CustomerInstallation
from .forms import CustomerInstallationForm
from apps.lcp.models import NAP
from apps.customers.models import Customer


@login_required
@permission_required('customer_installations.view_installation_list', raise_exception=True)
def installation_list(request):
    """List all customer installations with search and filter."""
    installations = CustomerInstallation.objects.select_related(
        'customer', 'router', 'installation_technician'
    ).order_by('-installation_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        installations = installations.filter(
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(customer__email__icontains=search_query) |
            Q(router__serial_number__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        installations = installations.filter(status=status_filter)
    
    context = {
        'installations': installations,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': CustomerInstallation.STATUS_CHOICES,
        'active_tab': 'installations',
    }
    
    return render(request, 'customer_installations/installation_list.html', context)


@login_required
@permission_required('customer_installations.view_installation_list', raise_exception=True)
def installation_detail(request, pk):
    """Display installation details."""
    installation = get_object_or_404(
        CustomerInstallation.objects.select_related(
            'customer', 'router', 'installation_technician'
        ),
        pk=pk
    )
    
    context = {
        'installation': installation,
        'active_tab': 'installations',
    }
    
    return render(request, 'customer_installations/installation_detail.html', context)


@login_required
@permission_required('customer_installations.create_installation', raise_exception=True)
def installation_create(request):
    """Create a new customer installation."""
    if request.method == 'POST':
        form = CustomerInstallationForm(request.POST)
        if form.is_valid():
            installation = form.save(commit=False)
            installation.is_active = True
            installation.save()
            
            messages.success(
                request, 
                f'Installation created successfully for {installation.customer.full_name}'
            )
            return redirect('customer_installations:installation_detail', pk=installation.pk)
    else:
        form = CustomerInstallationForm()
    
    context = {
        'form': form,
        'title': 'Create Installation',
        'submit_text': 'Create Installation',
        'active_tab': 'installations',
    }
    
    return render(request, 'customer_installations/installation_form.html', context)


@login_required
@permission_required('customer_installations.change_installation_status', raise_exception=True)
def installation_update(request, pk):
    """Update an existing installation."""
    installation = get_object_or_404(CustomerInstallation, pk=pk)
    
    if request.method == 'POST':
        form = CustomerInstallationForm(request.POST, instance=installation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Installation updated successfully')
            return redirect('customer_installations:installation_detail', pk=installation.pk)
    else:
        form = CustomerInstallationForm(instance=installation)
    
    context = {
        'form': form,
        'installation': installation,
        'title': 'Update Installation',
        'submit_text': 'Update Installation',
        'active_tab': 'installations',
    }
    
    return render(request, 'customer_installations/installation_form.html', context)


@login_required
@permission_required('customer_installations.delete_customerinstallation', raise_exception=True)
@require_http_methods(["POST"])
def installation_delete(request, pk):
    """Delete an installation (soft delete by setting status to terminated)."""
    installation = get_object_or_404(CustomerInstallation, pk=pk)
    
    installation.status = 'TERMINATED'
    installation.is_active = False
    installation.save()
    
    messages.success(
        request, 
        f'Installation for {installation.customer.full_name} has been terminated'
    )
    return redirect('customer_installations:installation_list')


@login_required
@permission_required('customer_installations.view_installation_list', raise_exception=True)
def get_nap_ports(request, nap_id):
    """API endpoint to get NAP port availability"""
    try:
        nap = NAP.objects.get(id=nap_id)
        
        # Get all occupied ports
        occupied_ports = CustomerInstallation.objects.filter(
            nap=nap
        ).values_list('nap_port', flat=True)
        
        # Generate port availability data
        ports = []
        for port_num in range(1, nap.port_capacity + 1):
            if port_num in occupied_ports:
                installation = CustomerInstallation.objects.get(nap=nap, nap_port=port_num)
                ports.append({
                    'number': port_num,
                    'available': False,
                    'customer': installation.customer.get_full_name()
                })
            else:
                ports.append({
                    'number': port_num,
                    'available': True,
                    'customer': None
                })
        
        return JsonResponse({
            'nap': {
                'id': nap.id,
                'code': nap.code,
                'name': nap.name,
                'capacity': nap.port_capacity,
                'location': nap.location,
                'lcp': nap.splitter.lcp.code,
                'splitter': nap.splitter.code,
            },
            'ports': ports,
            'available_count': sum(1 for p in ports if p['available']),
            'occupied_count': sum(1 for p in ports if not p['available'])
        })
    except NAP.DoesNotExist:
        return JsonResponse({'error': 'NAP not found'}, status=404)
