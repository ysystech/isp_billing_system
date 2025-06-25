from django.urls import path
from apps.barangays import views

app_name = "barangays"

urlpatterns = [
    path("", views.barangay_list, name="list"),
    path("create/", views.barangay_create, name="create"),
    path("<int:pk>/", views.barangay_detail, name="detail"),
    path("<int:pk>/update/", views.barangay_update, name="update"),
    path("<int:pk>/delete/", views.barangay_delete, name="delete"),
    path("stats/", views.barangay_quick_stats, name="stats"),
]
