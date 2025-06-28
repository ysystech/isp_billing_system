from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    # Main views
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/update/', views.ticket_update, name='ticket_update'),
    
    # Quick actions
    path('<int:pk>/assign/', views.ticket_quick_assign, name='ticket_quick_assign'),
    path('<int:pk>/status/', views.ticket_update_status, name='ticket_update_status'),
    
    # AJAX endpoints
    path('ajax/search-customers/', views.ajax_search_customers, name='ajax_search_customers'),
    path('ajax/customer-installations/', views.ajax_get_customer_installations, name='ajax_get_customer_installations'),
]
