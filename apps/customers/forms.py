from django import forms
from django.core.exceptions import ValidationError

from .models import Customer
from apps.barangays.models import Barangay


class CustomerForm(forms.ModelForm):
    """Form for creating and updating customers"""
    
    class Meta:
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_primary",
            "street_address",
            "barangay",
            "latitude",
            "longitude",
            "location_accuracy",
            "location_notes",
            "status",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "email": forms.EmailInput(attrs={"class": "input input-bordered w-full"}),
            "phone_primary": forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "+63 XXX XXX XXXX"}),
            "street_address": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "barangay": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "latitude": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "any", "placeholder": "8.4542"}),
            "longitude": forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "any", "placeholder": "124.6319"}),
            "location_accuracy": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "location_notes": forms.TextInput(attrs={"class": "input input-bordered w-full", "placeholder": "Near landmark..."}),
            "status": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "notes": forms.Textarea(attrs={"class": "textarea textarea-bordered w-full", "rows": 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active barangays in the dropdown
        self.fields["barangay"].queryset = Barangay.objects.filter(is_active=True)
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            # Check for duplicate email, excluding current instance in update
            qs = Customer.objects.filter(email__iexact=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A customer with this email already exists.")
        return email


class CustomerSearchForm(forms.Form):
    """Form for searching customers"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "Search by name, email, or phone...",
            "hx-get": "",
            "hx-trigger": "keyup changed delay:500ms",
            "hx-target": "#customer-list",
            "hx-indicator": "#search-indicator"
        })
    )
    barangay = forms.ModelChoiceField(
        required=False,
        queryset=Barangay.objects.filter(is_active=True),
        empty_label="All Barangays",
        widget=forms.Select(attrs={
            "class": "select select-bordered",
            "hx-get": "",
            "hx-trigger": "change",
            "hx-target": "#customer-list",
            "hx-indicator": "#search-indicator"
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Status")] + Customer.STATUS_CHOICES,
        widget=forms.Select(attrs={
            "class": "select select-bordered",
            "hx-get": "",
            "hx-trigger": "change",
            "hx-target": "#customer-list",
            "hx-indicator": "#search-indicator"
        })
    )
