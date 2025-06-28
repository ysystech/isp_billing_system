from django.urls import path
from . import views

app_name = 'customer_subscriptions'

urlpatterns = [
    # Main views
    path('', views.subscription_list, name='subscription_list'),
    path('active/', views.active_subscriptions, name='active_subscriptions'),
    path('create/', views.subscription_create, name='subscription_create'),
    path('<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('<int:pk>/cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('<int:subscription_id>/receipt/', views.generate_receipt, name='generate_receipt'),
    path('customer/<int:customer_id>/history/', views.customer_payment_history, name='payment_history'),
    
    # API endpoints
    path('api/latest-subscription/', views.api_get_latest_subscription, name='api_latest_subscription'),
    path('api/calculate-preview/', views.api_calculate_preview, name='api_calculate_preview'),
    path('api/plan-price/', views.api_get_plan_price, name='api_plan_price'),
]
