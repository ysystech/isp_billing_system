from django import forms
from .models import SubscriptionPlan


class SubscriptionPlanForm(forms.ModelForm):
    """Form for creating and updating subscription plans."""
    
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'description', 'speed', 'price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., Basic Plan'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Describe what this plan includes...'
            }),
            'speed': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., 100',
                'min': 1
            }),
            'price': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., 1000.00',
                'min': 0,
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary'
            })
        }
        labels = {
            'speed': 'Speed (Mbps)',
            'price': 'Monthly Price (₱)',
            'is_active': 'Active (Available for new subscriptions)'
        }
        help_texts = {
            'speed': 'Internet speed in Megabits per second',
            'price': 'Monthly subscription price in Philippine Pesos'
        }
    
    def clean_price(self):
        """Ensure price is not negative."""
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price
    
    def clean_speed(self):
        """Ensure speed is positive."""
        speed = self.cleaned_data.get('speed')
        if speed is not None and speed <= 0:
            raise forms.ValidationError("Speed must be greater than 0.")
        return speed


class SubscriptionPlanSearchForm(forms.Form):
    """Form for searching subscription plans."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered input-sm w-full max-w-xs',
            'placeholder': 'Search plans...',
            'hx-get': '',
            'hx-target': '#subscription-plan-list',
            'hx-trigger': 'keyup changed delay:500ms',
            'hx-indicator': '#search-indicator'
        })
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Plans'),
            ('true', 'Active Only'),
            ('false', 'Inactive Only')
        ],
        widget=forms.Select(attrs={
            'class': 'select select-bordered select-sm',
            'hx-get': '',
            'hx-target': '#subscription-plan-list',
            'hx-trigger': 'change',
            'hx-indicator': '#search-indicator'
        })
    )
