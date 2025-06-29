from django.db import models
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from apps.utils.models import BaseModel

User = get_user_model()


class AuditLogEntry(BaseModel):
    """
    Extended audit log entry that captures additional metadata
    beyond Django's built-in LogEntry
    """
    # Link to Django's LogEntry
    log_entry = models.OneToOneField(
        LogEntry,
        on_delete=models.CASCADE,
        related_name='audit_metadata',
        null=True,
        blank=True
    )
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/client user agent string"
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        help_text="HTTP request method"
    )
    
    # Additional tracking
    session_key = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        help_text="Django session key"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        if self.log_entry:
            return f"Audit log for {self.log_entry}"
        return f"Audit metadata {self.id}"
