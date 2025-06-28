# Network app models
from django.db import models


class NetworkPermission(models.Model):
    """
    Proxy model to hold network visualization permissions.
    This model doesn't create a database table, it's just for permissions.
    """
    
    class Meta:
        managed = False  # Don't create a database table
        default_permissions = []  # Don't create default add/change/delete permissions
        permissions = [
            ("view_network_map", "Can view network map"),
            ("view_network_hierarchy", "Can view network hierarchy"),
            ("export_network_data", "Can export network data"),
            ("view_coverage_analysis", "Can view coverage analysis"),
        ]
