from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class AccountsAPITests(APITestCase):

    def setUp(self):
        self.register_url = "/api/accounts/register/"
        self.login_url = "/api/accounts/login/"
        self.profile_url = "/api/accounts/profile/"
        self.change_password_url = "/api/accounts/change-password/"
        self.logout_url = "/api/accounts/logout/"
        self.refresh_url = "/api/accounts/token/refresh/"

        self.user_data = {
            "username": "testfarmer",
            "email": "testfarmer@example.com",
            "password": "StrongPass123!",
            "role": "farmer",
            "location": "Guntur",
            "phone_number": "9876543210",
        }

    def create_user(self):
        return User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"],
            role=self.user_data["role"],
            location=self.user_data["location"],
            phone_number=self.user_data["phone_number"],
        )

    def authenticate(self):
        user = self.create_user()
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        return user, refresh

    def test_register_user(self):
        response = self.client.post(
            self.register_url,
            self.user_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "testfarmer")
        self.assertEqual(response.data["role"], "farmer")

    def test_duplicate_email_rejected(self):
        self.create_user()

        response = self.client.post(
            self.register_url,
            self.user_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_returns_tokens(self):
        self.create_user()

        response = self.client.post(
            self.login_url,
            {
                "username": "testfarmer",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_profile_requires_authentication(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_view_profile(self):
        user, _ = self.authenticate()

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], user.username)
        self.assertEqual(response.data["role"], user.role)

    def test_user_can_update_profile(self):
        self.authenticate()

        response = self.client.patch(
            self.profile_url,
            {
                "location": "Hyderabad",
                "phone_number": "9999999999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location"], "Hyderabad")
        self.assertEqual(response.data["phone_number"], "9999999999")

    def test_user_cannot_change_username_or_role(self):
        user, _ = self.authenticate()

        response = self.client.patch(
            self.profile_url,
            {
                "username": "hacker",
                "role": "consumer",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()

        self.assertEqual(user.username, "testfarmer")
        self.assertEqual(user.role, "farmer")

    def test_change_password(self):
        self.authenticate()

        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "StrongPass123!",
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(username="testfarmer")
        self.assertTrue(user.check_password("NewStrongPass123!"))

    def test_wrong_old_password_rejected(self):
        self.authenticate()

        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "WrongPassword123!",
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_blacklists_refresh_token(self):
        user = self.create_user()
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        response = self.client.post(
            self.logout_url,
            {
                "refresh": str(refresh),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_205_RESET_CONTENT,
        )

        response = self.client.post(
            self.refresh_url,
            {
                "refresh": str(refresh),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )