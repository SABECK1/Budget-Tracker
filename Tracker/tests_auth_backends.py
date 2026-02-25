from django.test import TestCase
from django.contrib.auth import get_user_model
from Tracker.auth_backends import CaseInsensitiveEmailBackend

User = get_user_model()


class CaseInsensitiveEmailBackendTestCase(TestCase):
    """Test cases for the case-insensitive email authentication backend"""

    def setUp(self):
        """Set up test data"""
        self.backend = CaseInsensitiveEmailBackend()
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpassword123",
        )

    def test_authenticate_with_correct_email_and_password(self):
        """Test successful authentication with correct email and password"""
        user = self.backend.authenticate(
            None, username="testuser@example.com", password="testpassword123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_correct_email_uppercase_and_password(self):
        """Test successful authentication with uppercase email and correct password"""
        user = self.backend.authenticate(
            None, username="TESTUSER@EXAMPLE.COM", password="testpassword123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_correct_email_mixed_case_and_password(self):
        """Test successful authentication with mixed case email and correct password"""
        user = self.backend.authenticate(
            None, username="TestUser@Example.Com", password="testpassword123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_incorrect_password(self):
        """Test authentication failure with incorrect password"""
        user = self.backend.authenticate(
            None, username="testuser@example.com", password="wrongpassword"
        )
        self.assertIsNone(user)

    def test_authenticate_with_nonexistent_email(self):
        """Test authentication failure with non-existent email"""
        user = self.backend.authenticate(
            None, username="nonexistent@example.com", password="testpassword123"
        )
        self.assertIsNone(user)

    def test_authenticate_with_nonexistent_email_uppercase(self):
        """Test authentication failure with non-existent uppercase email"""
        user = self.backend.authenticate(
            None, username="NONEXISTENT@EXAMPLE.COM", password="testpassword123"
        )
        self.assertIsNone(user)

    def test_authenticate_with_empty_username(self):
        """Test authentication with empty username"""
        user = self.backend.authenticate(None, username="", password="testpassword123")
        self.assertIsNone(user)

    def test_authenticate_with_none_username(self):
        """Test authentication with None username"""
        user = self.backend.authenticate(
            None, username=None, password="testpassword123"
        )
        self.assertIsNone(user)

    def test_authenticate_with_kwargs_username(self):
        """Test authentication using kwargs username parameter"""
        user = self.backend.authenticate(
            None, password="testpassword123", **{"username": "testuser@example.com"}
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_kwargs_username_uppercase(self):
        """Test authentication using kwargs username parameter with uppercase"""
        user = self.backend.authenticate(
            None, password="testpassword123", **{"username": "TESTUSER@EXAMPLE.COM"}
        )
        self.assertEqual(user, self.user)

    def test_authenticate_inactive_user(self):
        """Test authentication with inactive user"""
        self.user.is_active = False
        self.user.save()

        user = self.backend.authenticate(
            None, username="testuser@example.com", password="testpassword123"
        )
        self.assertIsNone(user)

    def test_authenticate_with_email_field(self):
        """Test authentication using email field directly"""
        user = self.backend.authenticate(
            None, username="testuser@example.com", password="testpassword123"
        )
        self.assertEqual(user, self.user)

    def test_authenticate_with_email_field_uppercase(self):
        """Test authentication using email field directly with uppercase"""
        user = self.backend.authenticate(
            None, username="TESTUSER@EXAMPLE.COM", password="testpassword123"
        )
        self.assertEqual(user, self.user)

    def test_get_user_with_valid_id(self):
        """Test getting user with valid ID"""
        user = self.backend.get_user(self.user.id)
        self.assertEqual(user, self.user)

    def test_get_user_with_invalid_id(self):
        """Test getting user with invalid ID"""
        user = self.backend.get_user(99999)
        self.assertIsNone(user)

    def test_get_user_with_none_id(self):
        """Test getting user with None ID"""
        user = self.backend.get_user(None)
        self.assertIsNone(user)
