from django import forms
from django.utils import timezone
from decimal import Decimal
from .models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan
from apps.users.models import CustomUser


class CustomerSubscriptionForm(forms.ModelForm):
    """Form for creating new subscriptions (payments)."""
    
    installation = forms.ModelChoiceField(
        queryset=CustomerInstallation.objects.filter(
            status='ACTIVE',
            is_active=True
        ).select_related('customer'),
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'data-placeholder': 'Select an installation'
        })
    )
    
    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'data-placeholder': 'Select a plan',
            'x-model': 'selectedPlan',
            '@change': 'updatePrice()'
        })
    )
    
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'input input-bordered w-full',
            'x-model': 'startDate',
            '@change': 'updateEndDate()'
        }),
        initial=timezone.now,
        help_text="When should this subscription start?"
    )
    
    amount_paid = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'step': '0.01',
            'min': '0',
            'x-model': 'amountPaid'
        }),
        help_text="Amount actually paid by customer"
    )
    
    class Meta:
        model = CustomerSubscription
        fields = [
            'installation', 'plan', 'start_date', 'amount_paid',
            'payment_method', 'reference_number', 'notes'
        ]
        widgets = {
            'payment_method': forms.Select(attrs={
                'class': 'select select-bordered w-full',
                'x-model': 'paymentMethod'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Reference number for GCash/Bank transfers',
                'x-show': "paymentMethod !== 'CASH'"
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Additional notes about this payment...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom labels for choice fields
        self.fields['installation'].label_from_instance = lambda obj: f"{obj.customer.full_name} - {obj.customer.email}"
        self.fields['plan'].label_from_instance = lambda obj: f"{obj.name} - {obj.speed}Mbps ({obj.day_count} days) - ₱{obj.price}"
        
        # Set default values
        if not self.instance.pk:
            self.initial['payment_date'] = timezone.now()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set collected_by to current user
        if self.user and not instance.collected_by_id:
            instance.collected_by = self.user
        
        # Set payment_date if not set
        if not instance.payment_date:
            instance.payment_date = timezone.now()
        
        # Set is_paid to True (prepaid model)
        instance.is_paid = True
        
        if commit:
            instance.save()
        
        return instance


class SubscriptionSearchForm(forms.Form):
    """Form for searching subscriptions."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered input-sm w-full max-w-xs',
            'placeholder': 'Search by customer name or email...'
        })
    )
    
    payment_method = forms.ChoiceField(
        required=False,
        choices=[('', 'All Payment Methods')] + CustomerSubscription.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Subscriptions'),
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('expiring_soon', 'Expiring Soon')
        ],
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm'
        })
    )
