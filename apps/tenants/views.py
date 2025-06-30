from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _

from .forms import TenantSettingsForm
from .mixins import tenant_owner_required


@login_required
@tenant_owner_required
def tenant_settings(request):
    """View for tenant owners to manage their tenant settings."""
    tenant = request.tenant
    
    if request.method == 'POST':
        form = TenantSettingsForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, _('Company settings updated successfully.'))
            return redirect('tenants:settings')
    else:
        form = TenantSettingsForm(instance=tenant)
    
    context = {
        'form': form,
        'tenant': tenant,
        'active_tab': 'tenant-settings',
    }
    
    return render(request, 'tenants/settings.html', context)
