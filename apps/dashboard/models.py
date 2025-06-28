# Dashboard app models
from django.db import models


class DashboardPermission(models.Model):
    """
    Proxy model to hold dashboard permissions.
    This model doesn't create a database table, it's just for permissions.
    """
    
    class Meta:
        managed = False  # Don't create a database table
        default_permissions = []  # Don't create default add/change/delete permissions
        permissions = [
            ("view_dashboard", "Can view main dashboard"),
            ("view_customer_statistics", "Can view customer statistics"),
            ("view_infrastructure_statistics", "Can view infrastructure statistics"),
            ("view_financial_statistics", "Can view financial statistics"),
            ("view_system_statistics", "Can view system statistics"),
        ]
