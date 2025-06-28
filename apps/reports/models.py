# Reports app models
from django.db import models


class ReportPermission(models.Model):
    """
    Proxy model to hold report-related permissions.
    This model doesn't create a database table, it's just for permissions.
    """
    
    class Meta:
        managed = False  # Don't create a database table
        default_permissions = []  # Don't create default add/change/delete permissions
        permissions = [
            # Operational Reports
            ("view_daily_collection_report", "Can view daily collection report"),
            ("view_subscription_expiry_report", "Can view subscription expiry report"),
            ("export_operational_reports", "Can export operational reports"),
            
            # Business Intelligence Reports
            ("view_monthly_revenue_report", "Can view monthly revenue report"),
            ("view_ticket_analysis_report", "Can view ticket analysis report"),
            ("view_technician_performance_report", "Can view technician performance report"),
            ("view_customer_acquisition_report", "Can view customer acquisition report"),
            ("view_payment_behavior_report", "Can view payment behavior report"),
            ("export_business_reports", "Can export business intelligence reports"),
            
            # Strategic Planning
            ("view_area_performance_dashboard", "Can view area performance dashboard"),
            ("view_financial_dashboard", "Can view financial dashboard"),
            ("access_advanced_analytics", "Can access advanced analytics"),
            
            # Report Management
            ("schedule_reports", "Can schedule automated reports"),
            ("customize_report_parameters", "Can customize report parameters"),
        ]
