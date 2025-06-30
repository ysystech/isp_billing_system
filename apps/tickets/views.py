from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.tenants.mixins import tenant_required

from .models import Ticket, TicketComment
from .forms import TicketForm, TicketCommentForm, TicketFilterForm
from apps.customers.models import Customer
from apps.customer_installations.models import CustomerInstallation
from apps.users.models import CustomUser


@login_required
@tenant_required
@permission_required('tickets.view_ticket_list', raise_exception=True)
def ticket_list(request):
    """List all tickets with filtering and search."""
    tickets = Ticket.objects.filter(
        tenant=request.tenant
    ).select_related(
        'customer', 'customer_installation', 'reported_by', 'assigned_to'
    ).prefetch_related('comments')
    
    # Apply filters
    filter_form = TicketFilterForm(request.GET, tenant=request.tenant)
    
    if filter_form.is_valid():
        # Status filter
        status = filter_form.cleaned_data.get('status')
        if status:
            tickets = tickets.filter(status=status)
        
        # Priority filter
        priority = filter_form.cleaned_data.get('priority')
        if priority:
            tickets = tickets.filter(priority=priority)
        
        # Assigned to filter
        assigned_to = filter_form.cleaned_data.get('assigned_to')
        if assigned_to:
            tickets = tickets.filter(assigned_to=assigned_to)
        
        # Search
        search = filter_form.cleaned_data.get('search')
        if search:
            tickets = tickets.filter(
                Q(ticket_number__icontains=search) |
                Q(title__icontains=search) |
                Q(customer__first_name__icontains=search) |
                Q(customer__last_name__icontains=search) |
                Q(customer__email__icontains=search)
            )
    
    # Get ticket statistics
    stats = {
        'total': tickets.count(),
        'pending': tickets.filter(status='pending').count(),
        'in_progress': tickets.filter(status__in=['assigned', 'in_progress']).count(),
        'resolved': tickets.filter(status='resolved').count(),
    }
    
    context = {
        'tickets': tickets,
        'filter_form': filter_form,
        'stats': stats,
        'active_tab': 'tickets',
    }
    
    return render(request, 'tickets/ticket_list.html', context)


@login_required
@tenant_required
@permission_required('tickets.create_ticket', raise_exception=True)
def ticket_create(request):
    """Create a new ticket."""
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user, tenant=request.tenant)
        if form.is_valid():
            ticket = form.save(commit=False)

            ticket.tenant = request.tenant

            ticket.save()
            
            # Add initial comment if provided
            initial_comment = request.POST.get('initial_comment')
            if initial_comment:
                TicketComment.objects.create(
                    ticket=ticket,
                    user=request.user,
                    tenant=request.tenant,  # Add tenant
                    comment=f"Ticket created: {initial_comment}"
                )
            
            messages.success(
                request,
                f'Ticket {ticket.ticket_number} created successfully!'
            )
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm(user=request.user, tenant=request.tenant)
        
        # Pre-populate customer if passed in URL
        customer_id = request.GET.get('customer_id')
        if customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                form.initial['customer'] = customer
                # Also load their installations
                form.fields['customer_installation'].queryset = CustomerInstallation.objects.filter(
                    tenant=request.tenant, 
                    customer=customer
                )
                
            except Customer.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'title': 'Create New Ticket',
        'active_tab': 'tickets',
    }
    
    return render(request, 'tickets/ticket_form.html', context)


@login_required
@tenant_required
@permission_required('tickets.view_ticket_list', raise_exception=True)
def ticket_detail(request, pk):
    """View ticket details and add comments."""
    ticket = get_object_or_404(
        Ticket.objects.filter(tenant=request.tenant).select_related(
            'customer', 'customer_installation', 'reported_by', 'assigned_to'
        ),
        pk=pk
    )
    
    # Get all comments
    comments = ticket.comments.select_related('user').order_by('created_at')
    
    # Handle comment form
    if request.method == 'POST':
        comment_form = TicketCommentForm(request.POST, tenant=request.tenant)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.user = request.user
            comment.tenant = request.tenant  # Add tenant
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        comment_form = TicketCommentForm(tenant=request.tenant)
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
        'active_tab': 'tickets',
    }
    
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
@tenant_required
@permission_required('tickets.edit_ticket', raise_exception=True)
def ticket_update(request, pk):
    """Update ticket details."""
    ticket = get_object_or_404(Ticket.objects.filter(tenant=request.tenant), pk=pk)
    
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket, user=request.user, tenant=request.tenant)
        if form.is_valid():
            # Track status changes
            old_status = ticket.status
            ticket = form.save(commit=False)

            ticket.tenant = request.tenant

            ticket.save()
            
            # Add comment for status change
            if old_status != ticket.status:
                TicketComment.objects.create(
                    ticket=ticket,
                    user=request.user,
                    tenant=request.tenant,  # Add tenant
                    comment=f"Status changed from {old_status} to {ticket.status}"
                )
            
            messages.success(request, 'Ticket updated successfully!')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm(instance=ticket, user=request.user, tenant=request.tenant)
        # Load customer installations
        form.fields['customer_installation'].queryset = CustomerInstallation.objects.filter(
            tenant=request.tenant, 
            customer=ticket.customer
        )
        
    
    context = {
        'form': form,
        'ticket': ticket,
        'title': f'Update Ticket {ticket.ticket_number}',
        'active_tab': 'tickets',
    }
    
    return render(request, 'tickets/ticket_form.html', context)


@login_required
@tenant_required
@permission_required('tickets.edit_ticket', raise_exception=True)
@require_POST
def ticket_quick_assign(request, pk):
    """Quick assign ticket to a technician."""
    ticket = get_object_or_404(Ticket.objects.filter(tenant=request.tenant), pk=pk)
    technician_id = request.POST.get('technician_id')
    
    if technician_id:
        try:
            technician = CustomUser.objects.get(pk=technician_id, is_staff=True)
            old_assignee = ticket.assigned_to
            ticket.assigned_to = technician
            
            # Update status if still pending
            if ticket.status == 'pending':
                ticket.status = 'assigned'
            
            ticket.save()
            
            # Add comment
            if old_assignee != technician:
                TicketComment.objects.create(
                    ticket=ticket,
                    user=request.user,
                    tenant=request.tenant,  # Add tenant
                    comment=f"Assigned to {technician.get_full_name()}"
                )
            
            messages.success(request, f'Ticket assigned to {technician.get_full_name()}')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid technician selected')
    
    return redirect('tickets:ticket_list')


@login_required
@tenant_required
@permission_required('tickets.change_ticket_status', raise_exception=True)
@require_POST
def ticket_update_status(request, pk):
    """Quick update ticket status."""
    ticket = get_object_or_404(Ticket.objects.filter(tenant=request.tenant), pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(Ticket.STATUS_CHOICES):
        old_status = ticket.status
        ticket.status = new_status
        
        # Handle resolution
        if new_status == 'resolved':
            ticket.resolved_at = timezone.now()
            resolution_notes = request.POST.get('resolution_notes', '')
            if resolution_notes:
                ticket.resolution_notes = resolution_notes
        
        ticket.save()
        
        # Add comment
        TicketComment.objects.create(
            ticket=ticket,
            user=request.user,
            tenant=request.tenant,  # Add tenant
            comment=f"Status changed from {old_status} to {new_status}"
        )
        
        messages.success(request, f'Ticket status updated to {ticket.get_status_display()}')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('tickets:ticket_detail', pk=ticket.pk)


# AJAX endpoints for dynamic form behavior

@login_required
@tenant_required
@permission_required('tickets.view_ticket_list', raise_exception=True)
def ajax_search_customers(request):
    """AJAX endpoint to search customers."""
    query = request.GET.get('q', '')
    
    if len(query) >= 2:
        customers = Customer.objects.filter(
            tenant=request.tenant
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_primary__icontains=query)
        )[:10]
        
        results = []
        for customer in customers:
            results.append({
                'id': customer.id,
                'text': f"{customer.full_name} - {customer.email} ({customer.phone_primary})",
                'name': customer.full_name,
                'email': customer.email,
                'phone': customer.phone_primary,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


@login_required
@tenant_required
@permission_required('tickets.view_ticket_list', raise_exception=True)
def ajax_get_customer_installations(request):
    """AJAX endpoint to get customer installations."""
    customer_id = request.GET.get('customer_id')
    
    if customer_id:
        installations = CustomerInstallation.objects.filter(tenant=request.tenant, 
            customer_id=customer_id
        ).select_related('nap', 'router')
        
        results = []
        for installation in installations:
            results.append({
                'id': installation.id,
                'text': f"{installation.nap.name} - Port {installation.nap_port} ({installation.get_status_display()})",
                'status': installation.status,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})
