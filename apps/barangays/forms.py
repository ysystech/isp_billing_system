from django import forms
from apps.barangays.models import Barangay


class BarangayForm(forms.ModelForm):
    """Form for creating and updating Barangay"""
    
    class Meta:
        model = Barangay
        fields = ["name", "code", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Enter barangay name"
            }),
            "code": forms.TextInput(attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Optional barangay code"
            }),
            "description": forms.Textarea(attrs={
                "class": "textarea textarea-bordered w-full",
                "rows": 3,
                "placeholder": "Additional notes about this barangay"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "checkbox"
            }),
        }
