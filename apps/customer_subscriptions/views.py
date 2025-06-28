from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Prefetch
from decimal import Decimal
import json

from .models import CustomerSubscription
from .forms import CustomerSubscriptionForm
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan


@login_required
def subscription_list(request):
    """List all customer subscriptions with filtering."""
    subscriptions = CustomerSubscription.objects.select_related(
        'customer_installation__customer',
        'subscription_plan',
        'created_by'
    ).order_by('-start_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        subscriptions = subscriptions.filter(
            Q(customer_installation__customer__first_name__icontains=search_query) |
            Q(customer_installation__customer__last_name__icontains=search_query) |
            Q(customer_installation__customer__email__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    
    # Filter by subscription type
    type_filter = request.GET.get('subscription_type', '')
    if type_filter:
        subscriptions = subscriptions.filter(subscription_type=type_filter)
    
    # Update expired subscriptions
    for sub in subscriptions:
        sub.update_status()
        if sub.status == 'EXPIRED':
            sub.save()
    
    context = {
        'subscriptions': subscriptions,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_choices': CustomerSubscription.STATUS_CHOICES,
        'type_choices': CustomerSubscription.SUBSCRIPTION_TYPES,
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/subscription_list.html', context)


@login_required
def subscription_create(request):
    """Create a new subscription with preview."""
    # Check if installation_id is passed in query params
    installation_id = request.GET.get('installation_id')
    initial = {}
    
    if installation_id:
        try:
            installation = CustomerInstallation.objects.get(pk=installation_id)
            initial['customer_installation'] = installation
            
            # Get latest subscription to determine start date
            latest_sub = CustomerSubscription.get_latest_subscription(installation)
            if latest_sub and latest_sub.end_date > timezone.now():
                initial['start_date'] = latest_sub.end_date
        except CustomerInstallation.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = CustomerSubscriptionForm(request.POST, user=request.user)
        if form.is_valid():
            subscription = form.save()
            messages.success(
                request,
                f'Subscription created successfully for {subscription.customer_installation.customer.full_name}'
            )
            return redirect('customer_subscriptions:subscription_detail', pk=subscription.pk)
    else:
        form = CustomerSubscriptionForm(initial=initial, user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Subscription',
        'submit_text': 'Create Subscription',
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/subscription_form.html', context)


@login_required
def subscription_detail(request, pk):
    """View subscription details."""
    subscription = get_object_or_404(
        CustomerSubscription.objects.select_related(
            'customer_installation__customer',
            'subscription_plan',
            'created_by'
        ),
        pk=pk
    )
    
    # Update status if needed
    subscription.update_status()
    if subscription.status == 'EXPIRED':
        subscription.save()
    
    context = {
        'subscription': subscription,
        'active_tab': 'subscriptions',
    }
    
    return render(request, 'customer_subscriptions/subscription_detail.html', context)


@login_required
def subscription_cancel(request, pk):
    """Cancel a subscription."""
    subscription = get_object_or_404(CustomerSubscription, pk=pk)
    
    if request.method == 'POST':
        subscription.status = 'CANCELLED'
        subscription.save()
        messages.success(request, 'Subscription cancelled successfully')
        return redirect('customer_subscriptions:subscription_detail', pk=subscription.pk)
    
    return redirect('customer_subscriptions:subscription_detail', pk=subscription.pk)


# API Endpoints for AJAX functionality

@login_required
def api_get_latest_subscription(request):
    """Get the latest subscription for an installation."""
    installation_id = request.GET.get('installation_id')
    
    if not installation_id:
        return JsonResponse({'error': 'No installation ID provided'}, status=400)
    
    try:
        installation = CustomerInstallation.objects.get(pk=installation_id)
        latest_sub = CustomerSubscription.get_latest_subscription(installation)
        
        if latest_sub and latest_sub.end_date > timezone.now():
            return JsonResponse({
                'has_active': True,
                'end_date': latest_sub.end_date.isoformat(),
                'end_date_display': latest_sub.end_date.strftime('%Y-%m-%d %H:%M'),
                'plan_name': latest_sub.subscription_plan.name,
                'status': latest_sub.status
            })
        else:
            return JsonResponse({
                'has_active': False,
                'suggested_start': timezone.now().isoformat()
            })
    except CustomerInstallation.DoesNotExist:
        return JsonResponse({'error': 'Installation not found'}, status=404)


@login_required
def api_calculate_preview(request):
    """Calculate subscription preview based on amount and type."""
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')
        amount = Decimal(str(data.get('amount', 0)))
        subscription_type = data.get('subscription_type')
        
        if not all([plan_id, subscription_type]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        plan = SubscriptionPlan.objects.get(pk=plan_id)
        
        # Calculate preview
        preview = CustomerSubscription.calculate_preview(
            plan.price,
            amount,
            subscription_type
        )
        
        # Add formatted amount based on type
        if subscription_type == 'one_month':
            preview['amount'] = float(plan.price)
        elif subscription_type == 'fifteen_days':
            preview['amount'] = float(plan.price / 2)
        else:
            preview['amount'] = float(amount)
        
        return JsonResponse(preview)
        
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({'error': 'Plan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required 
def api_get_plan_price(request):
    """Get the price of a subscription plan."""
    plan_id = request.GET.get('plan_id')
    
    if not plan_id:
        return JsonResponse({'error': 'No plan ID provided'}, status=400)
    
    try:
        plan = SubscriptionPlan.objects.get(pk=plan_id)
        return JsonResponse({
            'price': float(plan.price),
            'name': plan.name,
            'speed': plan.speed
        })
    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({'error': 'Plan not found'}, status=404)


@login_required
def active_subscriptions(request):
    """View all active subscriptions per customer."""
    # Get all active installations with current active subscriptions
    active_installations = CustomerInstallation.objects.filter(
        status='ACTIVE'
    ).select_related(
        'customer',
        'installation_technician',
        'nap__splitter__lcp'
    ).prefetch_related(
        Prefetch(
            'subscriptions',
            queryset=CustomerSubscription.objects.filter(
                status='ACTIVE'
            ).select_related('subscription_plan').order_by('-end_date'),
            to_attr='active_subscriptions'
        )
    )

    print(active_installations)
    print("-----------------")
    
    # Build list of installations with active subscriptions
    installations_data = []
    for installation in active_installations:
        if installation.active_subscriptions:
            # Get the current active subscription (latest end date)
            current_sub = installation.active_subscriptions[0]
            installations_data.append({
                'installation': installation,
                'current_subscription': current_sub,
                'days_remaining': int(current_sub.days_remaining) if current_sub.days_remaining > 0 else 0
            })
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        filtered_data = []
        for data in installations_data:
            customer = data['installation'].customer
            if (search_query.lower() in customer.first_name.lower() or
                search_query.lower() in customer.last_name.lower() or
                search_query.lower() in customer.email.lower()):
                filtered_data.append(data)
        installations_data = filtered_data
    
    context = {
        'installations_data': installations_data,
        'search_query': search_query,
        'active_tab': 'active_subscriptions',
        'current_time': timezone.now(),
    }
    print(context)
    
    return render(request, 'customer_subscriptions/active_subscriptions.html', context)


@login_required
def customer_payment_history(request, customer_id):
    """View all payment history for a specific customer."""
    # Get all installations for this customer
    installations = CustomerInstallation.objects.filter(
        customer_id=customer_id
    ).prefetch_related(
        Prefetch(
            'subscriptions',
            queryset=CustomerSubscription.objects.select_related(
                'subscription_plan',
                'created_by'
            ).order_by('-created_at')
        )
    )
    
    # Collect all subscriptions from all installations
    all_subscriptions = []
    customer = None
    
    for installation in installations:
        if not customer:
            customer = installation.customer
        for subscription in installation.subscriptions.all():
            subscription.installation = installation  # Add installation reference
            all_subscriptions.append(subscription)
    
    # Sort by created date (newest first)
    all_subscriptions.sort(key=lambda x: x.created_at, reverse=True)
    
    # Calculate total payments
    total_amount = sum(sub.amount for sub in all_subscriptions)
    
    context = {
        'customer': customer,
        'subscriptions': all_subscriptions,
        'total_amount': total_amount,
        'subscription_count': len(all_subscriptions),
        'active_tab': 'active_subscriptions',
    }
    
    return render(request, 'customer_subscriptions/payment_history.html', context)
