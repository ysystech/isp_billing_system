from django.test import Client, override_settings
from apps.utils.test_base import TenantTestCase
from apps.users.models import CustomUser
from apps.tenants.models import Tenant

TEST_STORAGES = STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(STORAGES=TEST_STORAGES)
class TestLoginRequiredViewBase(TenantTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()
        cls.authenticated_client = Client()
        
    def setUp(self):
        super().setUp()
        # Create user with tenant context from TenantTestCase
        self.test_user = CustomUser.objects.create_user(
            username="testing@example.com", 
            password="12345",
            tenant=self.tenant
        )
        self.authenticated_client.login(username="testing@example.com", password="12345")

    def _run_tests(self, url: str):
        self._assert_login_requred(url)
        self._assert_logged_in_200(url)

    def _assert_login_requred(self, url):
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def _assert_logged_in_200(self, url):
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, 200)
