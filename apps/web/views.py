from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models
from django.contrib import messages

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
        # For now, redirect to the dashboard URL instead of rendering inline
        # This avoids any potential issues with the dashboard view
        return redirect('dashboard:home')
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
