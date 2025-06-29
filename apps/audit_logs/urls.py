from django.urls import path
from . import views

app_name = 'audit_logs'

urlpatterns = [
    path('', views.audit_log_list, name='list'),
    path('export/', views.export_audit_logs, name='export'),
]
