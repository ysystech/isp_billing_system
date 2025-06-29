from django import forms
from django.core.exceptions import ValidationError
from .models import Ticket, TicketComment
from apps.customer_installations.models import CustomerInstallation
from apps.customers.models import Customer
from apps.users.models import CustomUser


class TicketForm(forms.ModelForm):
    """Form for creating and updating tickets."""
    
    customer_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Search by customer name, email, or phone...',
            'x-model': 'customerSearch',
            '@input': 'searchCustomers'
        }),
        help_text="Start typing to search for a customer"
    )
    
    class Meta:
        model = Ticket
        fields = [
            'customer', 'customer_installation', 'title', 'description',
            'category', 'priority', 'status', 'source', 'assigned_to',
            'resolution_notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'customer_installation': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Brief description of the issue'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Provide detailed information about the issue...'
            }),
            'category': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'priority': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'source': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'resolution_notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Notes about how the issue was resolved...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Set the logged-in user as reported_by (will be set in view)
        self.user = user
        
        # Filter querysets by tenant
        if self.tenant:
            # Filter customers by tenant
            self.fields['customer'].queryset = Customer.objects.filter(
                tenant=self.tenant,
                status='active'
            )
            
            # Filter customer installations by tenant
            self.fields['customer_installation'].queryset = CustomerInstallation.objects.filter(
                tenant=self.tenant
            )
            
            # Limit assigned_to choices to staff users in the same tenant
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                tenant=self.tenant,
                is_staff=True
            ).order_by('first_name', 'last_name')
        
        # Set required fields
        self.fields['customer'].required = True
        self.fields['customer'].widget = forms.HiddenInput()  # Make it hidden since we use search
        self.fields['customer_installation'].required = True
        self.fields['title'].required = True
        self.fields['description'].required = True
        
        # Make resolution_notes required if status is resolved
        if self.instance.pk and self.instance.status == 'resolved':
            self.fields['resolution_notes'].required = True
        
        # If editing, pre-populate customer installations
        if self.instance.pk and self.instance.customer:
            installations_qs = CustomerInstallation.objects.filter(
                customer=self.instance.customer
            )
            if self.tenant:
                installations_qs = installations_qs.filter(tenant=self.tenant)
            self.fields['customer_installation'].queryset = installations_qs
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        resolution_notes = cleaned_data.get('resolution_notes')
        assigned_to = cleaned_data.get('assigned_to')
        
        # Validate resolution notes are provided when resolving
        if status == 'resolved' and not resolution_notes:
            raise ValidationError({
                'resolution_notes': 'Resolution notes are required when marking a ticket as resolved.'
            })
        
        # Validate assignment when changing to assigned or in_progress
        if status in ['assigned', 'in_progress'] and not assigned_to:
            raise ValidationError({
                'assigned_to': f'A technician must be assigned when status is {status}.'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        ticket = super().save(commit=False)
        
        # Set reported_by to the logged-in user if creating new ticket
        if not ticket.pk and self.user:
            ticket.reported_by = self.user
        
        if commit:
            ticket.save()
        
        return ticket


class TicketCommentForm(forms.ModelForm):
    """Form for adding comments to tickets."""
    
    class Meta:
        model = TicketComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Add your comment...'
            })
        }


class TicketFilterForm(forms.Form):
    """Form for filtering tickets in list view."""
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Ticket.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'select select-bordered'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Ticket.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'select select-bordered'})
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_staff=True),
        required=False,
        empty_label='All Technicians',
        widget=forms.Select(attrs={'class': 'select select-bordered'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered',
            'placeholder': 'Search tickets...'
        })
    )
