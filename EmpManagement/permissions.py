from rest_framework import permissions
from tenant_users.tenants.models import UserTenantPermissions
class IsSuperUserOrHasGeneralRequestPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow superusers full access
        if request.user.is_superuser:
            return True

        # Non-superusers: Check specific permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions
        required_permissions = [
            'view_GeneralRequest',
            'delete_GeneralRequest',
            'add_GeneralRequest',
            'change_GeneralRequest'
        ]

        # Check if the user has the necessary permissions
        for permission in required_permissions:
            if permission in [p.codename for p in user_permissions.group.permissions.all()]:
                return True

        return False

    def has_object_permission(self, request, view, obj):
        # Allow superusers full access
        if request.user.is_superuser:
            return True

        # Check if user is associated with the request (is_ess = True)
        if request.user.is_ess and request.user.username == obj.employee.emp_code:
            return True

        return False
    
class IsSuperUserOrInSameBranch(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow access to superusers
        if request.user.is_superuser:
            return True
        
        
        # Allow access to authenticated users
        if request.user.is_authenticated:
            return True
        # Deny access to unauthenticated users
        return False

    #     # Non-superusers: Check specific permissions
    #     try:
    #         user_permissions = UserTenantPermissions.objects.get(profile=request.user)
    #     except UserTenantPermissions.DoesNotExist:
    #         return False

    #     # Define required permissions
    #     required_permissions = [
    #         'view_report',
    #         'delete_report',
    #         'add_report',
    #         'change_report',
    #         'export_report'
    #     ]

    #     # Check if the user has the necessary permissions
    #     for permission in required_permissions:
    #         if permission in [p.codename for p in user_permissions.group.permissions.all()]:
    #             return True

    #     return False


    # def has_object_permission(self, request, view, obj):
    #     # Allow access to superusers
    #     if request.user.is_superuser:
    #         return True
        
    #     # Allow access to authenticated users in the same branch
    #     if request.user.is_authenticated:
    #         user_branch_id = request.user.branches
    #         return user_branch_id == obj.branches
        
    #     # Deny access to unauthenticated users
    #     return False