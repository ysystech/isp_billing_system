"""
Query Logging Middleware for Multi-Tenant Data Isolation Verification
This middleware logs all SQL queries in development to verify tenant isolation.
"""
import logging
import re
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from apps.tenants.models import Tenant

logger = logging.getLogger('tenant_queries')


class TenantQueryLoggingMiddleware(MiddlewareMixin):
    """
    Logs all SQL queries and verifies they include tenant filtering.
    Only active in DEBUG mode.
    """
    
    # Tables that should always have tenant filtering
    TENANT_AWARE_TABLES = [
        'customers_customer',
        'barangays_barangay',
        'routers_router',
        'subscriptions_subscriptionplan',
        'lcp_lcp',
        'lcp_splitter',
        'lcp_nap',
        'customer_installations_customerinstallation',
        'customer_subscriptions_customersubscription',
        'tickets_ticket',
        'tickets_ticketcomment',
        'roles_role',
        'audit_logs_auditlogentry',
    ]
    
    # Queries that are exempt from tenant filtering
    EXEMPT_PATTERNS = [
        r'SELECT.*FROM\s+"django_',  # Django internal tables
        r'SELECT.*FROM\s+"auth_',     # Auth tables
        r'SELECT.*FROM\s+"tenants_tenant"',  # Tenant table itself
        r'INSERT INTO',  # INSERT queries checked differently
        r'UPDATE.*SET',  # UPDATE queries checked differently
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_queries = []

    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Reset query log
        self.suspicious_queries = []
        initial_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Analyze queries made during request
        new_queries = connection.queries[initial_queries:]
        self.analyze_queries(new_queries, request)
        
        return response
    def analyze_queries(self, queries, request):
        """Analyze queries for potential tenant isolation issues."""
        tenant_id = getattr(request, 'tenant', None)
        tenant_id = tenant_id.id if tenant_id else None
        
        for query_info in queries:
            sql = query_info['sql']
            
            # Skip if exempt
            if self._is_exempt_query(sql):
                continue
            
            # Check if query touches tenant-aware tables
            for table in self.TENANT_AWARE_TABLES:
                if table in sql.lower():
                    if not self._has_tenant_filter(sql, tenant_id):
                        self._log_suspicious_query(sql, request.path, tenant_id)
                        self.suspicious_queries.append({
                            'sql': sql,
                            'path': request.path,
                            'tenant_id': tenant_id,
                            'user': getattr(request, 'user', None)
                        })
    
    def _is_exempt_query(self, sql):
        """Check if query is exempt from tenant filtering."""
        for pattern in self.EXEMPT_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                return True
        return False
    def _has_tenant_filter(self, sql, tenant_id):
        """Check if SQL query has tenant filtering."""
        # Look for tenant_id in WHERE clause
        tenant_patterns = [
            r'WHERE.*"tenant_id"\s*=\s*%s',
            r'WHERE.*"tenant_id"\s*=\s*\d+',
            f'WHERE.*"tenant_id"\\s*=\\s*{tenant_id}' if tenant_id else None,
            r'AND.*"tenant_id"\s*=\s*%s',
            r'AND.*"tenant_id"\s*=\s*\d+',
        ]
        
        for pattern in tenant_patterns:
            if pattern and re.search(pattern, sql, re.IGNORECASE):
                return True
        
        # Check for JOIN conditions with tenant
        if 'JOIN' in sql.upper() and '"tenant_id"' in sql:
            return True
            
        return False
    
    def _log_suspicious_query(self, sql, path, tenant_id):
        """Log queries that might be missing tenant filtering."""
        logger.warning(
            f"Potential tenant isolation issue:\n"
            f"Path: {path}\n"
            f"Expected Tenant ID: {tenant_id}\n"
            f"SQL: {sql[:200]}..."
        )