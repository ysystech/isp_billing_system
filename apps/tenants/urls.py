from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('settings/', views.tenant_settings, name='settings'),
]
