"""
Tenant-aware Celery tasks and utilities.
"""
import logging
from typing import Any, Dict, List, Optional

from celery import Task, shared_task
from django.db import transaction

from apps.tenants.context import tenant_context
from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)


class TenantAwareTask(Task):
    """
    Base class for tenant-aware Celery tasks.
    
    Provides utilities for running tasks in tenant context.
    """
    
    def run_for_tenant(self, tenant_id: int, *args, **kwargs) -> Any:
        """
        Run the task for a specific tenant.
        
        Args:
            tenant_id: ID of the tenant to run the task for
            *args, **kwargs: Arguments to pass to the task
        """
        try:
            tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        except Tenant.DoesNotExist:
            logger.warning(f"Tenant {tenant_id} not found or inactive")
            return None
            
        with tenant_context(tenant):
            logger.info(f"Running {self.name} for tenant {tenant.name}")
            return self.run(*args, **kwargs)
    
    def run_for_all_tenants(self, *args, **kwargs) -> Dict[int, Any]:
        """
        Run the task for all active tenants.
        
        Returns:
            Dictionary mapping tenant ID to task result
        """
        results = {}
        active_tenants = Tenant.objects.filter(is_active=True)
        
        for tenant in active_tenants:
            try:
                with tenant_context(tenant):
                    logger.info(f"Running {self.name} for tenant {tenant.name}")
                    results[tenant.id] = self.run(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error running {self.name} for tenant {tenant.name}: {e}")
                results[tenant.id] = {"error": str(e)}
                
        return results


@shared_task
def run_tenant_task(task_name: str, tenant_id: Optional[int] = None, *args, **kwargs):
    """
    Generic task runner that can run any task for a specific tenant or all tenants.
    
    Args:
        task_name: Fully qualified task name (e.g., 'apps.module.tasks.my_task')
        tenant_id: ID of specific tenant, or None to run for all tenants
        *args, **kwargs: Arguments to pass to the task
    """
    from celery import current_app
    
    task = current_app.tasks.get(task_name)
    if not task:
        logger.error(f"Task {task_name} not found")
        return None
        
    if not isinstance(task, TenantAwareTask):
        logger.warning(f"Task {task_name} is not tenant-aware")
        return task.apply_async(args=args, kwargs=kwargs)
        
    if tenant_id:
        return task.run_for_tenant(tenant_id, *args, **kwargs)
    else:
        return task.run_for_all_tenants(*args, **kwargs)


@shared_task
def cleanup_inactive_tenants():
    """
    Periodic task to clean up data for inactive tenants.
    This is a system-level task that doesn't need tenant context.
    """
    inactive_tenants = Tenant.objects.filter(is_active=False)
    
    for tenant in inactive_tenants:
        logger.info(f"Processing cleanup for inactive tenant: {tenant.name}")
        # Add cleanup logic here as needed
        # For now, just log
        
    return f"Processed {inactive_tenants.count()} inactive tenants"
