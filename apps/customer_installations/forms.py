from django import forms
from django.db import models
from django.utils import timezone
from .models import CustomerInstallation
from apps.customers.models import Customer
from apps.routers.models import Router
from apps.users.models import CustomUser


class CustomerInstallationForm(forms.ModelForm):
    """Form for creating and updating customer installations."""
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(installation__isnull=True, status='active'),
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'data-placeholder': 'Select a customer'
        }),
        help_text="Only customers without existing installations are shown"
    )
    
    router = forms.ModelChoiceField(
        queryset=Router.objects.all(),
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'data-placeholder': 'Select a router'
        }),
        required=False
    )
    
    installation_technician = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='TECHNICIAN', is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'data-placeholder': 'Select a technician'
        })
    )
    
    installation_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input input-bordered w-full',
            'max': timezone.now().date().isoformat()
        }),
        initial=timezone.now().date
    )
    
    class Meta:
        model = CustomerInstallation
        fields = [
            'customer', 'router', 'installation_date', 
            'installation_technician', 'status', 'installation_notes',
            'latitude', 'longitude', 'location_accuracy', 'location_notes'
        ]
        widgets = {
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'installation_notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Enter any installation notes...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing, allow the current customer
        if self.instance and self.instance.pk:
            self.fields['customer'].queryset = Customer.objects.filter(
                models.Q(installation__isnull=True) | models.Q(installation=self.instance)
            ).filter(status='active')
