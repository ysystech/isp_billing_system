from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from apps.tenants.mixins import tenant_required

from apps.routers.models import Router
from apps.routers.forms import RouterForm


@login_required
@permission_required('routers.view_router_list', raise_exception=True)
def router_list(request):
    """List all routers with search and pagination"""
    routers = Router.objects.filter(tenant=request.tenant)
    
    # Search functionality
    search = request.GET.get("search", "")
    if search:
        routers = routers.filter(
            Q(brand__icontains=search) |
            Q(model__icontains=search) |
            Q(serial_number__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(routers, 20)
    page = request.GET.get("page", 1)
    routers_page = paginator.get_page(page)
    
    context = {
        "routers": routers_page,
        "search": search,
        "active_tab": "routers",
    }
    
    # Handle HTMX requests
    if request.headers.get("HX-Request"):
        return render(request, "routers/partials/router_list.html", context)
    
    return render(request, "routers/router_list.html", context)


@login_required
@permission_required('routers.view_router_list', raise_exception=True)
def router_detail(request, pk):
    """View router details"""
    router = get_object_or_404(Router.objects.filter(tenant=request.tenant), pk=pk)
    
    context = {
        "router": router,
        "active_tab": "routers",
    }
    
    return render(request, "routers/router_detail.html", context)


@login_required
@permission_required('routers.add_router', raise_exception=True)
@tenant_required
def router_create(request):
    """Create a new router"""
    if request.method == "POST":
        form = RouterForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            try:
                router = form.save(commit=False)
                router.tenant = request.tenant
                router.save()
                messages.success(request, f"Router '{router}' created successfully!")
                
                if request.headers.get("HX-Request"):
                    response = HttpResponse("")
                    response["HX-Redirect"] = f"/routers/{router.pk}/"
                    return response
                return redirect("routers:detail", pk=router.pk)
            except IntegrityError as e:
                # Handle any database integrity errors
                if 'serial_number' in str(e):
                    form.add_error('serial_number', 'A router with this serial number already exists.')
                elif 'mac_address' in str(e):
                    form.add_error('mac_address', 'A router with this MAC address already exists.')
                else:
                    form.add_error(None, 'An error occurred while saving the router. Please check your input.')
    else:
        form = RouterForm(tenant=request.tenant)
    
    context = {"form": form, "active_tab": "routers"}
    
    if request.headers.get("HX-Request"):
        return render(request, "routers/partials/router_form.html", context)
    
    return render(request, "routers/router_create.html", context)


@login_required
@permission_required('routers.change_router', raise_exception=True)
@tenant_required
def router_update(request, pk):
    """Update a router"""
    router = get_object_or_404(Router.objects.filter(tenant=request.tenant), pk=pk)
    
    if request.method == "POST":
        form = RouterForm(request.POST, instance=router, tenant=request.tenant)
        if form.is_valid():
            try:
                router = form.save(commit=False)
                router.tenant = request.tenant
                router.save()
                messages.success(request, f"Router '{router}' updated successfully!")
                
                if request.headers.get("HX-Request"):
                    response = HttpResponse("")
                    response["HX-Redirect"] = f"/routers/{router.pk}/"
                    return response
                return redirect("routers:detail", pk=router.pk)
            except IntegrityError as e:
                # Handle any database integrity errors
                if 'serial_number' in str(e):
                    form.add_error('serial_number', 'A router with this serial number already exists.')
                elif 'mac_address' in str(e):
                    form.add_error('mac_address', 'A router with this MAC address already exists.')
                else:
                    form.add_error(None, 'An error occurred while saving the router. Please check your input.')
    else:
        form = RouterForm(instance=router, tenant=request.tenant)
    
    context = {
        "form": form,
        "router": router,
        "active_tab": "routers",
    }
    
    if request.headers.get("HX-Request"):
        return render(request, "routers/partials/router_form.html", context)
    
    return render(request, "routers/router_update.html", context)


@login_required
@permission_required('routers.delete_router', raise_exception=True)
@require_http_methods(["DELETE"])
def router_delete(request, pk):
    """Delete a router"""
    router = get_object_or_404(Router.objects.filter(tenant=request.tenant), pk=pk)
    
    router_str = str(router)
    router.delete()
    messages.success(request, f"Router '{router_str}' deleted successfully!")
    
    response = HttpResponse("")
    response["HX-Redirect"] = "/routers/"
    return response


@login_required
@permission_required('routers.view_router_list', raise_exception=True)
def router_quick_stats(request):
    """Get quick statistics for routers (for dashboard)"""
    stats = {
        "total": Router.objects.count(),
    }
    
    return render(request, "routers/partials/router_stats.html", {"stats": stats})
