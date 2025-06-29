from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import CustomUser
from .forms import UserManagementCreateForm, UserManagementUpdateForm, UserSearchForm


@login_required
@permission_required('users.view_customuser', raise_exception=True)
def user_management_list(request):
    """List all non-superuser users with search and filter functionality."""
    # Set default is_active to 'true' if not provided
    get_data = request.GET.copy()
    if 'is_active' not in get_data:
        get_data['is_active'] = 'true'
    
    form = UserSearchForm(get_data)
    # Exclude superusers from the list
    users = CustomUser.objects.filter(is_superuser=False)
    
    # Apply search filter
    if form.is_valid():
        search_query = form.cleaned_data.get('search')
        is_active = form.cleaned_data.get('is_active')
        
        if search_query:
            users = users.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(username__icontains=search_query)
            )
        
        if is_active:
            users = users.filter(is_active=(is_active == 'true'))
    
    users = users.order_by('-date_joined')
    
    # Handle HTMX request
    if request.htmx:
        return render(request, 'users/partials/user_list.html', {
            'users': users,
            'csrf_token': request.COOKIES.get('csrftoken', '')
        })
    
    return render(request, 'users/user_management_list.html', {
        'users': users,
        'form': form,
        'active_tab': 'user-management'
    })


@login_required
@permission_required('users.add_customuser', raise_exception=True)
def user_management_create(request):
    """Create a new user."""
    if request.method == 'POST':
        form = UserManagementCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.get_full_name()}" created successfully.')
            
            # Return HTMX response
            if request.htmx:
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': '/users/management/'}
                )
            return redirect('users:user_management_list')
    else:
        form = UserManagementCreateForm()
    
    return render(request, 'users/user_management_form.html', {
        'form': form,
        'title': 'Create New User',
        'submit_text': 'Create User'
    })


@login_required
@permission_required('users.change_customuser', raise_exception=True)
def user_management_update(request, pk):
    """Update an existing user."""
    user = get_object_or_404(CustomUser, pk=pk, is_superuser=False)
    
    if request.method == 'POST':
        form = UserManagementUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.get_full_name()}" updated successfully.')
            
            # Return HTMX response
            if request.htmx:
                return HttpResponse(
                    status=204,
                    headers={'HX-Redirect': '/users/management/'}
                )
            return redirect('users:user_management_list')
    else:
        form = UserManagementUpdateForm(instance=user)
    
    return render(request, 'users/user_management_form.html', {
        'form': form,
        'user': user,
        'title': f'Update {user.get_full_name()}',
        'submit_text': 'Update User'
    })


@login_required
@permission_required('users.delete_customuser', raise_exception=True)
@require_http_methods(["DELETE"])
def user_management_delete(request, pk):
    """Deactivate a user (soft delete)."""
    user = get_object_or_404(CustomUser, pk=pk, is_superuser=False)
    
    # Soft delete by deactivating the user
    user.is_active = False
    user.save()
    
    messages.success(request, f'User "{user.get_full_name()}" deactivated successfully.')
    
    # Return HTMX response
    if request.htmx:
        return HttpResponse(
            status=204,
            headers={'HX-Redirect': '/users/management/'}
        )
    
    return redirect('users:user_management_list')


@login_required
@permission_required('users.view_customuser', raise_exception=True)
def user_management_detail(request, pk):
    """View details of a user."""
    user = get_object_or_404(CustomUser, pk=pk, is_superuser=False)
    
    return render(request, 'users/user_management_detail.html', {
        'user_obj': user  # Using user_obj to avoid conflict with request.user
    })
