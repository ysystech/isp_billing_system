from django.urls import path
from . import views

app_name = 'network'

urlpatterns = [
    path('map/', views.network_map, name='network_map'),
    path('map/data/', views.network_map_data, name='network_map_data'),
    path('hierarchy/', views.network_hierarchy, name='network_hierarchy'),
]
