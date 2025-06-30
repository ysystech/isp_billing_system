def tenant_context(request):
    """Add tenant information to template context."""
    context = {}
    
    if hasattr(request, 'tenant') and request.tenant:
        context['current_tenant'] = request.tenant
        context['tenant_name'] = request.tenant.name
        context['is_tenant_owner'] = (
            request.user.is_authenticated and 
            request.user.is_tenant_owner
        )
    
    return context
