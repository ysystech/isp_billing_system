from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from apps.routers.models import Router
from apps.routers.forms import RouterForm


@login_required
def router_list(request):
    """List all routers with search and pagination"""
    routers = Router.objects.all()
    
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
def router_detail(request, pk):
    """View router details"""
    router = get_object_or_404(Router, pk=pk)
    
    context = {
        "router": router,
        "active_tab": "routers",
    }
    
    return render(request, "routers/router_detail.html", context)


@login_required
def router_create(request):
    """Create a new router"""
    if request.method == "POST":
        form = RouterForm(request.POST)
        if form.is_valid():
            router = form.save()
            messages.success(request, f"Router '{router}' created successfully!")
            
            if request.headers.get("HX-Request"):
                response = HttpResponse("")
                response["HX-Redirect"] = f"/routers/{router.pk}/"
                return response
            return redirect("routers:detail", pk=router.pk)
    else:
        form = RouterForm()
    
    context = {"form": form, "active_tab": "routers"}
    
    if request.headers.get("HX-Request"):
        return render(request, "routers/partials/router_form.html", context)
    
    return render(request, "routers/router_create.html", context)


@login_required
def router_update(request, pk):
    """Update a router"""
    router = get_object_or_404(Router, pk=pk)
    
    if request.method == "POST":
        form = RouterForm(request.POST, instance=router)
        if form.is_valid():
            router = form.save()
            messages.success(request, f"Router '{router}' updated successfully!")
            
            if request.headers.get("HX-Request"):
                response = HttpResponse("")
                response["HX-Redirect"] = f"/routers/{router.pk}/"
                return response
            return redirect("routers:detail", pk=router.pk)
    else:
        form = RouterForm(instance=router)
    
    context = {
        "form": form,
        "router": router,
        "active_tab": "routers",
    }
    
    if request.headers.get("HX-Request"):
        return render(request, "routers/partials/router_form.html", context)
    
    return render(request, "routers/router_update.html", context)


@login_required
@require_http_methods(["DELETE"])
def router_delete(request, pk):
    """Delete a router"""
    router = get_object_or_404(Router, pk=pk)
    
    router_str = str(router)
    router.delete()
    messages.success(request, f"Router '{router_str}' deleted successfully!")
    
    response = HttpResponse("")
    response["HX-Redirect"] = "/routers/"
    return response


@login_required
def router_quick_stats(request):
    """Get quick statistics for routers (for dashboard)"""
    stats = {
        "total": Router.objects.count(),
    }
    
    return render(request, "routers/partials/router_stats.html", {"stats": stats})
