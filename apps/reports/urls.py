from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('daily-collection/', views.daily_collection_report, name='daily_collection'),
    path('subscription-expiry/', views.subscription_expiry_report, name='subscription_expiry'),
    path('monthly-revenue/', views.monthly_revenue_report, name='monthly_revenue'),
    path('ticket-analysis/', views.ticket_analysis_report, name='ticket_analysis'),
    path('technician-performance/', views.technician_performance_report, name='technician_performance'),
    path('customer-acquisition/', views.customer_acquisition_report, name='customer_acquisition'),
    path('payment-behavior/', views.payment_behavior_report, name='payment_behavior'),
    path('area-performance/', views.area_performance_dashboard, name='area_performance'),
]
