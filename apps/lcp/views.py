from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
from .models import LCP, Splitter, NAP
from .forms import LCPForm, SplitterForm, NAPForm


@login_required
@permission_required('lcp.view_lcp_list', raise_exception=True)
def lcp_list(request):
    lcps = LCP.objects.select_related('barangay').annotate(
        splitter_count=Count('splitters'),
        nap_count=Count('splitters__naps')
    ).order_by('code')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        lcps = lcps.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(barangay__name__icontains=search_query)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        lcps = lcps.filter(is_active=True)
    elif status == 'inactive':
        lcps = lcps.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(lcps, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status': status,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/lcp_list.html', context)


@login_required
@permission_required('lcp.view_lcp_detail', raise_exception=True)
def lcp_detail(request, pk):
    lcp = get_object_or_404(LCP.objects.select_related('barangay'), pk=pk)
    splitters = lcp.splitters.annotate(nap_count=Count('naps')).order_by('code')
    
    context = {
        'lcp': lcp,
        'splitters': splitters,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/lcp_detail.html', context)


@login_required
@permission_required('lcp.add_lcp', raise_exception=True)
def lcp_create(request):
    if request.method == 'POST':
        form = LCPForm(request.POST)
        if form.is_valid():
            lcp = form.save()
            messages.success(request, f'LCP {lcp.code} created successfully!')
            return redirect('lcp:lcp_detail', pk=lcp.pk)
    else:
        form = LCPForm()
    
    context = {
        'form': form,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/lcp_form.html', context)


@login_required
@permission_required('lcp.manage_lcp_infrastructure', raise_exception=True)
def lcp_edit(request, pk):
    lcp = get_object_or_404(LCP, pk=pk)
    
    if request.method == 'POST':
        form = LCPForm(request.POST, instance=lcp)
        if form.is_valid():
            lcp = form.save()
            messages.success(request, f'LCP {lcp.code} updated successfully!')
            return redirect('lcp:lcp_detail', pk=lcp.pk)
    else:
        form = LCPForm(instance=lcp)
    
    context = {
        'form': form,
        'lcp': lcp,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/lcp_form.html', context)


@login_required
@permission_required('lcp.manage_lcp_infrastructure', raise_exception=True)
def lcp_delete(request, pk):
    lcp = get_object_or_404(LCP, pk=pk)
    
    if request.method == 'POST':
        code = lcp.code
        lcp.delete()
        messages.success(request, f'LCP {code} deleted successfully!')
        return redirect('lcp:lcp_list')
    
    context = {
        'lcp': lcp,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/lcp_confirm_delete.html', context)


# Splitter views
@login_required
@permission_required('lcp.add_lcp', raise_exception=True)
def splitter_create(request, lcp_pk):
    lcp = get_object_or_404(LCP, pk=lcp_pk)
    
    if request.method == 'POST':
        form = SplitterForm(request.POST)
        if form.is_valid():
            splitter = form.save(commit=False)
            splitter.lcp = lcp
            splitter.save()
            messages.success(request, f'Splitter {splitter.code} created successfully!')
            return redirect('lcp:lcp_detail', pk=lcp.pk)
    else:
        form = SplitterForm()
    
    context = {
        'form': form,
        'lcp': lcp,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/splitter_form.html', context)


@login_required
@permission_required('lcp.manage_lcp_infrastructure', raise_exception=True)
def splitter_edit(request, pk):
    splitter = get_object_or_404(Splitter.objects.select_related('lcp'), pk=pk)
    
    if request.method == 'POST':
        form = SplitterForm(request.POST, instance=splitter)
        if form.is_valid():
            splitter = form.save()
            messages.success(request, f'Splitter {splitter.code} updated successfully!')
            return redirect('lcp:lcp_detail', pk=splitter.lcp.pk)
    else:
        form = SplitterForm(instance=splitter)
    
    context = {
        'form': form,
        'splitter': splitter,
        'lcp': splitter.lcp,  # Add this line
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/splitter_form.html', context)


@login_required
@permission_required('lcp.manage_lcp_infrastructure', raise_exception=True)
def splitter_delete(request, pk):
    splitter = get_object_or_404(Splitter.objects.select_related('lcp'), pk=pk)
    lcp = splitter.lcp
    
    if request.method == 'POST':
        code = splitter.code
        splitter.delete()
        messages.success(request, f'Splitter {code} deleted successfully!')
        return redirect('lcp:lcp_detail', pk=lcp.pk)
    
    context = {
        'splitter': splitter,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/splitter_confirm_delete.html', context)


# NAP views
@login_required
@permission_required('lcp.add_lcp', raise_exception=True)
def nap_create(request, splitter_pk):
    splitter = get_object_or_404(Splitter.objects.select_related('lcp'), pk=splitter_pk)
    
    if request.method == 'POST':
        form = NAPForm(request.POST, splitter=splitter)
        if form.is_valid():
            nap = form.save(commit=False)
            nap.splitter = splitter
            nap.save()
            messages.success(request, f'NAP {nap.code} created successfully!')
            return redirect('lcp:lcp_detail', pk=splitter.lcp.pk)
    else:
        form = NAPForm(splitter=splitter)
    
    context = {
        'form': form,
        'splitter': splitter,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/nap_form.html', context)


@login_required
@permission_required('lcp.manage_lcp_infrastructure', raise_exception=True)
def nap_edit(request, pk):
    nap = get_object_or_404(NAP.objects.select_related('splitter__lcp'), pk=pk)
    
    if request.method == 'POST':
        form = NAPForm(request.POST, instance=nap, splitter=nap.splitter)
        if form.is_valid():
            nap = form.save()
            messages.success(request, f'NAP {nap.code} updated successfully!')
            return redirect('lcp:lcp_detail', pk=nap.splitter.lcp.pk)
    else:
        form = NAPForm(instance=nap, splitter=nap.splitter)
    
    context = {
        'form': form,
        'nap': nap,
        'splitter': nap.splitter,  # Add this line
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/nap_form.html', context)


@login_required
@permission_required('lcp.manage_lcp_infrastructure', raise_exception=True)
def nap_delete(request, pk):
    nap = get_object_or_404(NAP.objects.select_related('splitter__lcp'), pk=pk)
    lcp = nap.splitter.lcp
    
    if request.method == 'POST':
        code = nap.code
        nap.delete()
        messages.success(request, f'NAP {code} deleted successfully!')
        return redirect('lcp:lcp_detail', pk=lcp.pk)
    
    context = {
        'nap': nap,
        'active_tab': 'lcp',
    }
    return render(request, 'lcp/nap_confirm_delete.html', context)



# API Views for hierarchical selection
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@login_required
@permission_required('lcp.view_lcp_list', raise_exception=True)
@require_http_methods(["GET"])
def api_get_lcps(request):
    """Get all active LCPs for dropdown selection."""
    lcps = LCP.objects.filter(is_active=True).values('id', 'name', 'code').order_by('code')
    return JsonResponse(list(lcps), safe=False)


@login_required
@permission_required('lcp.view_lcp_list', raise_exception=True)
@require_http_methods(["GET"])
def api_get_splitters(request, lcp_id):
    """Get all splitters for a specific LCP."""
    splitters = Splitter.objects.filter(lcp_id=lcp_id).annotate(
        nap_count=Count('naps')
    )
    
    # Build the response with calculated properties
    splitter_list = []
    for splitter in splitters:
        splitter_data = {
            'id': splitter.id,
            'code': splitter.code,
            'type': splitter.type,
            'port_capacity': splitter.port_capacity,  # This is a property
            'nap_count': splitter.naps.count(),
            'used_ports': splitter.used_ports,  # This is a property
            'available_ports': splitter.available_ports  # This is a property
        }
        splitter_list.append(splitter_data)
    
    return JsonResponse(splitter_list, safe=False)


@login_required
@permission_required('lcp.view_lcp_list', raise_exception=True)
@require_http_methods(["GET"])
def api_get_naps(request, splitter_id):
    """Get all NAPs for a specific splitter."""
    naps = NAP.objects.filter(splitter_id=splitter_id, is_active=True)
    
    # Build the response with calculated properties
    nap_list = []
    for nap in naps:
        nap_data = {
            'id': nap.id,
            'name': nap.name,
            'code': nap.code,
            'port_capacity': nap.port_capacity,  # This is a field
            'used_ports': nap.used_ports,  # This is a property
            'available_ports': nap.available_ports  # This is a property
        }
        nap_list.append(nap_data)
    
    return JsonResponse(nap_list, safe=False)


@login_required
@permission_required('lcp.view_lcp_list', raise_exception=True)
@require_http_methods(["GET"])
def api_get_nap_hierarchy(request, nap_id):
    """Get the full hierarchy for a specific NAP (for edit mode)."""
    nap = get_object_or_404(NAP.objects.select_related('splitter__lcp'), id=nap_id)
    
    hierarchy = {
        'lcp_id': nap.splitter.lcp.id,
        'splitter_id': nap.splitter.id,
        'nap_id': nap.id,
        'lcp_name': nap.splitter.lcp.name,
        'splitter_code': nap.splitter.code,
        'nap_name': nap.name
    }
    
    return JsonResponse(hierarchy)
