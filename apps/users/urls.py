from django.urls import path

from . import views, views_management

app_name = "users"
urlpatterns = [
    path("profile/", views.profile, name="user_profile"),
    path("profile/upload-image/", views.upload_profile_image, name="upload_profile_image"),
    
    # User management URLs
    path("management/", views_management.user_management_list, name="user_management_list"),
    path("management/create/", views_management.user_management_create, name="user_management_create"),
    path("management/<int:pk>/", views_management.user_management_detail, name="user_management_detail"),
    path("management/<int:pk>/update/", views_management.user_management_update, name="user_management_update"),
    path("management/<int:pk>/delete/", views_management.user_management_delete, name="user_management_delete"),
]
