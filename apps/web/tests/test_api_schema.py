from django.test import TestCase
from apps.utils.test_base import TenantTestCase


class TestApiSchema(TenantTestCase):
    def test_schema_returns_success(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(200, response.status_code)
