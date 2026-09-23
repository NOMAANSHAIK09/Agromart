from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .permission import (
    IsFarmer,
    IsBulkBuyer,
    IsRetailer,
    IsConsumer,
)


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
    def test_invalid_login_rejected(self):
        self.create_user()

        response = self.client.post(
            self.login_url,
            {
                "username": "testfarmer",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_registration_with_invalid_role_rejected(self):
        invalid_data = self.user_data.copy()
        invalid_data["role"] = "admin"

        response = self.client.post(
            self.register_url,
            invalid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("role", response.data)

    def test_registration_with_weak_password_rejected(self):
        invalid_data = self.user_data.copy()
        invalid_data["password"] = "123"

        response = self.client.post(
            self.register_url,
            invalid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("password", response.data)

    def test_registration_with_missing_username_rejected(self):
        invalid_data = self.user_data.copy()
        invalid_data.pop("username")

        response = self.client.post(
            self.register_url,
            invalid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("username", response.data)

    def test_registration_with_invalid_email_rejected(self):
        invalid_data = self.user_data.copy()
        invalid_data["email"] = "not-an-email"

        response = self.client.post(
            self.register_url,
            invalid_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("email", response.data)

    def test_change_password_same_password_rejected(self):
        self.authenticate()

        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "StrongPass123!",
                "new_password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    def test_user_cannot_access_another_users_profile(self):
        user_a = self.create_user()

        user_b = User.objects.create_user(
            username="testconsumer",
            email="testconsumer@example.com",
            password="StrongPass123!",
            role="consumer",
            location="Hyderabad",
            phone_number="8888888888",
        )

        refresh = RefreshToken.for_user(user_a)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        response = self.client.get(
            f"{self.profile_url}?user_id={user_b.id}"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            user_a.username,
        )

        self.assertNotEqual(
            response.data["username"],
            user_b.username,
        )
    def check_permission(self, permission_class, user):
        factory = APIRequestFactory()
        request = factory.get("/test/")

        request.user = user

        permission = permission_class()
        return permission.has_permission(request, None)

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

    def test_farmer_permission(self):
        user = self.create_user()

        self.assertTrue(
            self.check_permission(IsFarmer, user)
        )
        self.assertFalse(
            self.check_permission(IsBulkBuyer, user)
        )
        self.assertFalse(
            self.check_permission(IsRetailer, user)
        )
        self.assertFalse(
            self.check_permission(IsConsumer, user)
        )

    def test_bulk_buyer_permission(self):
        user = self.create_user()
        user.role = "bulk_buyer"
        user.save()

        self.assertTrue(
            self.check_permission(IsBulkBuyer, user)
        )
        self.assertFalse(
            self.check_permission(IsFarmer, user)
        )
        self.assertFalse(
            self.check_permission(IsRetailer, user)
        )
        self.assertFalse(
            self.check_permission(IsConsumer, user)
        )

    def test_retailer_permission(self):
        user = self.create_user()
        user.role = "retailer"
        user.save()

        self.assertTrue(
            self.check_permission(IsRetailer, user)
        )
        self.assertFalse(
            self.check_permission(IsFarmer, user)
        )
        self.assertFalse(
            self.check_permission(IsBulkBuyer, user)
        )
        self.assertFalse(
            self.check_permission(IsConsumer, user)
        )

    def test_consumer_permission(self):
        user = self.create_user()
        user.role = "consumer"
        user.save()

        self.assertTrue(
            self.check_permission(IsConsumer, user)
        )
        self.assertFalse(
            self.check_permission(IsFarmer, user)
        )
        self.assertFalse(
            self.check_permission(IsBulkBuyer, user)
        )
        self.assertFalse(
            self.check_permission(IsRetailer, user)
        )