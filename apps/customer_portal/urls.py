from django.urls import path
from . import views

app_name = "customer_portal"

urlpatterns = [
    path("", views.customer_dashboard, name="dashboard"),
    path("profile/", views.customer_profile, name="profile"),
    path("subscriptions/", views.customer_subscriptions, name="subscriptions"),
    path("tickets/", views.customer_tickets, name="tickets"),
    path("tickets/<int:pk>/", views.customer_ticket_detail, name="ticket_detail"),
    path("post-login/", views.post_login_redirect, name="post_login_redirect"),
]
