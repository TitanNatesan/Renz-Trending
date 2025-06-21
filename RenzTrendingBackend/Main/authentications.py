# yourapp/authentication.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import Customer

class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Reference 'request' and 'kwargs' to prevent warnings or errors
        _ = request
        _ = kwargs

        try:
            if '@' in username:
                # Email login
                user = User.objects.get(email=username)
            elif "+" in username:
                # Mobile number login
                customer = Customer.objects.get(phone=username)
                user = customer
            else:
                # Username login
                user = User.objects.get(username=username)
        except (User.DoesNotExist, Customer.DoesNotExist):
            return None

        # Safely check if 'user' has check_password
        if hasattr(user, 'check_password') and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
