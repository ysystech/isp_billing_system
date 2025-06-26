from django.urls import path
from . import views

app_name = 'customer_subscriptions'

urlpatterns = [
    path('', views.subscription_list, name='subscription_list'),
    path('create/', views.subscription_create, name='subscription_create'),
    path('<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('installation/<int:installation_id>/', views.subscription_by_installation, name='installation_subscriptions'),
    path('expiring/', views.expiring_subscriptions, name='expiring_subscriptions'),
]
