from django import forms
from django.core.exceptions import ValidationError
from apps.routers.models import Router


class RouterForm(forms.ModelForm):
    """Form for creating and updating routers"""
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        # Make MAC address required in the form
        self.fields['mac_address'].required = True
    
    def clean_serial_number(self):
        serial_number = self.cleaned_data.get('serial_number')
        if serial_number and self.tenant:
            # Check if serial number already exists for this tenant
            qs = Router.objects.filter(
                tenant=self.tenant,
                serial_number=serial_number
            )
            # If updating, exclude current instance
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f"A router with serial number '{serial_number}' already exists in your inventory."
                )
        return serial_number
    
    def clean_mac_address(self):
        mac_address = self.cleaned_data.get('mac_address')
        if mac_address and self.tenant:
            # Normalize MAC address to uppercase
            mac_address = mac_address.upper()
            
            # Check if MAC address already exists for this tenant
            qs = Router.objects.filter(
                tenant=self.tenant,
                mac_address=mac_address
            )
            # If updating, exclude current instance
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f"A router with MAC address '{mac_address}' already exists in your inventory."
                )
        return mac_address
    
    class Meta:
        model = Router
        fields = [
            "brand",
            "model",
            "serial_number",
            "mac_address",
            "notes",
        ]
        widgets = {
            "brand": forms.Select(attrs={
                "class": "select select-bordered w-full"
            }),
            "model": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": "e.g., hAP ac2, Archer C6, UniFi Dream Machine"
            }),
            "serial_number": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Enter serial number"
            }),
            "mac_address": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": "e.g., 00:11:22:33:44:55",
                "pattern": "^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
                "title": "Enter a valid MAC address (e.g., 00:11:22:33:44:55)"
            }),
            "notes": forms.Textarea(attrs={
                "class": "textarea textarea-bordered w-full",
                "rows": 3,
                "placeholder": "Additional notes"
            }),
        }
