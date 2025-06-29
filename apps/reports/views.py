from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, Count, Q, F, Min
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta, date
import csv
import json
from decimal import Decimal
from django.db import models

from apps.customer_subscriptions.models import CustomerSubscription
from apps.customers.models import Customer
from apps.customer_installations.models import CustomerInstallation
from apps.barangays.models import Barangay
from apps.users.models import CustomUser
from apps.tickets.models import Ticket, TicketComment
from apps.lcp.models import NAP


@login_required
@permission_required('reports.view_reports_dashboard', raise_exception=True)
def reports_dashboard(request):
    """Main reports dashboard showing available reports."""
    context = {
        'active_tab': 'reports',
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
@permission_required('reports.view_daily_collection_report', raise_exception=True)
def daily_collection_report(request):
    """Daily collection report showing today's payments."""
    # Get date from request or use today
    date_str = request.GET.get('date')
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = timezone.now().date()
    else:
        report_date = timezone.now().date()
    
    # Get subscriptions created on this date
    subscriptions = CustomerSubscription.objects.filter(
        created_at__date=report_date
    ).select_related(
        'customer_installation__customer',
        'subscription_plan',
        'created_by'
    )
    
    # Calculate totals
    total_amount = subscriptions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_count = subscriptions.count()
    
    # Breakdown by subscription type
    type_breakdown = subscriptions.values('subscription_type').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('subscription_type')
    
    # Breakdown by plan
    plan_breakdown = subscriptions.values(
        'subscription_plan__name',
        'subscription_plan__speed'
    ).annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Get yesterday's data for comparison
    yesterday = report_date - timedelta(days=1)
    yesterday_total = CustomerSubscription.objects.filter(
        created_at__date=yesterday
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Get last week same day data
    last_week = report_date - timedelta(days=7)
    last_week_total = CustomerSubscription.objects.filter(
        created_at__date=last_week
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Handle export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="daily_collection_{report_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Daily Collection Report', f'Date: {report_date}'])
        writer.writerow([])
        writer.writerow(['Customer', 'Plan', 'Type', 'Amount', 'Processed By', 'Time'])
        
        for sub in subscriptions:
            writer.writerow([
                sub.customer_installation.customer.full_name,
                sub.subscription_plan.name,
                sub.get_subscription_type_display(),
                sub.amount,
                sub.created_by.get_full_name() if sub.created_by else 'System',
                sub.created_at.strftime('%I:%M %p')
            ])
        
        writer.writerow([])
        writer.writerow(['Total Collections:', f'₱{total_amount}'])
        writer.writerow(['Total Transactions:', total_count])
        
        return response
    
    context = {
        'active_tab': 'reports',
        'report_date': report_date,
        'subscriptions': subscriptions,
        'total_amount': total_amount,
        'total_count': total_count,
        'type_breakdown': type_breakdown,
        'plan_breakdown': plan_breakdown,
        'yesterday_total': yesterday_total,
        'last_week_total': last_week_total,
        'yesterday_change': ((total_amount - yesterday_total) / yesterday_total * 100) if yesterday_total else 0,
        'last_week_change': ((total_amount - last_week_total) / last_week_total * 100) if last_week_total else 0,
    }
    
    return render(request, 'reports/daily_collection.html', context)


@login_required
@permission_required('reports.view_subscription_expiry_report', raise_exception=True)
def subscription_expiry_report(request):
    """Report showing subscriptions due to expire."""
    today = timezone.now()
    
    # Get different expiry groups
    # Due in 3 days (urgent)
    due_3_days = CustomerSubscription.objects.filter(
        status='ACTIVE',
        end_date__date__gt=today.date(),
        end_date__date__lte=(today + timedelta(days=3)).date()
    ).select_related(
        'customer_installation__customer',
        'customer_installation__nap__splitter__lcp',
        'subscription_plan'
    ).order_by('end_date')
    
    # Due in 7 days (regular)
    due_7_days = CustomerSubscription.objects.filter(
        status='ACTIVE',
        end_date__date__gt=(today + timedelta(days=3)).date(),
        end_date__date__lte=(today + timedelta(days=7)).date()
    ).select_related(
        'customer_installation__customer',
        'customer_installation__nap__splitter__lcp',
        'subscription_plan'
    ).order_by('end_date')
    
    # Expired yesterday
    expired_yesterday = CustomerSubscription.objects.filter(
        status='EXPIRED',
        end_date__date=(today - timedelta(days=1)).date()
    ).select_related(
        'customer_installation__customer',
        'customer_installation__nap__splitter__lcp',
        'subscription_plan'
    ).order_by('customer_installation__customer__barangay__name')
    
    # Expired 3+ days (disconnection candidates)
    expired_3_plus = CustomerSubscription.objects.filter(
        status='EXPIRED',
        end_date__date__lte=(today - timedelta(days=3)).date(),
        end_date__date__gte=(today - timedelta(days=30)).date()  # Last 30 days only
    ).select_related(
        'customer_installation__customer',
        'customer_installation__nap__splitter__lcp',
        'subscription_plan'
    ).order_by('-end_date')
    
    # Group by barangay for field visits
    barangay_filter = request.GET.get('barangay')
    if barangay_filter:
        due_3_days = due_3_days.filter(
            customer_installation__customer__barangay_id=barangay_filter
        )
        due_7_days = due_7_days.filter(
            customer_installation__customer__barangay_id=barangay_filter
        )
        expired_yesterday = expired_yesterday.filter(
            customer_installation__customer__barangay_id=barangay_filter
        )
        expired_3_plus = expired_3_plus.filter(
            customer_installation__customer__barangay_id=barangay_filter
        )
    
    # Get all barangays for filter
    barangays = Barangay.objects.filter(is_active=True).order_by('name')
    
    # Handle export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="subscription_expiry_{today.date()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Subscription Expiry Report', f'Generated: {today.strftime("%Y-%m-%d %I:%M %p")}'])
        writer.writerow([])
        
        # Due in 3 days
        writer.writerow(['DUE IN 3 DAYS (URGENT)'])
        writer.writerow(['Customer', 'Phone', 'Area', 'Plan', 'Expires', 'Days Left'])
        for sub in due_3_days:
            days_left = (sub.end_date - today).days
            writer.writerow([
                sub.customer_installation.customer.full_name,
                sub.customer_installation.customer.phone_primary,
                sub.customer_installation.customer.barangay.name,
                sub.subscription_plan.name,
                sub.end_date.strftime('%Y-%m-%d %I:%M %p'),
                days_left
            ])
        
        writer.writerow([])
        # Continue with other sections...
        
        return response
    
    context = {
        'active_tab': 'reports',
        'due_3_days': due_3_days,
        'due_7_days': due_7_days,
        'expired_yesterday': expired_yesterday,
        'expired_3_plus': expired_3_plus,
        'barangays': barangays,
        'selected_barangay': barangay_filter,
        'current_time': today,
    }
    
    return render(request, 'reports/subscription_expiry.html', context)


@login_required
@permission_required('reports.view_monthly_revenue_report', raise_exception=True)
def monthly_revenue_report(request):
    """Monthly revenue analysis report."""
    # Get month and year from request
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    
    try:
        month = int(month)
        year = int(year)
    except ValueError:
        month = timezone.now().month
        year = timezone.now().year
    
    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get subscriptions for this month
    subscriptions = CustomerSubscription.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Calculate totals
    total_revenue = subscriptions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_subscriptions = subscriptions.count()
    
    # Get previous month data
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    prev_start = date(prev_year, prev_month, 1)
    if prev_month == 12:
        prev_end = date(prev_year + 1, 1, 1) - timedelta(days=1)
    else:
        prev_end = date(prev_year, prev_month + 1, 1) - timedelta(days=1)
    
    prev_revenue = CustomerSubscription.objects.filter(
        created_at__date__gte=prev_start,
        created_at__date__lte=prev_end
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate MoM growth
    mom_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
    
    # Get last year same month
    last_year_revenue = CustomerSubscription.objects.filter(
        created_at__date__gte=date(year - 1, month, 1),
        created_at__date__lte=date(year - 1, month, end_date.day)
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate YoY growth
    yoy_growth = ((total_revenue - last_year_revenue) / last_year_revenue * 100) if last_year_revenue else 0
    
    # Revenue by plan
    plan_revenue = subscriptions.values(
        'subscription_plan__name',
        'subscription_plan__speed',
        'subscription_plan__price'
    ).annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Add percentage to plan revenue
    for plan in plan_revenue:
        plan['percentage'] = float(plan['total']) / float(total_revenue) * 100 if total_revenue else 0
    
    # Revenue by barangay
    barangay_revenue = subscriptions.values(
        'customer_installation__customer__barangay__name'
    ).annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')[:10]  # Top 10 barangays
    
    # Add percentage to barangay revenue
    for barangay in barangay_revenue:
        barangay['percentage'] = float(barangay['total']) / float(total_revenue) * 100 if total_revenue else 0
    
    # Daily revenue for chart
    daily_revenue = []
    for day in range(1, end_date.day + 1):
        day_date = date(year, month, day)
        day_revenue = subscriptions.filter(
            created_at__date=day_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        daily_revenue.append({
            'day': day,
            'date': day_date,
            'revenue': float(day_revenue)
        })
    
    # New vs Renewal revenue
    # For simplicity, we'll consider first subscription per customer as new
    customer_first_subs = {}
    all_subs = CustomerSubscription.objects.filter(
        created_at__date__lte=end_date
    ).order_by('created_at').values('customer_installation__customer_id', 'id', 'created_at')
    
    for sub in all_subs:
        customer_id = sub['customer_installation__customer_id']
        if customer_id not in customer_first_subs:
            customer_first_subs[customer_id] = sub['id']
    
    new_revenue = subscriptions.filter(
        id__in=customer_first_subs.values()
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    renewal_revenue = total_revenue - new_revenue
    
    # Average revenue per customer
    unique_customers = subscriptions.values('customer_installation__customer').distinct().count()
    arpu = total_revenue / unique_customers if unique_customers else 0
    
    context = {
        'active_tab': 'reports',
        'month': month,
        'year': year,
        'month_name': date(year, month, 1).strftime('%B'),
        'total_revenue': total_revenue,
        'total_subscriptions': total_subscriptions,
        'prev_revenue': prev_revenue,
        'mom_growth': mom_growth,
        'yoy_growth': yoy_growth,
        'plan_revenue': plan_revenue,
        'barangay_revenue': barangay_revenue,
        'daily_revenue': daily_revenue,
        'new_revenue': new_revenue,
        'renewal_revenue': renewal_revenue,
        'arpu': arpu,
        'unique_customers': unique_customers,
    }
    
    return render(request, 'reports/monthly_revenue.html', context)



@login_required
@permission_required('reports.view_ticket_analysis_report', raise_exception=True)
def ticket_analysis_report(request):
    """Ticket analysis report for service quality insights."""
    from apps.tickets.models import Ticket, TicketComment
    
    # Get date range
    end_date = timezone.now().date()
    days = int(request.GET.get('days', 30))  # Default to last 30 days
    start_date = end_date - timedelta(days=days)
    
    # Get tickets in date range
    tickets = Ticket.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('customer', 'assigned_to', 'customer_installation__customer__barangay')
    
    # Overall statistics
    total_tickets = tickets.count()
    resolved_tickets = tickets.filter(status='resolved').count()
    pending_tickets = tickets.filter(status='pending').count()
    in_progress_tickets = tickets.filter(status__in=['assigned', 'in_progress']).count()
    cancelled_tickets = tickets.filter(status='cancelled').count()
    
    # Calculate resolution rate
    resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets else 0
    
    # Tickets by category
    category_stats = tickets.values('category').annotate(
        count=Count('id'),
        resolved=Count('id', filter=Q(status='resolved')),
        pending=Count('id', filter=Q(status='pending'))
    ).order_by('-count')
    
    # Add display names and calculate resolution rates
    for stat in category_stats:
        stat['display_name'] = dict(Ticket.CATEGORY_CHOICES).get(stat['category'], stat['category'])
        stat['resolution_rate'] = (stat['resolved'] / stat['count'] * 100) if stat['count'] else 0
    
    # Tickets by priority
    priority_stats = tickets.values('priority').annotate(
        count=Count('id'),
        avg_resolution_hours=Count('id')  # Placeholder, we'll calculate this differently
    ).order_by('priority')
    
    # Add display names
    priority_order = {'urgent': 1, 'high': 2, 'medium': 3, 'low': 4}
    priority_stats = sorted(priority_stats, key=lambda x: priority_order.get(x['priority'], 5))
    
    for stat in priority_stats:
        stat['display_name'] = dict(Ticket.PRIORITY_CHOICES).get(stat['priority'], stat['priority'])
        # Calculate average resolution time
        resolved = tickets.filter(priority=stat['priority'], status='resolved', resolved_at__isnull=False)
        if resolved.exists():
            total_hours = sum((t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved)
            stat['avg_resolution_hours'] = round(total_hours / resolved.count(), 1)
        else:
            stat['avg_resolution_hours'] = None
    
    # Tickets by barangay (top 10)
    barangay_stats = tickets.values(
        'customer_installation__customer__barangay__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Tickets by technician performance
    technician_stats = tickets.filter(
        assigned_to__isnull=False
    ).values(
        'assigned_to__first_name',
        'assigned_to__last_name',
        'assigned_to__email'
    ).annotate(
        total=Count('id'),
        resolved=Count('id', filter=Q(status='resolved')),
        pending=Count('id', filter=Q(status__in=['pending', 'assigned', 'in_progress']))
    ).order_by('-total')
    
    # Calculate resolution rate and format names
    for stat in technician_stats:
        stat['name'] = f"{stat['assigned_to__first_name']} {stat['assigned_to__last_name']}"
        stat['resolution_rate'] = (stat['resolved'] / stat['total'] * 100) if stat['total'] else 0
    
    # Common issues (most frequent tickets by customer)
    repeat_customers = tickets.values(
        'customer__id',
        'customer__first_name', 
        'customer__last_name'
    ).annotate(
        ticket_count=Count('id')
    ).filter(ticket_count__gt=1).order_by('-ticket_count')[:10]
    
    # Format customer names
    for customer in repeat_customers:
        customer['name'] = f"{customer['customer__first_name']} {customer['customer__last_name']}"
    
    # Daily ticket trend for chart
    daily_tickets = []
    for i in range(days):
        day_date = start_date + timedelta(days=i)
        day_tickets = tickets.filter(created_at__date=day_date)
        daily_tickets.append({
            'date': day_date.strftime('%Y-%m-%d'),
            'total': day_tickets.count(),
            'resolved': day_tickets.filter(status='resolved').count()
        })
    
    # Response time analysis (urgent tickets)
    urgent_tickets = tickets.filter(priority='urgent', status='resolved', resolved_at__isnull=False)
    if urgent_tickets.exists():
        urgent_response_times = [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in urgent_tickets]
        avg_urgent_response = sum(urgent_response_times) / len(urgent_response_times)
    else:
        avg_urgent_response = 0
    
    # Overdue tickets (based on SLA)
    overdue_tickets = []
    for ticket in tickets.filter(status__in=['pending', 'assigned', 'in_progress']):
        if ticket.is_overdue:
            overdue_tickets.append(ticket)
    
    context = {
        'active_tab': 'reports',
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'total_tickets': total_tickets,
        'resolved_tickets': resolved_tickets,
        'pending_tickets': pending_tickets,
        'in_progress_tickets': in_progress_tickets,
        'cancelled_tickets': cancelled_tickets,
        'resolution_rate': resolution_rate,
        'category_stats': category_stats,
        'priority_stats': priority_stats,
        'barangay_stats': barangay_stats,
        'technician_stats': technician_stats,
        'repeat_customers': repeat_customers,
        'daily_tickets': json.dumps(daily_tickets),  # Convert to JSON for JavaScript
        'avg_urgent_response': avg_urgent_response,
        'overdue_tickets': overdue_tickets[:10],  # Show top 10 overdue
        'overdue_count': len(overdue_tickets),
    }
    
    return render(request, 'reports/ticket_analysis.html', context)



@login_required
@permission_required('reports.view_technician_performance_report', raise_exception=True)
def technician_performance_report(request):
    """Technician performance report for staff efficiency tracking."""
    from apps.tickets.models import Ticket
    from apps.customer_installations.models import CustomerInstallation
    
    # Get date range
    end_date = timezone.now().date()
    days = int(request.GET.get('days', 30))
    start_date = end_date - timedelta(days=days)
    
    # Get all staff users
    technicians = CustomUser.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    
    technician_stats = []
    for tech in technicians:
        # Installations completed
        installations = CustomerInstallation.objects.filter(
            installation_technician=tech,
            installation_date__gte=start_date,
            installation_date__lte=end_date
        )
        
        # Tickets handled
        tickets = Ticket.objects.filter(
            assigned_to=tech,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        resolved_tickets = tickets.filter(status='resolved')
        
        # Calculate average resolution time
        total_resolution_time = 0
        resolution_count = 0
        for ticket in resolved_tickets:
            if ticket.resolved_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                total_resolution_time += resolution_time
                resolution_count += 1
        
        avg_resolution_time = total_resolution_time / resolution_count if resolution_count else 0
        
        # Areas covered (unique barangays)
        installation_areas = installations.values_list(
            'customer__barangay__name', flat=True
        ).distinct()
        
        ticket_areas = tickets.values_list(
            'customer_installation__customer__barangay__name', flat=True
        ).distinct()
        
        areas_covered = set(list(installation_areas) + list(ticket_areas))
        
        technician_stats.append({
            'technician': tech,
            'installations_completed': installations.count(),
            'tickets_assigned': tickets.count(),
            'tickets_resolved': resolved_tickets.count(),
            'tickets_pending': tickets.filter(status__in=['pending', 'assigned', 'in_progress']).count(),
            'resolution_rate': (resolved_tickets.count() / tickets.count() * 100) if tickets.count() else 0,
            'avg_resolution_time': avg_resolution_time,
            'areas_covered': len(areas_covered),
            'area_names': sorted(areas_covered)
        })
    
    # Sort by total activity
    technician_stats.sort(key=lambda x: x['installations_completed'] + x['tickets_resolved'], reverse=True)
    
    # Daily activity chart data
    daily_activity = []
    for i in range(min(days, 30)):  # Limit to 30 days for performance
        day_date = end_date - timedelta(days=i)
        
        day_installations = CustomerInstallation.objects.filter(
            installation_date=day_date
        ).count()
        
        day_tickets = Ticket.objects.filter(
            created_at__date=day_date
        ).count()
        
        daily_activity.append({
            'date': day_date.strftime('%Y-%m-%d'),
            'installations': day_installations,
            'tickets': day_tickets
        })
    
    daily_activity.reverse()
    
    context = {
        'active_tab': 'reports',
        'technician_stats': technician_stats,
        'start_date': start_date,
        'end_date': end_date,
        'days': days,
        'daily_activity': json.dumps(daily_activity),
    }
    
    return render(request, 'reports/technician_performance.html', context)


@login_required
@permission_required('reports.view_customer_acquisition_report', raise_exception=True)
def customer_acquisition_report(request):
    """Customer acquisition report for growth tracking."""
    # Get year
    year = int(request.GET.get('year', timezone.now().year))
    
    # Monthly acquisition data
    monthly_data = []
    for month in range(1, 13):
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # New customers this month
        new_customers = Customer.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Installations this month
        new_installations = CustomerInstallation.objects.filter(
            installation_date__gte=start_date,
            installation_date__lte=end_date
        )
        
        # First subscriptions (activation)
        first_subs = CustomerSubscription.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('customer_installation__customer').annotate(
            first_sub_date=models.Min('created_at')
        )
        
        monthly_data.append({
            'month': month,
            'month_name': date(year, month, 1).strftime('%B'),
            'new_customers': new_customers.count(),
            'new_installations': new_installations.count(),
            'activations': first_subs.count()
        })
    
    # Cumulative growth
    cumulative_customers = 0
    for data in monthly_data:
        cumulative_customers += data['new_customers']
        data['cumulative'] = cumulative_customers
    
    # Acquisition by barangay
    barangay_data = Customer.objects.filter(
        created_at__year=year
    ).values('barangay__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Popular plans for new customers
    # Get first subscription for each customer in the year
    new_customer_ids = Customer.objects.filter(
        created_at__year=year
    ).values_list('id', flat=True)
    
    first_plans = CustomerSubscription.objects.filter(
        customer_installation__customer__in=new_customer_ids
    ).values(
        'customer_installation__customer',
        'subscription_plan__name',
        'subscription_plan__speed'
    ).distinct().values(
        'subscription_plan__name',
        'subscription_plan__speed'
    ).annotate(
        count=Count('customer_installation__customer')
    ).order_by('-count')
    
    # Installation to activation time
    activation_times = []
    installations_with_subs = CustomerInstallation.objects.filter(
        installation_date__year=year,
        subscriptions__isnull=False
    ).distinct()
    
    for installation in installations_with_subs[:100]:  # Sample for performance
        first_sub = installation.subscriptions.order_by('created_at').first()
        if first_sub:
            time_diff = (first_sub.created_at.date() - installation.installation_date).days
            activation_times.append(time_diff)
    
    avg_activation_time = sum(activation_times) / len(activation_times) if activation_times else 0
    
    # Year over year comparison
    prev_year_customers = Customer.objects.filter(
        created_at__year=year-1
    ).count()
    
    current_year_customers = Customer.objects.filter(
        created_at__year=year
    ).count()
    
    yoy_growth = ((current_year_customers - prev_year_customers) / prev_year_customers * 100) if prev_year_customers else 0
    
    context = {
        'active_tab': 'reports',
        'year': year,
        'monthly_data': json.dumps(monthly_data),
        'monthly_data_table': monthly_data,
        'barangay_data': barangay_data,
        'first_plans': first_plans,
        'avg_activation_time': avg_activation_time,
        'total_new_customers': sum(d['new_customers'] for d in monthly_data),
        'total_new_installations': sum(d['new_installations'] for d in monthly_data),
        'yoy_growth': yoy_growth,
        'monthly_average': sum(d['new_customers'] for d in monthly_data) / 12,
    }
    
    return render(request, 'reports/customer_acquisition.html', context)


@login_required
@permission_required('reports.view_payment_behavior_report', raise_exception=True)
def payment_behavior_report(request):
    """Payment behavior report for financial planning."""
    # Get date range
    end_date = timezone.now().date()
    days = int(request.GET.get('days', 90))
    start_date = end_date - timedelta(days=days)
    
    # Get all subscriptions in date range
    subscriptions = CustomerSubscription.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).select_related('customer_installation__customer', 'subscription_plan')
    
    # Payment type distribution
    payment_types = subscriptions.values('subscription_type').annotate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    payment_type_data = []
    for pt in payment_types:
        payment_type_data.append({
            'type': pt['subscription_type'],
            'display': dict(CustomerSubscription.SUBSCRIPTION_TYPES).get(pt['subscription_type']),
            'count': pt['count'],
            'total': pt['total'],
            'percentage': (pt['count'] / subscriptions.count() * 100) if subscriptions.count() else 0
        })
    
    # Renewal patterns - find customers with multiple subscriptions
    customers_with_renewals = subscriptions.values(
        'customer_installation__customer'
    ).annotate(
        subscription_count=Count('id')
    ).filter(subscription_count__gt=1)
    
    # Calculate days before renewal for each customer
    renewal_patterns = []
    for customer_data in customers_with_renewals:
        customer_subs = subscriptions.filter(
            customer_installation__customer=customer_data['customer_installation__customer']
        ).order_by('created_at')
        
        # Check gaps between subscriptions
        prev_sub = None
        for sub in customer_subs:
            if prev_sub and prev_sub.end_date:
                gap_days = (sub.start_date - prev_sub.end_date).days
                renewal_patterns.append({
                    'gap_days': gap_days,
                    'renewed_early': gap_days < 0,
                    'renewed_on_time': -1 <= gap_days <= 1,
                    'renewed_late': gap_days > 1
                })
            prev_sub = sub
    
    # Calculate renewal statistics
    total_renewals = len(renewal_patterns)
    early_renewals = sum(1 for r in renewal_patterns if r['renewed_early'])
    on_time_renewals = sum(1 for r in renewal_patterns if r['renewed_on_time'])
    late_renewals = sum(1 for r in renewal_patterns if r['renewed_late'])
    
    avg_gap_days = sum(r['gap_days'] for r in renewal_patterns) / total_renewals if total_renewals else 0
    
    # Payment amount distribution
    amount_ranges = [
        (0, 500, '₱0-500'),
        (500, 1000, '₱500-1000'),
        (1000, 1500, '₱1000-1500'),
        (1500, 2000, '₱1500-2000'),
        (2000, float('inf'), '₱2000+')
    ]
    
    amount_distribution = []
    for min_amt, max_amt, label in amount_ranges:
        if max_amt == float('inf'):
            count = subscriptions.filter(amount__gte=min_amt).count()
        else:
            count = subscriptions.filter(amount__gte=min_amt, amount__lt=max_amt).count()
        
        amount_distribution.append({
            'range': label,
            'count': count,
            'percentage': (count / subscriptions.count() * 100) if subscriptions.count() else 0
        })
    
    # Custom amount analysis
    custom_subs = subscriptions.filter(subscription_type='custom')
    custom_amounts = list(custom_subs.values_list('amount', flat=True))
    
    if custom_amounts:
        avg_custom_amount = float(sum(custom_amounts) / len(custom_amounts))
        min_custom_amount = float(min(custom_amounts))
        max_custom_amount = float(max(custom_amounts))
    else:
        avg_custom_amount = min_custom_amount = max_custom_amount = 0
    
    # Day of week analysis
    dow_data = []
    for i in range(7):
        dow_subs = subscriptions.filter(created_at__week_day=i+1)  # 1=Sunday, 7=Saturday
        total_amount = dow_subs.aggregate(total=Sum('amount'))['total'] or 0
        dow_data.append({
            'day': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][i],
            'count': dow_subs.count(),
            'total': float(total_amount)  # Convert Decimal to float for JSON serialization
        })
    
    context = {
        'active_tab': 'reports',
        'start_date': start_date,
        'end_date': end_date,
        'days': days,
        'total_subscriptions': subscriptions.count(),
        'total_revenue': subscriptions.aggregate(total=Sum('amount'))['total'] or 0,
        'average_payment': (subscriptions.aggregate(total=Sum('amount'))['total'] or 0) / subscriptions.count() if subscriptions.count() else 0,
        'payment_type_data': payment_type_data,
        'renewal_stats': {
            'total': total_renewals,
            'early': early_renewals,
            'early_pct': (early_renewals / total_renewals * 100) if total_renewals else 0,
            'on_time': on_time_renewals,
            'on_time_pct': (on_time_renewals / total_renewals * 100) if total_renewals else 0,
            'late': late_renewals,
            'late_pct': (late_renewals / total_renewals * 100) if total_renewals else 0,
            'avg_gap_days': avg_gap_days
        },
        'amount_distribution': amount_distribution,
        'custom_stats': {
            'count': custom_subs.count(),
            'avg': avg_custom_amount,
            'min': min_custom_amount,
            'max': max_custom_amount
        },
        'dow_data': json.dumps(dow_data),
    }
    
    return render(request, 'reports/payment_behavior.html', context)


@login_required
@permission_required('reports.view_area_performance_dashboard', raise_exception=True)
def area_performance_dashboard(request):
    """Area performance dashboard for geographic business insights."""
    # Get all active barangays
    barangays = Barangay.objects.filter(is_active=True).order_by('name')
    
    # Selected barangay
    selected_barangay_id = request.GET.get('barangay')
    if selected_barangay_id:
        selected_barangay = get_object_or_404(Barangay, id=selected_barangay_id)
    else:
        selected_barangay = None
    
    # Date range (default last 3 months)
    end_date = timezone.now().date()
    days = 90
    start_date = end_date - timedelta(days=days)
    
    area_stats = []
    
    if selected_barangay:
        # Detailed stats for selected barangay
        customers = Customer.objects.filter(barangay=selected_barangay)
        
        # Revenue
        revenue = CustomerSubscription.objects.filter(
            customer_installation__customer__barangay=selected_barangay,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Active subscriptions
        active_subs = CustomerSubscription.objects.filter(
            customer_installation__customer__barangay=selected_barangay,
            status='ACTIVE'
        ).count()
        
        # Service issues
        tickets = Ticket.objects.filter(
            customer_installation__customer__barangay=selected_barangay,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Infrastructure
        naps_in_area = NAP.objects.filter(
            splitter__lcp__barangay=selected_barangay
        )
        
        total_ports = sum(nap.port_capacity for nap in naps_in_area)
        used_ports = CustomerInstallation.objects.filter(
            nap__in=naps_in_area,
            status='ACTIVE'
        ).count()
        
        # Growth (new customers)
        new_customers = customers.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()
        
        # Monthly trend for selected area
        monthly_trend = []
        for i in range(3):
            month_start = end_date.replace(day=1) - timedelta(days=i*30)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_revenue = CustomerSubscription.objects.filter(
                customer_installation__customer__barangay=selected_barangay,
                created_at__date__gte=month_start,
                created_at__date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_trend.append({
                'month': month_start.strftime('%B'),
                'revenue': float(month_revenue)
            })
        
        monthly_trend.reverse()
        
        selected_stats = {
            'barangay': selected_barangay,
            'total_customers': customers.count(),
            'active_customers': customers.filter(installation__status='ACTIVE').distinct().count(),
            'revenue': revenue,
            'active_subscriptions': active_subs,
            'tickets_total': tickets.count(),
            'tickets_resolved': tickets.filter(status='resolved').count(),
            'tickets_pending': tickets.filter(status__in=['pending', 'assigned', 'in_progress']).count(),
            'total_ports': total_ports,
            'used_ports': used_ports,
            'port_utilization': (used_ports / total_ports * 100) if total_ports else 0,
            'new_customers': new_customers,
            'monthly_trend': json.dumps(monthly_trend),
            'popular_plans': CustomerSubscription.objects.filter(
                customer_installation__customer__barangay=selected_barangay,
                created_at__date__gte=start_date
            ).values('subscription_plan__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
        }
    else:
        # Overview of all areas
        for barangay in barangays:
            customers = Customer.objects.filter(barangay=barangay)
            active_customers = customers.filter(
                installation__status='ACTIVE'
            ).distinct().count()
            
            revenue = CustomerSubscription.objects.filter(
                customer_installation__customer__barangay=barangay,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            tickets = Ticket.objects.filter(
                customer_installation__customer__barangay=barangay,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).count()
            
            # Calculate potential (based on households estimate)
            # This is a rough estimate - you might want to add actual household data
            penetration_rate = (active_customers / 100) * 100  # Assuming 100 households per barangay
            
            area_stats.append({
                'barangay': barangay,
                'total_customers': customers.count(),
                'active_customers': active_customers,
                'revenue': revenue,
                'tickets': tickets,
                'penetration_rate': min(penetration_rate, 100)  # Cap at 100%
            })
        
        # Sort by revenue
        area_stats.sort(key=lambda x: x['revenue'], reverse=True)
        
        selected_stats = None
    
    # Top performing areas (if showing overview)
    if not selected_barangay:
        top_revenue = area_stats[:5] if area_stats else []
        low_penetration = sorted(
            [a for a in area_stats if a['active_customers'] > 0],
            key=lambda x: x['penetration_rate']
        )[:5]
        high_issues = sorted(
            [a for a in area_stats if a['tickets'] > 0],
            key=lambda x: x['tickets'],
            reverse=True
        )[:5]
    else:
        top_revenue = low_penetration = high_issues = []
    
    context = {
        'active_tab': 'reports',
        'barangays': barangays,
        'selected_barangay': selected_barangay,
        'selected_stats': selected_stats,
        'area_stats': area_stats[:20],  # Show top 20 areas in overview
        'top_revenue': top_revenue,
        'low_penetration': low_penetration,
        'high_issues': high_issues,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'reports/area_performance.html', context)
