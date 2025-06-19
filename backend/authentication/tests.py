import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient


class AuthTests(APITestCase):
    """
    Tests for the /auth/ endpoints (login, logout) in the 'authentication' app.
    """

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.username = "testuser"
        self.password = "strongpassword123"
        self.email = "test@example.com"
        self.user = self.user_model.objects.create_user(
            username=self.username, password=self.password, email=self.email
        )
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")

    def test_user_login_success(self):
        """
        Ensure a valid user can log in and receive a token.
        """
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.json())

    def test_user_login_failure_invalid_credentials(self):
        """
        Ensure login fails with invalid credentials.
        """
        data = {"username": self.username, "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_failure_missing_username(self):
        """
        Ensure login fails if username is missing.
        """
        data = {"password": self.password}
        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_failure_missing_password(self):
        """
        Ensure login fails if password is missing.
        """
        data = {"username": self.username}
        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_logout_success(self):
        """
        Ensure a logged-in user can log out successfully.
        """
        # First, log in to get a token
        login_data = {"username": self.username, "password": self.password}
        login_response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.json()["token"]

        # Set the token in the client's credentials for logout request
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)

        # Now, attempt to log out
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Logout successful")

        # Verify the token is no longer valid by trying to use it again (e.g., access a protected endpoint)
        # This requires an example of a protected endpoint. For simplicity, we'll just check if subsequent logout fails.
        # A more robust test would be to try to access /profile/ or /shopping-lists/
        second_logout_response = self.client.post(self.logout_url)
        self.assertNotEqual(
            second_logout_response.status_code, status.HTTP_200_OK
        )  # Expecting non-200, as token might be invalid or user already logged out.
        # Specific expected status code (e.g., 401 Unauthorized) depends on DRF's default token auth behavior for invalid tokens on logout.

    def test_user_logout_unauthenticated(self):
        """
        Ensure logout fails for an unauthenticated user (no token provided).
        """
        # Do not set any credentials
        response = self.client.post(self.logout_url)

        # The OpenAPI spec implies a 200 for logout, but in a real Django REST Framework setup,
        # attempting to logout an unauthenticated user or with an invalid token would likely result in 401.
        # Adjust expected status code based on your specific DRF authentication setup's behavior for this scenario.
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data) # Check for DRF default error detail