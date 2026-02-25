from django.test import TestCase
from django.contrib.auth.models import User
from Tracker.forms import CreateUserForm


class CreateUserFormTestCase(TestCase):
    """Test cases for the CreateUserForm"""

    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {"email": "test@example.com", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())

        # Test saving the form
        user = form.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "test@example.com")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpassword123"))

    def test_form_invalid_email(self):
        """Test form with invalid email"""
        form_data = {"email": "invalid-email", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_missing_email(self):
        """Test form with missing email"""
        form_data = {"password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_missing_password(self):
        """Test form with missing password"""
        form_data = {"email": "test@example.com"}
        form = CreateUserForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_form_empty_data(self):
        """Test form with empty data"""
        form_data = {}
        form = CreateUserForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_form_save_without_commit(self):
        """Test form save method with commit=False"""
        form_data = {"email": "test@example.com", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())

        # Test saving without commit
        user = form.save(commit=False)
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "test@example.com")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpassword123"))

        # User should not be saved to database yet
        self.assertIsNone(user.id)

        # Now save to database
        user.save()
        self.assertIsNotNone(user.id)

    def test_form_save_with_commit_true(self):
        """Test form save method with commit=True (default)"""
        form_data = {"email": "test@example.com", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())

        # Test saving with commit=True
        user = form.save(commit=True)
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "test@example.com")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpassword123"))

        # User should be saved to database
        self.assertIsNotNone(user.id)

    def test_form_password_hashing(self):
        """Test that password is properly hashed"""
        form_data = {"email": "test@example.com", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())
        user = form.save()

        # Password should be hashed, not stored in plain text
        self.assertNotEqual(user.password, "testpassword123")
        self.assertTrue(user.check_password("testpassword123"))

    def test_form_username_set_to_email(self):
        """Test that username is automatically set to email"""
        form_data = {"email": "user@domain.com", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertEqual(user.username, "user@domain.com")
        self.assertEqual(user.email, "user@domain.com")

    def test_form_duplicate_email(self):
        """Test form with duplicate email"""
        # Create a user first
        User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="password123",
        )

        form_data = {"email": "existing@example.com", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        # Form should be valid (form validation doesn't check for duplicates)
        self.assertTrue(form.is_valid())

        # But saving should fail due to database constraint
        with self.assertRaises(Exception):
            form.save()

    def test_form_whitespace_handling(self):
        """Test form with whitespace in email"""
        form_data = {"email": "  test@example.com  ", "password": "testpassword123"}
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())
        user = form.save()

        # Email should be stripped of whitespace
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "test@example.com")

    def test_form_long_password(self):
        """Test form with long password"""
        long_password = "a" * 128  # Very long password
        form_data = {"email": "test@example.com", "password": long_password}
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertTrue(user.check_password(long_password))

    def test_form_special_characters_in_email(self):
        """Test form with special characters in email"""
        form_data = {
            "email": "user+tag@example-domain.com",
            "password": "testpassword123",
        }
        form = CreateUserForm(data=form_data)

        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertEqual(user.email, "user+tag@example-domain.com")
        self.assertEqual(user.username, "user+tag@example-domain.com")
