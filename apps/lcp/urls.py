from django.urls import path
from . import views

app_name = 'lcp'

urlpatterns = [
    # LCP URLs
    path('', views.lcp_list, name='lcp_list'),
    path('create/', views.lcp_create, name='lcp_create'),
    path('<int:pk>/', views.lcp_detail, name='lcp_detail'),
    path('<int:pk>/edit/', views.lcp_edit, name='lcp_edit'),
    path('<int:pk>/delete/', views.lcp_delete, name='lcp_delete'),
    
    # Splitter URLs
    path('<int:lcp_pk>/splitter/create/', views.splitter_create, name='splitter_create'),
    path('splitter/<int:pk>/edit/', views.splitter_edit, name='splitter_edit'),
    path('splitter/<int:pk>/delete/', views.splitter_delete, name='splitter_delete'),
    
    # NAP URLs
    path('splitter/<int:splitter_pk>/nap/create/', views.nap_create, name='nap_create'),
    path('nap/<int:pk>/edit/', views.nap_edit, name='nap_edit'),
    path('nap/<int:pk>/delete/', views.nap_delete, name='nap_delete'),
]
