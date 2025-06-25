from django import forms
from apps.routers.models import Router


class RouterForm(forms.ModelForm):
    """Form for creating and updating routers"""
    
    class Meta:
        model = Router
        fields = [
            "brand",
            "model",
            "serial_number",
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
            "notes": forms.Textarea(attrs={
                "class": "textarea textarea-bordered w-full",
                "rows": 3,
                "placeholder": "Additional notes"
            }),
        }
