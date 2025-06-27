from datetime import datetime, timedelta

from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models

from apps.dashboard.forms import DateRangeForm
from apps.dashboard.services import get_user_signups
from apps.dashboard.serializers import UserSignupStatsSerializer
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.routers.models import Router
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation
from apps.customer_subscriptions.models import CustomerSubscription


def _string_to_date(date_str: str) -> datetime.date:
    date_format = "%Y-%m-%d"
    return datetime.strptime(date_str, date_format).date()


def home(request):
    if request.user.is_authenticated:
        # Dashboard functionality - only for superusers
        context = {
            "active_tab": "dashboard",
            "page_title": _("Dashboard"),
        }
        
        if request.user.is_superuser:
            # Date range handling
            end_str = request.GET.get("end")
            end = _string_to_date(end_str) if end_str else timezone.now().date() + timedelta(days=1)
            start_str = request.GET.get("start")
            start = _string_to_date(start_str) if start_str else end - timedelta(days=90)
            serializer = UserSignupStatsSerializer(get_user_signups(start, end), many=True)
            form = DateRangeForm(initial={"start": start, "end": end})
            start_value = CustomUser.objects.filter(date_joined__lt=start).count()
            
            # Get customer statistics
            customer_stats = {
                "total": Customer.objects.count(),
                "active": Customer.objects.filter(status=Customer.ACTIVE).count(),
                "inactive": Customer.objects.filter(status=Customer.INACTIVE).count(),
                "suspended": Customer.objects.filter(status=Customer.SUSPENDED).count(),
            }
            
            # Get barangay statistics
            barangay_stats = {
                "total": Barangay.objects.count(),
                "active": Barangay.objects.filter(is_active=True).count(),
                "with_customers": Barangay.objects.filter(customers__isnull=False).distinct().count(),
            }
            
            # Get router statistics
            router_stats = {
                "total": Router.objects.count(),
            }
            
            # Get subscription plan statistics
            subscription_plan_stats = {
                "total": SubscriptionPlan.objects.count(),
                "active": SubscriptionPlan.objects.filter(is_active=True).count(),
                "inactive": SubscriptionPlan.objects.filter(is_active=False).count(),
            }
            
            # Get user statistics (excluding superusers)
            user_stats = {
                "total": CustomUser.objects.filter(is_superuser=False).count(),
                "cashiers": CustomUser.objects.filter(user_type=CustomUser.CASHIER, is_superuser=False).count(),
                "technicians": CustomUser.objects.filter(user_type=CustomUser.TECHNICIAN, is_superuser=False).count(),
                "active": CustomUser.objects.filter(is_active=True, is_superuser=False).count(),
            }
            
            # Get installation statistics
            installation_stats = {
                "total_installations": CustomerInstallation.objects.count(),
                "active_installations": CustomerInstallation.objects.filter(status='ACTIVE').count(),
            }
            
            # Get subscription statistics
            now = timezone.now()
            three_days_later = now + timedelta(days=3)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            subscription_stats = {
                "active_subscriptions": CustomerSubscription.objects.filter(
                    start_date__lte=now,
                    end_date__gte=now,
                    is_paid=True
                ).count(),
                "expiring_soon": CustomerSubscription.objects.filter(
                    start_date__lte=now,
                    end_date__gte=now,
                    end_date__lte=three_days_later,
                    is_paid=True
                ).count(),
                "todays_revenue": CustomerSubscription.objects.filter(
                    payment_date__gte=today_start,
                    payment_date__lte=now,
                    is_paid=True
                ).aggregate(total=models.Sum('amount_paid'))['total'] or 0,
            }
            
            # Update context with dashboard data
            context.update({
                "signup_data": serializer.data,
                "form": form,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "start_value": start_value,
                "customer_stats": customer_stats,
                "barangay_stats": barangay_stats,
                "router_stats": router_stats,
                "subscription_plan_stats": subscription_plan_stats,
                "user_stats": user_stats,
                "installation_stats": installation_stats,
                "subscription_stats": subscription_stats,
            })
        
        return render(request, "web/app_home.html", context)
    else:
        return render(request, "web/landing_page.html")


def simulate_error(request):
    raise Exception("This is a simulated error.")
