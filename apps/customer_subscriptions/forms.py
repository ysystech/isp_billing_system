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
        queryset=CustomerInstallation.objects.filter(status='ACTIVE'),
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'onchange': 'checkExistingSubscription()'
        }),
        label="Customer Installation"
    )
    
    subscription_plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True),
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
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'input input-bordered w-full',
            'onchange': 'updatePreview()'
        }),
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
        super().__init__(*args, **kwargs)
        
        # Set initial start date to now
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now()
    
    def clean(self):
        cleaned_data = super().clean()
        customer_installation = cleaned_data.get('customer_installation')
        subscription_type = cleaned_data.get('subscription_type')
        amount = cleaned_data.get('amount')
        subscription_plan = cleaned_data.get('subscription_plan')
        start_date = cleaned_data.get('start_date')
        
        if all([customer_installation, subscription_type, amount, subscription_plan]):
            # Validate amount based on subscription type
            if subscription_type == 'one_month':
                cleaned_data['amount'] = subscription_plan.price
            elif subscription_type == 'fifteen_days':
                cleaned_data['amount'] = subscription_plan.price / 2
            elif subscription_type == 'custom' and amount <= 0:
                raise ValidationError("Custom amount must be greater than 0")
            
            # Check for existing active subscription to determine start date
            latest_sub = CustomerSubscription.get_latest_subscription(customer_installation)
            if latest_sub and latest_sub.end_date > timezone.now():
                # If there's an active/future subscription, start after it ends
                if start_date < latest_sub.end_date:
                    cleaned_data['start_date'] = latest_sub.end_date
                    self.add_error(None, 
                        f"Start date adjusted to {latest_sub.end_date.strftime('%Y-%m-%d %H:%M')} "
                        f"(after current subscription ends)")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance
