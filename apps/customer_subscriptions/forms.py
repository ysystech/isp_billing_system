from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan


class CustomerSubscriptionForm(forms.ModelForm):
    """Form for creating customer subscriptions with preview functionality."""
    
    # Override fields for better UI
    customer_installation = forms.ModelChoiceField(
        queryset=CustomerInstallation.objects.none(),  # Will be filtered by tenant in __init__
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'onchange': 'checkExistingSubscription()'
        }),
        label="Customer Installation"
    )
    
    subscription_plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.none(),  # Will be filtered by tenant in __init__
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'onchange': 'updateAmountAndPreview()'
        }),
        label="Subscription Plan"
    )
    
    subscription_type = forms.ChoiceField(
        choices=CustomerSubscription.SUBSCRIPTION_TYPES,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'onchange': 'updateAmountAndPreview()'
        }),
        label="Payment Type"
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'step': '0.01',
            'min': '0.01',
            'oninput': 'updatePreview()'
        }),
        label="Amount (₱)"
    )
    
    start_date = forms.DateTimeField(
        widget=forms.HiddenInput(),
        required=False,
        label="Start Date & Time"
    )
    
    class Meta:
        model = CustomerSubscription
        fields = [
            'customer_installation',
            'subscription_plan',
            'subscription_type',
            'amount',
            'start_date',
            'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Optional notes...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.tenant = kwargs.pop('tenant', None)  # Add tenant handling
        super().__init__(*args, **kwargs)
        
        # Filter querysets by tenant if provided
        if self.tenant:
            self.fields['customer_installation'].queryset = CustomerInstallation.objects.filter(
                tenant=self.tenant,
                status='ACTIVE'
            )
            self.fields['subscription_plan'].queryset = SubscriptionPlan.objects.filter(
                tenant=self.tenant,
                is_active=True
            )
        
        # Set initial start date to now
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now()
    
    def clean(self):
        cleaned_data = super().clean()
        customer_installation = cleaned_data.get('customer_installation')
        subscription_type = cleaned_data.get('subscription_type')
        amount = cleaned_data.get('amount')
        subscription_plan = cleaned_data.get('subscription_plan')
        
        if all([customer_installation, subscription_type, amount, subscription_plan]):
            # Validate amount based on subscription type
            if subscription_type == 'one_month':
                cleaned_data['amount'] = subscription_plan.price
            elif subscription_type == 'fifteen_days':
                cleaned_data['amount'] = subscription_plan.price / 2
            elif subscription_type == 'custom' and amount <= 0:
                raise ValidationError("Custom amount must be greater than 0")
            
            # Automatically set start date based on existing subscription
            latest_sub = CustomerSubscription.get_latest_subscription(customer_installation)
            if latest_sub and latest_sub.end_date > timezone.now():
                # If there's an active/future subscription, start after it ends
                cleaned_data['start_date'] = latest_sub.end_date
            else:
                # Otherwise start immediately
                cleaned_data['start_date'] = timezone.now()
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance
