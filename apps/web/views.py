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
            "active": CustomUser.objects.filter(is_active=True, is_superuser=False).count(),
            "inactive": CustomUser.objects.filter(is_active=False, is_superuser=False).count(),
        }
        
        # Get installation statistics
        installation_stats = {
            "total_installations": CustomerInstallation.objects.count(),
            "active_installations": CustomerInstallation.objects.filter(status='ACTIVE').count(),
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
        })
        
        return render(request, "web/app_home.html", context)
    else:
        # Landing page data
        landing_context = {
            "page_title": _("FiberBill - Prepaid Internet Management System"),
            "page_description": _("Revolutionize your internet service with automated management, seamless connectivity, and effortless troubleshooting."),
            "features": [
                {
                    "icon": "fa-asterisk",
                    "title": _("Auto Connect"),
                    "description": _("Automatically connect/disconnect clients, saving time and ensuring seamless internet access for everyone."),
                    "delay": "100"
                },
                {
                    "icon": "fa-bahai",
                    "title": _("Manage Router"),
                    "description": _("Manage Mikrotik routers effortlessly from our system, optimizing network performance and stability."),
                    "delay": "200"
                },
                {
                    "icon": "fa-certificate",
                    "title": _("Easy Mapping"),
                    "description": _("Visualize your network from LCP to client, simplifying troubleshooting and reducing downtime effectively."),
                    "delay": "300"
                }
            ],
            "services": [
                {
                    "icon": "fa-circle",
                    "title": _("Client Status"),
                    "description": _("Monitor all client statuses at a glance, ensuring smooth operations and quick issue resolution."),
                    "align": "right"
                },
                {
                    "icon": "fa-circle",
                    "title": _("Customer Portal"),
                    "description": _("Provide customers self-service portal, enhancing satisfaction with easy access to account and support."),
                    "align": "right"
                },
                {
                    "icon": "fa-circle",
                    "title": _("Technician Portal"),
                    "description": _("Empower technicians with dedicated portal, streamlining tasks and improving efficiency."),
                    "align": "right"
                },
                {
                    "icon": "fa-circle",
                    "title": _("Auto Reminder"),
                    "description": _("Automated reminders to clients, reducing late payments and improving cash flow."),
                    "align": "left"
                },
                {
                    "icon": "fa-circle",
                    "title": _("Network Mapping"),
                    "description": _("Visualize network from LCP to client location, simplifying troubleshooting and minimizing downtime."),
                    "align": "left"
                },
                {
                    "icon": "fa-circle",
                    "title": _("Mikrotik Router"),
                    "description": _("Seamlessly manage Mikrotik routers, optimizing network performance and ensuring stable connections."),
                    "align": "left"
                }
            ],
            "faqs": [
                {
                    "question": _("What is FiberBill?"),
                    "answer": _("FiberBill is a software solution that automates prepaid internet management, simplifies troubleshooting, and enhances customer experience for internet service providers.")
                },
                {
                    "question": _("How does FiberBill work?"),
                    "answer": _("FiberBill automates prepaid internet, manages clients, maps networks visually, and provides portals for technicians and customers, enhancing efficiency and satisfaction.")
                },
                {
                    "question": _("Who uses FiberBill?"),
                    "answer": _("FiberBill is used by internet service providers to automate prepaid internet, manage clients, and streamline troubleshooting for improved efficiency and customer satisfaction.")
                },
                {
                    "question": _("Is FiberBill secure?"),
                    "answer": _("FiberBill employs advanced security measures, including encryption and access controls, to protect your data and ensure the privacy of your clients.")
                }
            ]
        }
        return render(request, "web/landing_page.html", landing_context)


def simulate_error(request):
    raise Exception("This is a simulated error.")
