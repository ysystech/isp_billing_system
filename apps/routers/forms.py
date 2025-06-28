from django import forms
from apps.routers.models import Router


class RouterForm(forms.ModelForm):
    """Form for creating and updating routers"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make MAC address required in the form
        self.fields['mac_address'].required = True
    
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
            "brand": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": "e.g., TP-Link, Mikrotik"
            }),
            "model": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": "e.g., Archer C6, RB750"
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
