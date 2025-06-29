import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.deprecation import MiddlewareMixin
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from apps.audit_logs.models import AuditLogEntry


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to capture request metadata for audit logging
    """
    def process_request(self, request):
        """Store request metadata in thread-local storage"""
        # Get session key safely
        session_key = None
        if hasattr(request, 'session') and request.session:
            try:
                # Ensure session is created if it doesn't exist
                if not request.session.session_key:
                    request.session.create()
                session_key = request.session.session_key
            except:
                # If there's any issue with the session, just skip it
                pass
                
        request.audit_metadata = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'request_method': request.method,
            'session_key': session_key or '',
        }
        
    def get_client_ip(self, request):
        """Get the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Signal handlers to create audit logs for all models
_thread_locals = {}


def get_current_request():
    """Get the current request from thread-local storage"""
    import threading
    return getattr(threading.current_thread(), 'request', None)


def set_current_request(request):
    """Set the current request in thread-local storage"""
    import threading
    threading.current_thread().request = request


class AuditLogRequestMiddleware(MiddlewareMixin):
    """Store request in thread-local storage for access in signals"""
    def process_request(self, request):
        set_current_request(request)
        
    def process_response(self, request, response):
        set_current_request(None)
        return response
