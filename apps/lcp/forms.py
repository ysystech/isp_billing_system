from django import forms
from .models import LCP, Splitter, NAP


class LCPForm(forms.ModelForm):
    class Meta:
        model = LCP
        fields = ['name', 'code', 'location', 'barangay', 'is_active', 'notes']
        widgets = {
            'location': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class SplitterForm(forms.ModelForm):
    class Meta:
        model = Splitter
        fields = ['code', 'type', 'location', 'is_active']
        widgets = {
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Cabinet A, Upper Shelf'}),
        }


class NAPForm(forms.ModelForm):
    class Meta:
        model = NAP
        fields = ['code', 'name', 'splitter_port', 'location', 'port_capacity', 'is_active', 'notes']
        widgets = {
            'location': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        splitter = kwargs.pop('splitter', None)
        super().__init__(*args, **kwargs)
        
        if splitter:
            # Set the max value for splitter_port based on splitter capacity
            self.fields['splitter_port'].widget.attrs['max'] = splitter.port_capacity
            self.fields['splitter_port'].widget.attrs['min'] = 1
            self.fields['splitter_port'].help_text = f'Port number (1-{splitter.port_capacity})'
