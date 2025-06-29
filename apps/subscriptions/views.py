from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from apps.tenants.mixins import tenant_required

from .models import SubscriptionPlan
from .forms import SubscriptionPlanForm, SubscriptionPlanSearchForm


@login_required
@permission_required('subscriptions.view_subscriptionplan_list', raise_exception=True)
def subscription_plan_list(request):
    """List all subscription plans with search and filter functionality."""
    form = SubscriptionPlanSearchForm(request.GET)
    plans = SubscriptionPlan.objects.filter(tenant=request.tenant)
    
    # Apply search filter
    if form.is_valid():
        search_query = form.cleaned_data.get('search')
        is_active = form.cleaned_data.get('is_active')
        
        if search_query:
            plans = plans.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if is_active:
            plans = plans.filter(is_active=(is_active == 'true'))
    
    plans = plans.order_by('price', 'name')
    
    # Handle HTMX request
    if request.htmx:
        return render(request, 'subscriptions/partials/subscription_plan_list.html', {
            'plans': plans
        })
    
    return render(request, 'subscriptions/subscription_plan_list.html', {
        'plans': plans,
        'form': form
    })


@login_required
@permission_required('subscriptions.add_subscriptionplan', raise_exception=True)
def subscription_plan_create(request):
    """Create a new subscription plan."""
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)

            plan.tenant = request.tenant

            plan.save()
            messages.success(request, f'Subscription plan "{plan.name}" created successfully.')
            
            # Return HTMX response
            if request.htmx:
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': '/subscriptions/plans/'}
                )
            return redirect('subscriptions:subscription_plan_list')
    else:
        form = SubscriptionPlanForm()
    
    return render(request, 'subscriptions/subscription_plan_form.html', {
        'form': form,
        'title': 'Create Subscription Plan',
        'submit_text': 'Create Plan'
    })


@login_required
@permission_required('subscriptions.change_subscriptionplan', raise_exception=True)
def subscription_plan_update(request, pk):
    """Update an existing subscription plan."""
    plan = get_object_or_404(SubscriptionPlan.objects.filter(tenant=request.tenant), pk=pk
    
    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save(commit=False)

            plan.tenant = request.tenant

            plan.save()
            messages.success(request, f'Subscription plan "{plan.name}" updated successfully.')
            
            # Return HTMX response
            if request.htmx:
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': '/subscriptions/plans/'}
                )
            return redirect('subscriptions:subscription_plan_list')
    else:
        form = SubscriptionPlanForm(instance=plan)
    
    return render(request, 'subscriptions/subscription_plan_form.html', {
        'form': form,
        'plan': plan,
        'title': f'Update {plan.name}',
        'submit_text': 'Update Plan'
    })


@login_required
@permission_required('subscriptions.delete_subscriptionplan', raise_exception=True)
@require_http_methods(["DELETE"])
def subscription_plan_delete(request, pk):
    """Delete a subscription plan."""
    plan = get_object_or_404(SubscriptionPlan.objects.filter(tenant=request.tenant), pk=pk
    
    # Check if plan has any active subscriptions (will be implemented later)
    # For now, just delete the plan
    
    plan_name = plan.name
    plan.delete()
    messages.success(request, f'Subscription plan "{plan_name}" deleted successfully.')
    
    # Return HTMX response
    if request.htmx:
        return HttpResponse(
            status=204,
            headers={'HX-Redirect': '/subscriptions/plans/'}
        )
    
    return redirect('subscriptions:subscription_plan_list')


@login_required
@permission_required('subscriptions.view_subscriptionplan_list', raise_exception=True)
def subscription_plan_detail(request, pk):
    """View details of a subscription plan."""
    plan = get_object_or_404(SubscriptionPlan.objects.filter(tenant=request.tenant), pk=pk
    
    return render(request, 'subscriptions/subscription_plan_detail.html', {
        'plan': plan
    })
