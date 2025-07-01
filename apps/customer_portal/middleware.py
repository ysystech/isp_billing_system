from django.shortcuts import redirect
from django.urls import reverse


class CustomerPortalRedirectMiddleware:
    """
    Middleware to redirect customer users to their portal
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        
        # Check if user just logged in (redirect to home)
        if (request.user.is_authenticated and 
            hasattr(request.user, 'customer_profile') and
            request.path == reverse('web:home') and
            not request.user.is_staff and
            not request.user.is_tenant_owner):
            # Redirect customer users to their portal
            return redirect('customer_portal:dashboard')
        
        return response
