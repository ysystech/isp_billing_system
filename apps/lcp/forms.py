from django import forms
from .models import LCP, Splitter, NAP


class LCPForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if tenant:
            # Filter barangays by tenant
            self.fields['barangay'].queryset = self.fields['barangay'].queryset.filter(tenant=tenant)
    
    class Meta:
        model = LCP
        fields = ['name', 'code', 'location', 'barangay', 'latitude', 'longitude', 
                 'location_accuracy', 'location_notes', 'coverage_radius_meters', 
                 'is_active', 'notes']
        widgets = {
            'location': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'code': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'barangay': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'coverage_radius_meters': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }


class SplitterForm(forms.ModelForm):
    class Meta:
        model = Splitter
        fields = ['code', 'type', 'location', 'latitude', 'longitude', 
                 'location_accuracy', 'location_notes', 'is_active']
        widgets = {
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Cabinet A, Upper Shelf', 'class': 'input input-bordered w-full'}),
            'code': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'type': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }


class NAPForm(forms.ModelForm):
    class Meta:
        model = NAP
        fields = ['code', 'name', 'splitter_port', 'location', 'latitude', 'longitude',
                 'location_accuracy', 'location_notes', 'max_distance_meters',
                 'port_capacity', 'is_active', 'notes']
        widgets = {
            'location': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered w-full'}),
            'code': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'splitter_port': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'port_capacity': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'max_distance_meters': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        splitter = kwargs.pop('splitter', None)
        super().__init__(*args, **kwargs)
        
        if splitter:
            # Set the max value for splitter_port based on splitter capacity
            self.fields['splitter_port'].widget.attrs['max'] = splitter.port_capacity
            self.fields['splitter_port'].widget.attrs['min'] = 1
            self.fields['splitter_port'].help_text = f'Port number (1-{splitter.port_capacity})'
