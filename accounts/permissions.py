from rest_framework.permissions import BasePermission
from accounts.models import User

class IsVerifiedUser(BasePermission):
    def has_permission(self, request, view):
        email = request.data.get('email') or request.query_params.get('email')
        if not email:
            return False

        try:
            user = User.objects.get(email=email)
            return user.is_verified
        except User.DoesNotExist:
            return False