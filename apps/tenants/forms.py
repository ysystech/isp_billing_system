from django import forms
from .models import Tenant


class TenantSettingsForm(forms.ModelForm):
    """Form for tenant owners to update their tenant settings."""
    
    class Meta:
        model = Tenant
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Company Name',
                'class': 'input input-bordered w-full'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Company Name'
        self.fields['name'].help_text = 'This name will be displayed throughout the system'
