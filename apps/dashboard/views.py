from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import models
from django.template.response import TemplateResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.forms import DateRangeForm
from apps.dashboard.serializers import UserSignupStatsSerializer
from apps.dashboard.services import get_user_signups
from apps.users.models import CustomUser
from apps.customers.models import Customer
from apps.barangays.models import Barangay
from apps.routers.models import Router
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation


def _string_to_date(date_str: str) -> datetime.date:
    date_format = "%Y-%m-%d"
    return datetime.strptime(date_str, date_format).date()


@login_required
@staff_member_required
def dashboard(request):
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
    
    return TemplateResponse(
        request,
        "dashboard/user_dashboard.html",
        context={
            "active_tab": "project-dashboard",
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
        },
    )


class UserSignupStatsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=None, responses=UserSignupStatsSerializer(many=True))
    def get(self, request):
        serializer = UserSignupStatsSerializer(get_user_signups(), many=True)
        return Response(serializer.data)
