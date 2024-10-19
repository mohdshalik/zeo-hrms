from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from .models import CustomUser

UserModel = get_user_model()
class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            # Check if the username provided is an email
            if '@' in username:
                user = CustomUser.objects.get(email=username)
            else:
                user = CustomUser.objects.get(username=username)

            
            if user.is_superuser and user.check_password(password):
                return user
            elif not user.is_superuser and user.check_password(password):
                return user
            else:
                return None                
        except UserModel.DoesNotExist:
            return None
    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None