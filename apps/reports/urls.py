from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('daily-collection/', views.daily_collection_report, name='daily_collection'),
    path('subscription-expiry/', views.subscription_expiry_report, name='subscription_expiry'),
    path('monthly-revenue/', views.monthly_revenue_report, name='monthly_revenue'),
]
