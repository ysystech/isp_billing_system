from django.urls import path
from apps.routers import views

app_name = "routers"

urlpatterns = [
    path("", views.router_list, name="list"),
    path("create/", views.router_create, name="create"),
    path("<int:pk>/", views.router_detail, name="detail"),
    path("<int:pk>/update/", views.router_update, name="update"),
    path("<int:pk>/delete/", views.router_delete, name="delete"),
    path("stats/", views.router_quick_stats, name="stats"),
]
