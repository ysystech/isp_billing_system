from django import forms
from django.db import models
from django.utils import timezone
from .models import CustomerInstallation
from apps.customers.models import Customer
from apps.routers.models import Router
from apps.users.models import CustomUser
from apps.lcp.models import NAP


class CustomerInstallationForm(forms.ModelForm):
    """Form for creating and updating customer installations."""
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'data-placeholder': 'Select a customer'
        }),
        help_text="Only customers without existing installations are shown"
    )
    
    router = forms.ModelChoiceField(
        queryset=Router.objects.none(),  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'data-placeholder': 'Select a router'
        }),
        required=False
    )
    
    installation_technician = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True),
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
            'customer', 'router', 'nap', 'nap_port', 'installation_date', 
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
            }),
            'nap': forms.Select(attrs={
                'class': 'select select-bordered w-full',
                'onchange': 'updatePortOptions()',
                'data-placeholder': 'Select a NAP'
            }),
            'nap_port': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 1,
                'placeholder': 'Port number'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Filter querysets by tenant
        if self.tenant:
            # Filter customers by tenant
            if self.instance and self.instance.pk:
                self.fields['customer'].queryset = Customer.objects.filter(
                    tenant=self.tenant,
                    models.Q(installation__isnull=True) | models.Q(installation=self.instance)
                ).filter(status='active')
            else:
                self.fields['customer'].queryset = Customer.objects.filter(
                    tenant=self.tenant,
                    installation__isnull=True, 
                    status='active'
                )
            
            # Filter routers by tenant
            self.fields['router'].queryset = Router.objects.filter(tenant=self.tenant)
            
            # Filter NAPs by tenant
            self.fields['nap'].queryset = NAP.objects.filter(
                tenant=self.tenant,
                is_active=True
            ).select_related('splitter__lcp').order_by('splitter__lcp__code', 'code')
        
        # Format NAP display
        self.fields['nap'].label_from_instance = lambda obj: f"{obj.splitter.lcp.code} → {obj.splitter.code} → {obj.code} ({obj.name})"
        
        # Set help text for NAP
        self.fields['nap'].help_text = "Select the NAP where this customer will be connected"
        
        # Dynamic port validation based on selected NAP
        if self.instance and self.instance.nap:
            self.fields['nap_port'].widget.attrs['max'] = self.instance.nap.port_capacity
            self.fields['nap_port'].help_text = f"Available ports: 1-{self.instance.nap.port_capacity}"
