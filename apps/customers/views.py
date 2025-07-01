from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from apps.tenants.mixins import tenant_required
from apps.customer_portal.forms import CustomerWithUserForm
from .forms import CustomerForm, CustomerSearchForm
from .models import Customer


@login_required
@tenant_required
@permission_required('customers.view_customer_list', raise_exception=True)
def customer_list(request):
    """List all customers with search and filtering"""
    form = CustomerSearchForm(request.GET or None, tenant=request.tenant)
    customers = Customer.objects.select_related("user", "barangay").filter(tenant=request.tenant)
    
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
        "page_obj": page_obj,
        "form": form,
        "search_query": search_query,
        "active_tab": "customers",
    })


@login_required
@tenant_required
@permission_required('customers.view_customer_detail', raise_exception=True)
def customer_detail(request, pk):
    """Display customer details"""
    customer = get_object_or_404(
        Customer.objects.select_related("user", "barangay").filter(tenant=request.tenant), 
        pk=pk
    )
    
    # Check if we have new credentials to display
    new_credentials = None
    if 'new_customer_credentials' in request.session:
        creds = request.session['new_customer_credentials']
        if creds['customer_id'] == customer.id:
            new_credentials = creds
            # Remove from session after retrieving
            del request.session['new_customer_credentials']
    
    return render(request, "customers/detail.html", {
        "customer": customer,
        "new_credentials": new_credentials,
        "active_tab": "customers",
    })


@login_required
@tenant_required
@permission_required('customers.create_customer', raise_exception=True)
def customer_create(request):
    """Create a new customer"""
    if request.method == "POST":
        form = CustomerWithUserForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.tenant = request.tenant
            customer = form.save()  # This will handle user creation
            messages.success(request, f"Customer {customer.get_full_name()} created successfully!")
            
            if customer.user and hasattr(form, 'generated_password'):
                # Store credentials in session to display on detail page
                request.session['new_customer_credentials'] = {
                    'customer_id': customer.id,
                    'username': form.generated_username,
                    'password': form.generated_password,
                    'email': customer.email
                }
                return redirect("customers:customer_detail", pk=customer.pk)
            elif customer.user:
                messages.info(request, "Customer will receive an email with instructions to set their password.")
            
            return redirect("customers:customer_detail", pk=customer.pk)
    else:
        form = CustomerWithUserForm(tenant=request.tenant)
    
    return render(request, "customers/form.html", {
        "form": form,
        "title": "Create Customer",
        "active_tab": "customers",
    })


@login_required
@tenant_required
@permission_required('customers.change_customer_basic', raise_exception=True)
def customer_update(request, pk):
    """Update an existing customer"""
    customer = get_object_or_404(Customer.objects.filter(tenant=request.tenant), pk=pk)
    
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer, tenant=request.tenant)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer {customer.get_full_name()} updated successfully!")
            return redirect("customers:customer_detail", pk=customer.pk)
    else:
        form = CustomerForm(instance=customer, tenant=request.tenant)
    
    return render(request, "customers/form.html", {
        "form": form,
        "customer": customer,
        "title": "Update Customer",
        "active_tab": "customers",
    })


@login_required
@tenant_required
@permission_required('customers.remove_customer', raise_exception=True)
def customer_delete(request, pk):
    """Delete a customer"""
    customer = get_object_or_404(Customer.objects.filter(tenant=request.tenant), pk=pk)
    
    if request.method == "POST":
        customer_name = customer.get_full_name()
        customer.delete()
        messages.success(request, f"Customer {customer_name} deleted successfully!")
        return redirect("customers:customer_list")
    
    return render(request, "customers/confirm_delete.html", {
        "customer": customer,
        "active_tab": "customers",
    })


@login_required
@tenant_required
@require_http_methods(["GET"])
def customer_quick_stats(request):
    """Return quick statistics for customers"""
    stats = {
        "total": Customer.objects.filter(tenant=request.tenant).count(),
        "active": Customer.objects.filter(tenant=request.tenant, status=Customer.ACTIVE).count(),
        "inactive": Customer.objects.filter(tenant=request.tenant, status=Customer.INACTIVE).count(),
        "suspended": Customer.objects.filter(tenant=request.tenant, status=Customer.SUSPENDED).count(),
    }
    return JsonResponse(stats)


@login_required
@tenant_required
def customer_coordinates_api(request):
    """API endpoint to get all customer coordinates for mapping"""
    customers = Customer.objects.filter(
        tenant=request.tenant,
        latitude__isnull=False, 
        longitude__isnull=False
    ).values(
        'id', 'first_name', 'last_name', 'latitude', 'longitude', 
        'status', 'street_address', 'barangay__name'
    )
    
    return JsonResponse({
        'customers': list(customers),
        'total': customers.count()
    })
