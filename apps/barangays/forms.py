from django import forms
from django.core.exceptions import ValidationError
from apps.barangays.models import Barangay


class BarangayForm(forms.ModelForm):
    """Form for creating and updating Barangay"""
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and self.tenant:
            # Check if name already exists for this tenant
            qs = Barangay.objects.filter(
                tenant=self.tenant,
                name__iexact=name  # Case-insensitive check
            )
            # If updating, exclude current instance
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f"A barangay named '{name}' already exists."
                )
        return name
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code and self.tenant:
            # Check if code already exists for this tenant
            qs = Barangay.objects.filter(
                tenant=self.tenant,
                code__iexact=code  # Case-insensitive check
            )
            # If updating, exclude current instance
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    f"A barangay with code '{code}' already exists."
                )
        return code
    
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
