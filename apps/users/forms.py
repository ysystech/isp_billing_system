import logging

import requests
from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .helpers import validate_profile_picture
from .models import CustomUser
from apps.roles.models import Role
from apps.roles.helpers.permissions import get_accessible_roles


class TurnstileSignupForm(SignupForm):
    """
    Sign up form that includes a turnstile captcha.
    """

    turnstile_token = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_turnstile_token(self):
        if not settings.TURNSTILE_SECRET:
            logging.info("No turnstile secret found, not checking captcha")
            return

        turnstile_token = self.cleaned_data.get("turnstile_token", None)
        if not turnstile_token:
            raise forms.ValidationError("Missing captcha. Please try again.")

        turnstile_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": settings.TURNSTILE_SECRET,
            "response": turnstile_token,
        }
        try:
            response = requests.post(turnstile_url, data=payload, timeout=10).json()
            if not response["success"]:
                raise forms.ValidationError("Invalid captcha. Please try again.")
        except requests.Timeout:
            raise forms.ValidationError("Captcha verification timed out. Please try again.") from None

        return turnstile_token


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(label=_("Email"), required=True)

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name")


class UploadAvatarForm(forms.Form):
    avatar = forms.FileField(validators=[validate_profile_picture])


class TermsSignupForm(TurnstileSignupForm):
    """Custom signup form to add a checkbox for accepting the terms and company name."""

    terms_agreement = forms.BooleanField(required=True)
    company_name = forms.CharField(
        max_length=100,
        required=True,
        label=_("Company Name"),
        help_text=_("Enter your company or organization name"),
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., ABC Internet Services'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # blank out overly-verbose help text
        self.fields["password1"].help_text = ""
        link = '<a class="link" href="{}" target="_blank">{}</a>'.format(
            reverse("web:terms"),
            _("Terms and Conditions"),
        )
        self.fields["terms_agreement"].label = mark_safe(_("I agree to the {terms_link}").format(terms_link=link))
        
        # Move company_name to be after email but before password
        field_order = ['email', 'company_name', 'password1', 'password2', 'terms_agreement']
        if 'turnstile_token' in self.fields:
            field_order.append('turnstile_token')
        
        # Reorder fields
        new_fields = {}
        for field_name in field_order:
            if field_name in self.fields:
                new_fields[field_name] = self.fields[field_name]
        # Add any remaining fields
        for field_name, field in self.fields.items():
            if field_name not in new_fields:
                new_fields[field_name] = field
        self.fields = new_fields
    
    def save(self, request):
        # First save the user via parent
        user = super().save(request)
        
        # Create tenant for the new user
        from apps.tenants.models import Tenant
        company_name = self.cleaned_data.get('company_name')
        
        if company_name and user:
            tenant = Tenant.objects.create(
                name=company_name,
                created_by=user
            )
            
            # Update user with tenant and make them tenant owner
            user.tenant = tenant
            user.is_tenant_owner = True
            user.save()
        
        return user

class UserManagementCreateForm(forms.ModelForm):
    """Form for creating new users in the admin panel."""
    
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., Juan Dela Cruz',
            'x-model': 'fullName',
            '@input': 'updateEmail()'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., juan.delacruz@example.com',
            'x-model': 'email'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter password'
        }),
        help_text="Password must be at least 8 characters long."
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm password'
        }),
        label="Confirm Password"
    )
    
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.none(),  # Will be set in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        help_text="Select roles to assign to this user (only showing roles you have permission to manage)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'roles']
        widgets = {
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Store the user for permission validation
        self.user = user
        
        # Filter roles to only show ones the current user can manage
        if user:
            self.fields['roles'].queryset = get_accessible_roles(user)
        else:
            self.fields['roles'].queryset = Role.objects.filter(is_active=True)
    
    def clean_roles(self):
        roles = self.cleaned_data.get('roles', [])
        user = getattr(self, 'user', None)
        
        # Skip validation for superusers or if no user is provided
        if not user or user.is_superuser:
            return roles
        
        # Get all accessible roles for the current user
        accessible_roles = set(get_accessible_roles(user).values_list('id', flat=True))
        
        # Check if all selected roles are accessible
        for role in roles:
            if role.id not in accessible_roles:
                raise forms.ValidationError(
                    f"You do not have permission to assign the role '{role.name}'. "
                    f"You can only assign roles that contain permissions you have."
                )
        
        return roles
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_roles(self):
        roles = self.cleaned_data.get('roles', [])
        user = getattr(self, 'user', None)
        
        # Skip validation for superusers or if no user is provided
        if not user or user.is_superuser:
            return roles
        
        # Get all accessible roles for the current user
        accessible_roles = set(get_accessible_roles(user).values_list('id', flat=True))
        
        # Check if all selected roles are accessible
        for role in roles:
            if role.id not in accessible_roles:
                raise forms.ValidationError(
                    f"You do not have permission to assign the role '{role.name}'. "
                    f"You can only assign roles that contain permissions you have."
                )
        
        return roles
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Passwords do not match.")
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Split full name into first and last name
        full_name = self.cleaned_data.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Set username as email
        user.username = self.cleaned_data['email']
        
        # Set password
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            
            # Add user to selected role groups
            selected_roles = self.cleaned_data.get('roles', [])
            for role in selected_roles:
                user.groups.add(role.group)
        
        return user


class UserManagementUpdateForm(forms.ModelForm):
    """Form for updating existing users."""
    
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., Juan Dela Cruz'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'e.g., juan.delacruz@example.com'
        })
    )
    
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.none(),  # Will be set in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox checkbox-primary'
        }),
        help_text="Select roles to assign to this user (only showing roles you have permission to manage)"
    )
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'is_active', 'roles']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Store the user for permission validation
        self.user = user
        
        # Filter roles to only show ones the current user can manage
        if user:
            self.fields['roles'].queryset = get_accessible_roles(user)
        else:
            self.fields['roles'].queryset = Role.objects.filter(is_active=True)
            
        if self.instance and self.instance.pk:
            # Set full name from first and last name
            self.fields['full_name'].initial = self.instance.get_full_name()
            
            # Set initial roles, but only include roles that current user can manage
            if user:
                accessible_roles = get_accessible_roles(user)
                self.fields['roles'].initial = accessible_roles.filter(group__user=self.instance)
            else:
                self.fields['roles'].initial = Role.objects.filter(group__user=self.instance)
    
    def clean_roles(self):
        roles = self.cleaned_data.get('roles', [])
        user = getattr(self, 'user', None)
        
        # Skip validation for superusers or if no user is provided
        if not user or user.is_superuser:
            return roles
        
        # Get all accessible roles for the current user
        accessible_roles = set(get_accessible_roles(user).values_list('id', flat=True))
        
        # Check if all selected roles are accessible
        for role in roles:
            if role.id not in accessible_roles:
                raise forms.ValidationError(
                    f"You do not have permission to assign the role '{role.name}'. "
                    f"You can only assign roles that contain permissions you have."
                )
        
        return roles
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email exists for other users
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Split full name into first and last name
        full_name = self.cleaned_data.get('full_name', '').strip()
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Update username to match email
        user.username = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Update roles
            # First, remove user from all role groups
            user.groups.clear()
            
            # Then add user to selected role groups
            selected_roles = self.cleaned_data.get('roles', [])
            for role in selected_roles:
                user.groups.add(role.group)
        
        return user


class UserSearchForm(forms.Form):
    """Form for searching and filtering users."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered input-sm w-full max-w-xs',
            'placeholder': 'Search users...',
            'hx-get': '',
            'hx-target': '#user-list',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-indicator': '#search-indicator'
        })
    )
    
    is_active = forms.ChoiceField(
        required=False,
        initial='true',  # Set default to Active Only
        choices=[
            ('true', 'Active Only'),
            ('false', 'Inactive Only'),
            ('', 'All Users')
        ],
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm',
            'hx-get': '',
            'hx-target': '#user-list',
            'hx-trigger': 'change',
            'hx-indicator': '#search-indicator'
        })
    )
