from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse

from apps.customers.models import Customer
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
from apps.tickets.models import Ticket


def customer_portal_required(view_func):
    """Decorator to ensure user has a customer profile"""
    @login_required
    def wrapped_view(request, *args, **kwargs):
        try:
            customer = request.user.customer_profile
        except Customer.DoesNotExist:
            messages.error(request, "You don't have access to the customer portal.")
            return redirect('web:home')
        
        # Add customer to request for easy access
        request.customer = customer
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


@customer_portal_required
def customer_dashboard(request):
    """Main customer portal dashboard"""
    customer = request.customer
    
    # Get active subscriptions
    active_subscriptions = []
    if hasattr(customer, 'installation'):
        active_subscriptions = CustomerSubscription.objects.filter(
            customer_installation=customer.installation,
            status='ACTIVE'
        ).select_related('subscription_plan')
    
    # Get recent tickets
    recent_tickets = Ticket.objects.filter(
        customer=customer
    ).order_by('-created_at')[:5]
    
    # Get installation info
    try:
        installation = CustomerInstallation.objects.get(customer=customer)
    except CustomerInstallation.DoesNotExist:
        installation = None
    
    context = {
        'customer': customer,
        'active_subscriptions': active_subscriptions,
        'recent_tickets': recent_tickets,
        'installation': installation,
    }
    
    return render(request, 'customer_portal/dashboard.html', context)


@customer_portal_required
def customer_profile(request):
    """View and update customer profile"""
    customer = request.customer
    
    if request.method == 'POST':
        # Update contact information only
        phone = request.POST.get('phone_primary')
        if phone:
            customer.phone_primary = phone
            customer.save()
            messages.success(request, "Profile updated successfully.")
        return redirect('customer_portal:profile')
    
    return render(request, 'customer_portal/profile.html', {
        'customer': customer,
    })


@customer_portal_required
def customer_subscriptions(request):
    """View all customer subscriptions"""
    customer = request.customer
    
    subscriptions = []
    if hasattr(customer, 'installation'):
        subscriptions = CustomerSubscription.objects.filter(
            customer_installation=customer.installation
        ).select_related('subscription_plan').order_by('-start_date')
    
    return render(request, 'customer_portal/subscriptions.html', {
        'customer': customer,
        'subscriptions': subscriptions,
    })


@customer_portal_required
def customer_tickets(request):
    """View and create support tickets"""
    customer = request.customer
    
    if request.method == 'POST':
        # Create new ticket
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category', 'other')
        
        if title and description:
            # Get customer installation if exists
            try:
                installation = CustomerInstallation.objects.get(customer=customer)
            except CustomerInstallation.DoesNotExist:
                messages.error(request, "No installation found for your account. Please contact support.")
                return redirect('customer_portal:tickets')
            
            ticket = Ticket.objects.create(
                tenant=customer.tenant,
                customer=customer,
                customer_installation=installation,
                title=title,
                description=description,
                category=category,
                status='pending',  # Use string value directly
                priority='medium',  # Use string value directly
                source='other',  # Customer portal submission
                reported_by=request.user
            )
            messages.success(request, f"Ticket #{ticket.ticket_number} created successfully. We'll respond shortly.")
            return redirect('customer_portal:ticket_detail', pk=ticket.pk)
    
    tickets = Ticket.objects.filter(
        customer=customer
    ).order_by('-created_at')
    
    return render(request, 'customer_portal/tickets.html', {
        'customer': customer,
        'tickets': tickets,
        'category_choices': Ticket.CATEGORY_CHOICES,
    })


@customer_portal_required
def customer_ticket_detail(request, pk):
    """View ticket details"""
    customer = request.customer
    
    try:
        ticket = Ticket.objects.get(pk=pk, customer=customer)
    except Ticket.DoesNotExist:
        messages.error(request, "Ticket not found.")
        return redirect('customer_portal:tickets')
    
    return render(request, 'customer_portal/ticket_detail.html', {
        'customer': customer,
        'ticket': ticket,
    })
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def post_login_redirect(request):
    """
    Redirect users after login based on their role
    """
    user = request.user
    
    # Check if user has a customer profile
    if hasattr(user, 'customer_profile'):
        # Regular customer - redirect to customer portal
        if not user.is_staff and not user.is_tenant_owner:
            return redirect('customer_portal:dashboard')
    
    # Staff or tenant owner - redirect to main dashboard
    return redirect('web:home')
