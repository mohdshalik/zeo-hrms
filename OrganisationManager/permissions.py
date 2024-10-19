from rest_framework.permissions import BasePermission
class IsOwnerOrReadOnly(BasePermission):
    """
    Allows access only to the owner of the object or for read-only actions.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read-only access for any user.
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Otherwise, require ownership of the object.
        return obj.owner == request.user