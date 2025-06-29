from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from apps.audit_logs.models import AuditLogEntry
from apps.users.models import CustomUser


ACTION_FLAGS = {
    ADDITION: 'Created',
    CHANGE: 'Updated', 
    DELETION: 'Deleted'
}


@login_required
@permission_required('admin.view_logentry', raise_exception=True)
def audit_log_list(request):
    """List all audit log entries with filtering"""
    
    # Get all log entries with related data
    logs = LogEntry.objects.select_related(
        'user', 'content_type', 'audit_metadata'
    ).order_by('-action_time')
    
    # Set default date range if not provided
    today = timezone.now().date()
    three_days_ago = today - timedelta(days=3)
    
    # Filter by user
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Filter by action
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action_flag=action)
    
    # Filter by content type
    content_type_id = request.GET.get('content_type')
    if content_type_id:
        logs = logs.filter(content_type_id=content_type_id)
    
    # Filter by date range - use defaults if not provided
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # If no date filters are provided at all, use the 3-day default
    if not date_from and not date_to and not request.GET.get('search') and not user_id and not action and not content_type_id:
        date_from = three_days_ago.strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(action_time__gte=date_from_obj)
        except ValueError:
            date_from = None
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            logs = logs.filter(action_time__lte=date_to_obj)
        except ValueError:
            date_to = None
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        logs = logs.filter(
            Q(object_repr__icontains=search) |
            Q(change_message__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    # Get filter options
    users = CustomUser.objects.filter(
        is_active=True
    ).order_by('first_name', 'last_name')
    
    content_types = ContentType.objects.filter(
        logentry__isnull=False
    ).distinct().order_by('app_label', 'model')
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add action flag labels
    for log in page_obj:
        log.action_label = ACTION_FLAGS.get(log.action_flag, 'Unknown')
    
    context = {
        'page_obj': page_obj,
        'users': users,
        'content_types': content_types,
        'action_flags': [(ADDITION, 'Created'), (CHANGE, 'Updated'), (DELETION, 'Deleted')],
        'selected_user': user_id,
        'selected_action': action,
        'selected_content_type': content_type_id,
        'date_from': date_from or '',
        'date_to': date_to or '',
        'search': search or '',
        'total_count': logs.count(),
        'active_tab': 'audit-logs',
    }
    
    return render(request, 'audit_logs/audit_log_list.html', context)


@login_required
@permission_required('admin.view_logentry', raise_exception=True)
def export_audit_logs(request):
    """Export audit logs to CSV"""
    
    # Get the same filtered queryset as the list view
    logs = LogEntry.objects.select_related(
        'user', 'content_type', 'audit_metadata'
    ).order_by('-action_time')
    
    # Set default date range if not provided
    today = timezone.now().date()
    three_days_ago = today - timedelta(days=3)
    
    # Apply the same filters
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action_flag=action)
    
    content_type_id = request.GET.get('content_type')
    if content_type_id:
        logs = logs.filter(content_type_id=content_type_id)
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # If no date filters are provided at all, use the 3-day default
    if not date_from and not date_to and not request.GET.get('search') and not user_id and not action and not content_type_id:
        date_from = three_days_ago.strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(action_time__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            logs = logs.filter(action_time__lte=date_to_obj)
        except ValueError:
            pass
    
    search = request.GET.get('search')
    if search:
        logs = logs.filter(
            Q(object_repr__icontains=search) |
            Q(change_message__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date/Time',
        'User',
        'Action',
        'Object Type',
        'Object',
        'Details',
        'IP Address',
        'User Agent'
    ])
    
    for log in logs[:10000]:  # Limit to 10k records for performance
        writer.writerow([
            log.action_time.strftime('%Y-%m-%d %H:%M:%S'),
            f"{log.user.get_full_name()} ({log.user.username})" if log.user else 'System',
            ACTION_FLAGS.get(log.action_flag, 'Unknown'),
            f"{log.content_type.app_label}.{log.content_type.model}",
            log.object_repr,
            log.change_message,
            log.audit_metadata.ip_address if hasattr(log, 'audit_metadata') else '',
            log.audit_metadata.user_agent[:50] if hasattr(log, 'audit_metadata') else ''
        ])
    
    return response
