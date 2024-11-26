from rest_framework import permissions


class LanguageMasterPermission(permissions.BasePermission):
    """
    Custom permission to allow only users with specific permissions to access the LanguageMaster model.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if the user has tenant-specific permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Allow access to superusers
        if user_permissions.is_superuser:
            return True

        # Define the required permissions
        required_permissions = [
            'view_languagemaster',
            'add_languagemaster',
            'change_languagemaster',
            'delete_languagemaster',
        ]

        # Collect the user's group permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if the user has any of the required permissions
        return any(permission in user_group_permissions for permission in required_permissions)