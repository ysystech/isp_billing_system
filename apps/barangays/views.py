from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.tenants.mixins import tenant_required
from apps.barangays.models import Barangay
from apps.barangays.forms import BarangayForm


@login_required
@tenant_required
@permission_required('barangays.view_barangay_list', raise_exception=True)
def barangay_list(request):
    """List all barangays with search and pagination"""
    barangays = Barangay.objects.filter(tenant=request.tenant).annotate(
        active_customers=Count("customers", filter=Q(customers__status="active")),
        total_customers=Count("customers")
    )
    
    # Search functionality
    search = request.GET.get("search", "")
    if search:
        barangays = barangays.filter(
            Q(name__icontains=search) | 
            Q(code__icontains=search)
        )
    
    # Filter by active status
    is_active = request.GET.get("is_active", "")
    if is_active == "true":
        barangays = barangays.filter(is_active=True)
    elif is_active == "false":
        barangays = barangays.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(barangays, 20)
    page = request.GET.get("page", 1)
    barangays_page = paginator.get_page(page)
    
    context = {
        "barangays": barangays_page,
        "search": search,
        "is_active": is_active,
        "active_tab": "barangays",
    }
    
    # Handle HTMX requests
    if request.headers.get("HX-Request"):
        return render(request, "barangays/partials/barangay_list.html", context)
    
    return render(request, "barangays/barangay_list.html", context)


@login_required
@tenant_required
@permission_required('barangays.view_barangay_list', raise_exception=True)
def barangay_detail(request, pk):
    """View barangay details"""
    barangay = get_object_or_404(
        Barangay.objects.filter(tenant=request.tenant).annotate(
            active_customers=Count("customers", filter=Q(customers__status="active")),
            total_customers=Count("customers")
        ),
        pk=pk
    )
    
    # Get customers in this barangay
    customers = barangay.customers.select_related("barangay").order_by("-created_at")[:10]
    
    context = {
        "barangay": barangay,
        "recent_customers": customers,
        "active_tab": "barangays",
    }
    
    return render(request, "barangays/barangay_detail.html", context)


@login_required
@tenant_required
@permission_required('barangays.add_barangay', raise_exception=True)
def barangay_create(request):
    """Create a new barangay"""
    if request.method == "POST":
        form = BarangayForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            try:
                barangay = form.save(commit=False)
                barangay.tenant = request.tenant
                barangay.save()
                messages.success(request, f"Barangay '{barangay.name}' created successfully!")
                
                if request.headers.get("HX-Request"):
                    response = HttpResponse("")
                    response["HX-Redirect"] = f"/barangays/{barangay.pk}/"
                    return response
                return redirect("barangays:detail", pk=barangay.pk)
            except IntegrityError as e:
                # Handle any database integrity errors
                if 'name' in str(e):
                    form.add_error('name', 'A barangay with this name already exists.')
                elif 'code' in str(e):
                    form.add_error('code', 'A barangay with this code already exists.')
                else:
                    form.add_error(None, 'An error occurred while saving the barangay. Please check your input.')
    else:
        form = BarangayForm(tenant=request.tenant)
    
    context = {"form": form, "active_tab": "barangays"}
    
    if request.headers.get("HX-Request"):
        return render(request, "barangays/partials/barangay_form.html", context)
    
    return render(request, "barangays/barangay_create.html", context)


@login_required
@tenant_required
@permission_required('barangays.change_barangay', raise_exception=True)
def barangay_update(request, pk):
    """Update a barangay"""
    barangay = get_object_or_404(Barangay.objects.filter(tenant=request.tenant), pk=pk)
    
    if request.method == "POST":
        form = BarangayForm(request.POST, instance=barangay, tenant=request.tenant)
        if form.is_valid():
            try:
                barangay = form.save()
                messages.success(request, f"Barangay '{barangay.name}' updated successfully!")
                
                if request.headers.get("HX-Request"):
                    response = HttpResponse("")
                    response["HX-Redirect"] = f"/barangays/{barangay.pk}/"
                    return response
                return redirect("barangays:detail", pk=barangay.pk)
            except IntegrityError as e:
                # Handle any database integrity errors
                if 'name' in str(e):
                    form.add_error('name', 'A barangay with this name already exists.')
                elif 'code' in str(e):
                    form.add_error('code', 'A barangay with this code already exists.')
                else:
                    form.add_error(None, 'An error occurred while saving the barangay. Please check your input.')
    else:
        form = BarangayForm(instance=barangay, tenant=request.tenant)
    
    context = {
        "form": form,
        "barangay": barangay,
        "active_tab": "barangays",
    }
    
    if request.headers.get("HX-Request"):
        return render(request, "barangays/partials/barangay_form.html", context)
    
    return render(request, "barangays/barangay_update.html", context)


@login_required
@tenant_required
@permission_required('barangays.delete_barangay', raise_exception=True)
@require_http_methods(["DELETE"])
def barangay_delete(request, pk):
    """Delete a barangay (soft delete by setting is_active=False)"""
    barangay = get_object_or_404(Barangay.objects.filter(tenant=request.tenant), pk=pk)
    
    # Check if barangay has customers
    if barangay.customers.exists():
        barangay.is_active = False
        barangay.save()
        messages.warning(
            request, 
            f"Barangay '{barangay.name}' has been deactivated (has existing customers)."
        )
    else:
        barangay.delete()
        messages.success(request, f"Barangay '{barangay.name}' deleted successfully!")
    
    response = HttpResponse("")
    response["HX-Redirect"] = "/barangays/"
    return response


@login_required
@tenant_required
def barangay_quick_stats(request):
    """Get quick statistics for barangays (for dashboard)"""
    stats = {
        "total": Barangay.objects.filter(tenant=request.tenant).count(),
        "active": Barangay.objects.filter(tenant=request.tenant, is_active=True).count(),
        "with_customers": Barangay.objects.filter(
            tenant=request.tenant, 
            customers__isnull=False
        ).distinct().count(),
    }
    
    return render(request, "barangays/partials/barangay_stats.html", {"stats": stats})
