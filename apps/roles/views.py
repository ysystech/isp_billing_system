"""
Views for role management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.tenants.mixins import tenant_required

from .models import Role, PermissionCategory, PermissionCategoryMapping
from .forms import RoleForm, RolePermissionsForm
from .decorators import require_permission
from .helpers.permissions import get_accessible_roles, can_manage_role


@login_required
@permission_required('roles.view_role', raise_exception=True)
def role_list(request):
    """List all roles with user counts."""
    # Only show roles the user has permission to manage
    roles = get_accessible_roles(request.user).annotate(
        user_count_anno=Count('group__user', distinct=True)
    ).order_by('name')
    
    return render(request, 'roles/role_list.html', {
        'roles': roles,
    })


@login_required
@permission_required('roles.add_role', raise_exception=True)
def role_create(request):
    """Create a new role."""
    if request.method == 'POST':
        form = RoleForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            role = form.save(commit=False)

            role.tenant = request.tenant

            role.save()
            messages.success(request, f'Role "{role.name}" created successfully.')
            return redirect('roles:role_permissions', pk=role.pk)
    else:
        form = RoleForm(tenant=request.tenant)
    
    return render(request, 'roles/role_form.html', {
        'form': form,
        'title': 'Create Role',
    })


@login_required
@permission_required('roles.view_role', raise_exception=True)
def role_detail(request, pk):
    """View role details."""
    role = get_object_or_404(Role.objects.filter(tenant=request.tenant), pk=pk
    
    # Check if user can access this role
    if not request.user.is_superuser and not can_manage_role(request.user, role):
        messages.error(request, f'You do not have permission to view the role "{role.name}".')
        return redirect('roles:role_list')
    
    permissions = role.permissions.select_related('content_type').order_by(
        'content_type__app_label', 
        'codename'
    )
    users = role.users.order_by('username')
    
    return render(request, 'roles/role_detail.html', {
        'role': role,
        'permissions': permissions,
        'users': users,
    })


@login_required
@permission_required('roles.change_role', raise_exception=True)
def role_edit(request, pk):
    """Edit role basic information."""
    role = get_object_or_404(Role.objects.filter(tenant=request.tenant), pk=pk
    
    # Check if user can access this role
    if not request.user.is_superuser and not can_manage_role(request.user, role):
        messages.error(request, f'You do not have permission to edit the role "{role.name}".')
        return redirect('roles:role_list')
    
    if role.is_system and not request.user.is_superuser:
        messages.error(request, 'System roles can only be edited by superusers.')
        return redirect('roles:role_list')
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role, tenant=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role "{role.name}" updated successfully.')
            return redirect('roles:role_detail', pk=role.pk)
    else:
        form = RoleForm(instance=role, tenant=request.tenant)
    
    return render(request, 'roles/role_form.html', {
        'form': form,
        'role': role,
        'title': f'Edit Role: {role.name}',
    })

@login_required
@permission_required('roles.delete_role', raise_exception=True)
def role_delete(request, pk):
    """Delete a role."""
    role = get_object_or_404(Role.objects.filter(tenant=request.tenant), pk=pk
    
    # Check if user can access this role
    if not request.user.is_superuser and not can_manage_role(request.user, role):
        messages.error(request, f'You do not have permission to delete the role "{role.name}".')
        return redirect('roles:role_list')
    
    if role.is_system:
        messages.error(request, 'System roles cannot be deleted.')
        return redirect('roles:role_list')
    
    if role.user_count > 0:
        messages.error(request, f'Cannot delete role with {role.user_count} users assigned.')
        return redirect('roles:role_detail', pk=role.pk)
    
    if request.method == 'POST':
        role_name = role.name
        role.delete()
        messages.success(request, f'Role "{role_name}" deleted successfully.')
        return redirect('roles:role_list')
    
    return render(request, 'roles/role_confirm_delete.html', {
        'role': role,
    })


@login_required
@permission_required('roles.change_role', raise_exception=True)
def role_permissions(request, pk):
    """Manage role permissions."""
    role = get_object_or_404(Role.objects.filter(tenant=request.tenant), pk=pk
    
    # Check if user can access this role
    if not request.user.is_superuser and not can_manage_role(request.user, role):
        messages.error(request, f'You do not have permission to manage permissions for the role "{role.name}".')
        return redirect('roles:role_list')
    
    if role.is_system and not request.user.is_superuser:
        messages.error(request, 'System role permissions can only be edited by superusers.')
        return redirect('roles:role_detail', pk=role.pk)
    
    # Get all permission categories with their permissions
    categories = PermissionCategory.objects.prefetch_related(
        'permission_mappings__permission__content_type'
    ).order_by('order', 'name')
    
    # Get current role permissions
    current_permission_ids = list(role.permissions.values_list('id', flat=True))
    
    if request.method == 'POST':
        # Get selected permissions from form
        selected_permissions = request.POST.getlist('permissions')
        selected_permission_ids = [int(p) for p in selected_permissions]
        
        # Ensure user is not assigning permissions they don't have
        if not request.user.is_superuser:
            user_permissions = set(request.user.get_all_permissions())
            permissions_to_assign = Permission.objects.filter(id__in=selected_permission_ids)
            
            for perm in permissions_to_assign:
                perm_name = f"{perm.content_type.app_label}.{perm.codename}"
                if perm_name not in user_permissions:
                    messages.error(
                        request, 
                        f'You cannot assign the permission "{perm_name}" because you do not have it.'
                    )
                    return redirect('roles:role_permissions', pk=role.pk)
        
        # Update role permissions
        permissions = Permission.objects.filter(id__in=selected_permission_ids)
        role.group.permissions.set(permissions)
        
        messages.success(request, f'Permissions updated for role "{role.name}".')
        return redirect('roles:role_detail', pk=role.pk)
    
    # Prepare permission data for template
    permission_data = []
    for category in categories:
        category_perms = []
        for mapping in category.permission_mappings.all():
            # Skip permissions the user doesn't have (unless superuser)
            perm_name = f"{mapping.permission.content_type.app_label}.{mapping.permission.codename}"
            if request.user.is_superuser or perm_name in request.user.get_all_permissions():
                category_perms.append({
                    'id': mapping.permission.id,
                    'display_name': mapping.display_name,
                    'description': mapping.description,
                    'codename': mapping.permission.codename,
                    'is_selected': mapping.permission.id in current_permission_ids,
                })
        
        if category_perms:
            permission_data.append({
                'category': category,
                'permissions': category_perms,
            })
    
    # Debug output
    print(f"Permission data categories: {len(permission_data)}")
    for item in permission_data:
        print(f"  - {item['category'].name}: {len(item['permissions'])} permissions")
    
    return render(request, 'roles/role_permissions.html', {
        'role': role,
        'permission_data': permission_data,
    })
