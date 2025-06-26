from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Value, Case, When, BooleanField
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta

from .models import CustomerSubscription
from .forms import CustomerSubscriptionForm, SubscriptionSearchForm
from apps.customer_installations.models import CustomerInstallation


@login_required
def subscription_list(request):
    """List all subscriptions with search and filter."""
    form = SubscriptionSearchForm(request.GET)
    
    # Base queryset
    subscriptions = CustomerSubscription.objects.select_related(
        'installation__customer',
        'plan',
        'collected_by'
    ).annotate(
        is_active_sub=Case(
            When(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
                is_paid=True,
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).order_by('-payment_date')
    
    # Apply filters
    if form.is_valid():
        # Search filter
        search_query = form.cleaned_data.get('search')
        if search_query:
            subscriptions = subscriptions.filter(
                Q(installation__customer__first_name__icontains=search_query) |
                Q(installation__customer__last_name__icontains=search_query) |
                Q(installation__customer__email__icontains=search_query) |
                Q(reference_number__icontains=search_query)
            )
        
        # Payment method filter
        payment_method = form.cleaned_data.get('payment_method')
        if payment_method:
            subscriptions = subscriptions.filter(payment_method=payment_method)
        
        # Status filter
        status = form.cleaned_data.get('status')
        now = timezone.now()
        if status == 'active':
            subscriptions = subscriptions.filter(
                start_date__lte=now,
                end_date__gte=now,
                is_paid=True
            )
        elif status == 'expired':
            subscriptions = subscriptions.filter(
                end_date__lt=now
            )
        elif status == 'expiring_soon':
            three_days_later = now + timedelta(days=3)
            subscriptions = subscriptions.filter(
                end_date__gte=now,
                end_date__lte=three_days_later,
                is_paid=True
            )
    
    # Calculate summary statistics
    total_subscriptions = subscriptions.count()
    active_count = subscriptions.filter(is_active_sub=True).count()
    expired_count = subscriptions.filter(end_date__lt=now).count()
    
    context = {
        'subscriptions': subscriptions,
        'form': form,
        'total_subscriptions': total_subscriptions,
        'active_count': active_count,
        'expired_count': expired_count,
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/subscription_list.html', context)


@login_required
def subscription_create(request):
    """Create a new subscription (process payment)."""
    if request.method == 'POST':
        form = CustomerSubscriptionForm(request.POST, user=request.user)
        if form.is_valid():
            subscription = form.save()
            
            messages.success(
                request,
                f'Subscription created successfully for {subscription.installation.customer.full_name}'
            )
            return redirect('customer_subscriptions:subscription_detail', pk=subscription.pk)
    else:
        # Pre-populate if installation_id in GET params
        initial = {}
        installation_id = request.GET.get('installation_id')
        if installation_id:
            try:
                installation = CustomerInstallation.objects.get(pk=installation_id)
                initial['installation'] = installation
            except CustomerInstallation.DoesNotExist:
                pass
        
        form = CustomerSubscriptionForm(initial=initial, user=request.user)
    
    context = {
        'form': form,
        'title': 'New Subscription Payment',
        'submit_text': 'Process Payment',
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/subscription_form.html', context)


@login_required
def subscription_detail(request, pk):
    """Display subscription details."""
    subscription = get_object_or_404(
        CustomerSubscription.objects.select_related(
            'installation__customer',
            'plan',
            'collected_by'
        ),
        pk=pk
    )
    
    context = {
        'subscription': subscription,
        'is_active': subscription.is_active,
        'days_remaining': subscription.days_remaining,
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/subscription_detail.html', context)


@login_required
def subscription_by_installation(request, installation_id):
    """View subscriptions for a specific installation."""
    installation = get_object_or_404(
        CustomerInstallation.objects.select_related('customer'),
        pk=installation_id
    )
    
    subscriptions = installation.subscriptions.select_related(
        'plan', 'collected_by'
    ).order_by('-start_date')
    
    context = {
        'installation': installation,
        'subscriptions': subscriptions,
        'current_subscription': installation.current_subscription,
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/installation_subscriptions.html', context)


@login_required
@require_http_methods(["GET"])
def expiring_subscriptions(request):
    """View subscriptions expiring soon."""
    days_ahead = int(request.GET.get('days', 7))
    
    now = timezone.now()
    expiry_date = now + timedelta(days=days_ahead)
    
    subscriptions = CustomerSubscription.objects.select_related(
        'installation__customer',
        'plan'
    ).filter(
        start_date__lte=now,
        end_date__gte=now,
        end_date__lte=expiry_date,
        is_paid=True
    ).order_by('end_date')
    
    context = {
        'subscriptions': subscriptions,
        'days_ahead': days_ahead,
        'title': f'Subscriptions Expiring in {days_ahead} Days',
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/expiring_subscriptions.html', context)
