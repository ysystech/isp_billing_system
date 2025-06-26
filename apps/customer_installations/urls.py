from django.urls import path
from . import views

app_name = 'customer_installations'

urlpatterns = [
    path('', views.installation_list, name='installation_list'),
    path('create/', views.installation_create, name='installation_create'),
    path('<int:pk>/', views.installation_detail, name='installation_detail'),
    path('<int:pk>/update/', views.installation_update, name='installation_update'),
    path('<int:pk>/delete/', views.installation_delete, name='installation_delete'),
]
