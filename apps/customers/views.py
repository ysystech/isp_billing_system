from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from .forms import CustomerForm, CustomerSearchForm
from .models import Customer


@login_required
@permission_required('customers.view_customer_list', raise_exception=True)
def customer_list(request):
    """List all customers with search and filtering"""
    form = CustomerSearchForm(request.GET or None)
    customers = Customer.objects.select_related("user", "barangay").all()
    
    # Apply search filter
    search_query = request.GET.get("search", "")
    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_primary__icontains=search_query)
        )
    
    # Apply barangay filter
    barangay_id = request.GET.get("barangay", "")
    if barangay_id:
        customers = customers.filter(barangay_id=barangay_id)
    
    # Apply status filter
    status = request.GET.get("status", "")
    if status:
        customers = customers.filter(status=status)
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    # Check if this is an HTMX request
    if request.headers.get("HX-Request"):
        return render(request, "customers/partials/customer_table.html", {
            "page_obj": page_obj,
        })
    
    return render(request, "customers/list.html", {
        "form": form,
        "page_obj": page_obj,
        "active_tab": "customers",
    })


@login_required
@permission_required('customers.view_customer_detail', raise_exception=True)
def customer_detail(request, pk):
    """Display customer details"""
    customer = get_object_or_404(Customer.objects.select_related("user", "barangay"), pk=pk)
    return render(request, "customers/detail.html", {
        "customer": customer,
        "active_tab": "customers",
    })


@login_required
@permission_required('customers.create_customer', raise_exception=True)
def customer_create(request):
    """Create a new customer"""
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer {customer.get_full_name()} created successfully!")
            
            # Check if this is an HTMX request
            if request.headers.get("HX-Request"):
                response = render(request, "customers/partials/customer_row.html", {
                    "customer": customer,
                })
                response["HX-Redirect"] = reverse("customers:customer_detail", kwargs={"pk": customer.pk})
                return response
            
            return redirect("customers:customer_detail", pk=customer.pk)
    else:
        form = CustomerForm()
    
    return render(request, "customers/form.html", {
        "form": form,
        "title": "Add New Customer",
        "active_tab": "customers",
    })


@login_required
@permission_required('customers.change_customer', raise_exception=True)
def customer_update(request, pk):
    """Update customer information"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer {customer.get_full_name()} updated successfully!")
            
            if request.headers.get("HX-Request"):
                return render(request, "customers/partials/customer_row.html", {
                    "customer": customer,
                })
            
            return redirect("customers:customer_detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, "customers/form.html", {
        "form": form,
        "customer": customer,
        "title": f"Edit Customer: {customer.get_full_name()}",
        "active_tab": "customers",
    })


@login_required
@permission_required('customers.remove_customer', raise_exception=True)
@require_http_methods(["POST", "DELETE"])
def customer_delete(request, pk):
    """Delete (deactivate) a customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == "POST":
        # Soft delete - just change status to terminated
        customer.status = Customer.TERMINATED
        customer.save()
        messages.success(request, f"Customer {customer.get_full_name()} has been deactivated.")
        
        if request.headers.get("HX-Request"):
            response = render(request, "customers/partials/customer_row.html", {
                "customer": customer,
            })
            response["HX-Trigger"] = "customerDeleted"
            return response
        
        return redirect("customers:customer_list")


@login_required
@permission_required('customers.view_customer_list', raise_exception=True)
def customer_quick_stats(request):
    """Get quick statistics for dashboard"""
    stats = {
        "total": Customer.objects.count(),
        "active": Customer.objects.filter(status=Customer.ACTIVE).count(),
        "inactive": Customer.objects.filter(status=Customer.INACTIVE).count(),
        "suspended": Customer.objects.filter(status=Customer.SUSPENDED).count(),
    }
    
    if request.headers.get("HX-Request"):
        return render(request, "customers/partials/quick_stats.html", {
            "stats": stats,
        })
    
    return render(request, "customers/stats.html", {
        "stats": stats,
        "active_tab": "customers",
    })


@login_required
def customer_coordinates_api(request):
    """API endpoint to get customer coordinates"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            customer_ids = data.get('customer_ids', [])
            
            customers = Customer.objects.filter(
                id__in=customer_ids
            ).values('id', 'latitude', 'longitude', 'location_notes')
            
            return JsonResponse(list(customers), safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
