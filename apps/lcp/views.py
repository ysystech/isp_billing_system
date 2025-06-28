from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.urls import reverse
from .models import LCP, Splitter, NAP
from .forms import LCPForm, SplitterForm, NAPForm


def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
@user_passes_test(is_superuser)
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
