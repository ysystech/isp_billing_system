from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.subscription_plan_list, name='subscription_plan_list'),
    path('plans/create/', views.subscription_plan_create, name='subscription_plan_create'),
    path('plans/<int:pk>/', views.subscription_plan_detail, name='subscription_plan_detail'),
    path('plans/<int:pk>/update/', views.subscription_plan_update, name='subscription_plan_update'),
    path('plans/<int:pk>/delete/', views.subscription_plan_delete, name='subscription_plan_delete'),
]
