from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class CaseInsensitiveEmailBackend(ModelBackend):
    """
    Custom authentication backend that allows case-insensitive email login.
    This backend authenticates users using their email address (case-insensitive)
    instead of the default username field.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user by email (case-insensitive) and password.

        Args:
            request: The HTTP request object
            username: The email address to authenticate (treated as email)
            password: The password to verify
            **kwargs: Additional keyword arguments

        Returns:
            User object if authentication successful, None otherwise
        """
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        try:
            # Perform case-insensitive lookup on email field
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
