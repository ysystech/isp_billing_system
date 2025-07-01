from datetime import datetime, timedelta
from apps.tenants.mixins import tenant_required

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import models
from django.template.response import TemplateResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
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
from apps.tenants.models import Tenant


def _string_to_date(date_str: str) -> datetime.date:
    date_format = "%Y-%m-%d"
    return datetime.strptime(date_str, date_format).date()


@login_required
def dashboard(request):
    """
    Dashboard view that handles cases where user might not have tenant or staff access
    """
    # Check if user has a tenant
    if not hasattr(request.user, 'tenant') or not request.user.tenant:
        # Try to assign user to a default tenant or create one
        try:
            # Get or create default tenant
            default_tenant, created = Tenant.objects.get_or_create(
                name="Default ISP",
                defaults={'is_active': True}
            )
            
            # Assign user to tenant
            request.user.tenant = default_tenant
            request.user.save()
            
            # Set tenant in request for this session
            request.tenant = default_tenant
            
            if created:
                messages.info(request, _("Welcome! A default company has been created for you."))
        except Exception as e:
            messages.error(request, _("Unable to set up your account. Please contact support."))
            return redirect('users:user_profile')
    else:
        request.tenant = request.user.tenant
    
    # Check if user is staff or tenant owner
    if not request.user.is_staff and not getattr(request.user, 'is_tenant_owner', False):
        # For non-staff/non-owner users, show a simplified dashboard or redirect
        messages.info(request, _("You need staff privileges to access the full dashboard."))
        return redirect('users:user_profile')
    
    # Regular dashboard logic
    end_str = request.GET.get("end")
    end = _string_to_date(end_str) if end_str else timezone.now().date() + timedelta(days=1)
    start_str = request.GET.get("start")
    start = _string_to_date(start_str) if start_str else end - timedelta(days=90)
    
    # Get user signups for this tenant
    signup_data = (
        CustomUser.objects.filter(
            tenant=request.tenant,
            date_joined__gte=start,
            date_joined__lte=end
        )
        .annotate(date=models.functions.TruncDate("date_joined"))
        .values("date")
        .annotate(count=models.Count("id"))
        .order_by("date")
    )
    
    serializer = UserSignupStatsSerializer(signup_data, many=True)
    form = DateRangeForm(initial={"start": start, "end": end})
    start_value = CustomUser.objects.filter(tenant=request.tenant, date_joined__lt=start).count()
    
    # Get statistics with safe defaults
    customer_stats = {
        "total": Customer.objects.filter(tenant=request.tenant).count(),
        "active": Customer.objects.filter(tenant=request.tenant, status=Customer.ACTIVE).count(),
        "inactive": Customer.objects.filter(tenant=request.tenant, status=Customer.INACTIVE).count(),
        "suspended": Customer.objects.filter(tenant=request.tenant, status=Customer.SUSPENDED).count(),
    }
    
    barangay_stats = {
        "total": Barangay.objects.filter(tenant=request.tenant).count(),
        "active": Barangay.objects.filter(tenant=request.tenant, is_active=True).count(),
        "with_customers": Barangay.objects.filter(tenant=request.tenant, customers__isnull=False).distinct().count(),
    }
    
    router_stats = {
        "total": Router.objects.filter(tenant=request.tenant).count(),
    }
    
    subscription_plan_stats = {
        "total": SubscriptionPlan.objects.filter(tenant=request.tenant).count(),
        "active": SubscriptionPlan.objects.filter(tenant=request.tenant, is_active=True).count(),
        "inactive": SubscriptionPlan.objects.filter(tenant=request.tenant, is_active=False).count(),
    }
    
    user_stats = {
        "total": CustomUser.objects.filter(tenant=request.tenant, is_superuser=False).count(),
        "active": CustomUser.objects.filter(tenant=request.tenant, is_active=True, is_superuser=False).count(),
        "inactive": CustomUser.objects.filter(tenant=request.tenant, is_active=False, is_superuser=False).count(),
    }
    
    installation_stats = {
        "total_installations": CustomerInstallation.objects.filter(tenant=request.tenant).count(),
        "active_installations": CustomerInstallation.objects.filter(tenant=request.tenant, status='ACTIVE').count(),
    }
    
    return render(
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
        # Get tenant from request
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({"error": "Tenant not found"}, status=400)
        
        # Get signup stats for this tenant
        start = timezone.now().date() - timedelta(days=90)
        end = timezone.now().date() + timedelta(days=1)
        
        # Filter users by tenant
        data = (
            CustomUser.objects.filter(
                tenant=tenant,
                date_joined__gte=start, 
                date_joined__lte=end
            )
            .annotate(date=models.functions.TruncDate("date_joined"))
            .values("date")
            .annotate(count=models.Count("id"))
            .order_by("date")
        )
        
        serializer = UserSignupStatsSerializer(data, many=True)
        return Response(serializer.data)
