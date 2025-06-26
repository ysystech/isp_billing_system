from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import CustomerInstallation
from .forms import CustomerInstallationForm
from apps.customers.models import Customer


@login_required
def installation_list(request):
    """List all customer installations with search and filter."""
    installations = CustomerInstallation.objects.select_related(
        'customer', 'router', 'installation_technician'
    ).annotate(
        active_subscriptions=Count(
            'subscriptions',
            filter=Q(
                subscriptions__start_date__lte=timezone.now(),
                subscriptions__end_date__gte=timezone.now(),
                subscriptions__is_paid=True
            )
        ),
        last_payment=Max('subscriptions__payment_date')
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
    
    # Filter by subscription status
    subscription_status = request.GET.get('subscription_status', '')
    if subscription_status == 'active':
        installations = installations.filter(active_subscriptions__gt=0)
    elif subscription_status == 'expired':
        installations = installations.filter(active_subscriptions=0)
    
    context = {
        'installations': installations,
        'search_query': search_query,
        'status_filter': status_filter,
        'subscription_status': subscription_status,
        'status_choices': CustomerInstallation.STATUS_CHOICES,
        'active_tab': 'installations',
    }
    
    return render(request, 'customer_installations/installation_list.html', context)


@login_required
def installation_detail(request, pk):
    """Display installation details with subscription history."""
    installation = get_object_or_404(
        CustomerInstallation.objects.select_related(
            'customer', 'router', 'installation_technician'
        ),
        pk=pk
    )
    
    # Get subscription history
    subscriptions = installation.subscriptions.select_related(
        'plan', 'collected_by'
    ).order_by('-start_date')
    
    context = {
        'installation': installation,
        'subscriptions': subscriptions,
        'current_subscription': installation.current_subscription,
        'is_expired': installation.is_expired,
        'active_tab': 'installations',
    }
    
    return render(request, 'customer_installations/installation_detail.html', context)


@login_required
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
@require_http_methods(["POST"])
def installation_delete(request, pk):
    """Delete an installation (soft delete by setting status to terminated)."""
    installation = get_object_or_404(CustomerInstallation, pk=pk)
    
    # Check if installation has active subscriptions
    if installation.current_subscription:
        messages.error(
            request, 
            'Cannot delete installation with active subscription'
        )
        return redirect('customer_installations:installation_detail', pk=pk)
    
    installation.status = 'TERMINATED'
    installation.is_active = False
    installation.save()
    
    messages.success(
        request, 
        f'Installation for {installation.customer.full_name} has been terminated'
    )
    return redirect('customer_installations:installation_list')
