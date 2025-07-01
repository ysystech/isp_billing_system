from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.db import transaction
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.crypto import get_random_string
from apps.customers.forms import CustomerForm

User = get_user_model()


class CustomerWithUserForm(CustomerForm):
    """Extended form that can create a user account with the customer"""
    
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        label="Create customer portal account",
        help_text="Allow customer to log in and view their account information",
        widget=forms.CheckboxInput(attrs={"class": "checkbox"})
    )
    
    set_initial_password = forms.BooleanField(
        required=False,
        initial=False,
        label="Set initial password (otherwise send reset link)",
        help_text="Generate a random password that will be shown after creation",
        widget=forms.CheckboxInput(attrs={"class": "checkbox"})
    )
    
    def save(self, commit=True):
        with transaction.atomic():
            # Save the customer first
            customer = super().save(commit=False)
            
            if commit:
                customer.save()
                
                # Create user account if requested
                if self.cleaned_data.get('create_user_account'):
                    # Check if user with this email already exists
                    existing_user = User.objects.filter(email=customer.email).first()
                    
                    if not existing_user:
                        # Create username from email
                        username = customer.email.split('@')[0]
                        base_username = username
                        counter = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}{counter}"
                            counter += 1
                        
                        # Create user
                        user = User.objects.create_user(
                            username=username,
                            email=customer.email,
                            first_name=customer.first_name,
                            last_name=customer.last_name,
                            tenant=customer.tenant,
                            is_tenant_owner=False,
                        )
                        
                        # Set password based on option selected
                        if self.cleaned_data.get('set_initial_password'):
                            # Generate random password
                            password = get_random_string(12)
                            user.set_password(password)
                            user.save()
                            
                            # Store password to display after save
                            self.generated_password = password
                            self.generated_username = username
                        else:
                            # Set unusable password - they'll need to reset it
                            user.set_unusable_password()
                            user.save()
                            
                            # Send password reset email
                            form = PasswordResetForm({'email': user.email})
                            if form.is_valid():
                                form.save(
                                    subject_template_name='registration/password_reset_subject.txt',
                                    email_template_name='customer_portal/emails/welcome_customer.html',
                                    from_email=None,
                                    request=None,  # You might need to pass request from view
                                )
                        
                        # Link to customer
                        customer.user = user
                        customer.save()
                    else:
                        # Link existing user if not already linked
                        if not hasattr(existing_user, 'customer_profile'):
                            customer.user = existing_user
                            customer.save()
                
        return customer
