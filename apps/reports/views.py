from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta, date
import csv
from decimal import Decimal

from apps.customer_subscriptions.models import CustomerSubscription
from apps.customers.models import Customer
from apps.customer_installations.models import CustomerInstallation
from apps.barangays.models import Barangay


@login_required
def reports_dashboard(request):
    """Main reports dashboard showing available reports."""
    context = {
        'active_tab': 'reports',
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
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
    
    # Revenue by barangay
    barangay_revenue = subscriptions.values(
        'customer_installation__customer__barangay__name'
    ).annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')[:10]  # Top 10 barangays
    
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
