"""
URL configuration for the roles app.
"""
from django.urls import path
from . import views

app_name = 'roles'

urlpatterns = [
    path('', views.role_list, name='role_list'),
    path('create/', views.role_create, name='role_create'),
    path('<int:pk>/', views.role_detail, name='role_detail'),
    path('<int:pk>/edit/', views.role_edit, name='role_edit'),
    path('<int:pk>/delete/', views.role_delete, name='role_delete'),
    path('<int:pk>/permissions/', views.role_permissions, name='role_permissions'),
]
