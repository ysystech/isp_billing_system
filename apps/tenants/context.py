"""
Tenant context management for background tasks and signals.
"""
import threading
from contextlib import contextmanager
from typing import Optional

from apps.tenants.models import Tenant

# Thread-local storage for tenant context
_thread_locals = threading.local()


def get_current_tenant() -> Optional[Tenant]:
    """Get the current tenant from thread-local storage."""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant: Optional[Tenant]) -> None:
    """Set the current tenant in thread-local storage."""
    _thread_locals.tenant = tenant


@contextmanager
def tenant_context(tenant: Tenant):
    """
    Context manager to set tenant context for background operations.
    
    Usage:
        with tenant_context(tenant):
            # Code here will have access to the tenant context
            # via get_current_tenant()
    """
    previous_tenant = get_current_tenant()
    set_current_tenant(tenant)
    try:
        yield tenant
    finally:
        set_current_tenant(previous_tenant)


def clear_tenant_context():
    """Clear the current tenant context."""
    set_current_tenant(None)
