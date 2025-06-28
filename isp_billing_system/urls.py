"""ISP Billing System URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/stable/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.web.sitemaps import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap(),
}

urlpatterns = [
    # redirect Django admin login to main login page
    path("admin/login/", RedirectView.as_view(pattern_name="account_login")),
    path("admin/", admin.site.urls),
    # path("dashboard/", include("apps.dashboard.urls")),  # Dashboard functionality moved to home page
    path("barangays/", include("apps.barangays.urls")),
    path("routers/", include("apps.routers.urls")),
    path("customers/", include("apps.customers.urls")),
    path("subscriptions/", include("apps.subscriptions.urls")),
    path("lcp/", include("apps.lcp.urls")),
    path("network/", include("apps.network.urls")),
    path("installations/", include("apps.customer_installations.urls")),
    path("customer-subscriptions/", include("apps.customer_subscriptions.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("accounts/", include("allauth.urls")),
    path("_allauth/", include("allauth.headless.urls")),
    path("users/", include("apps.users.urls")),
    path("", include("apps.web.urls")),
    path("celery-progress/", include("celery_progress.urls")),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI - you may wish to remove one of these depending on your preference
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
