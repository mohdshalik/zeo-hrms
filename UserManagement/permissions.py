from rest_framework import permissions
# 

from .models import CustomUser
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from rest_framework.permissions import BasePermission
from tenant_users.tenants.models import UserTenantPermissions
class UserPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if view.action == 'list':
            return request.user.is_authenticated() and request.user.is_admin
        elif view.action == 'create':
            return True
        elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return True
        else:
            return False
                                                                                                
    def has_object_permission(self, request, view, obj):
        # Deny actions on objects if the user is not authenticated
        if not request.user.is_authenticated():
            return False

        if view.action == 'retrieve':
            return obj == request.user or request.user.is_admin
        elif view.action in ['update', 'partial_update']:
            return obj == request.user or request.user.is_admin
        elif view.action == 'destroy':
            return request.user.is_admin
        else:
            return False

class IsEssUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow is_ess users to view their own data.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for all users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed for is_ess users editing their own data
        return obj.is_ess and obj == request.user

# class IsSuperuserOrReadOnly(permissions.BasePermission):
#     """
#     Custom permission to allow superusers to edit, delete any instance,
#     but allow read-only access to other users.
#     """

#     def has_permission(self, request, view):
#         # Allow read-only permissions for non-superusers
#         if request.method in permissions.SAFE_METHODS:
#             return True
        
#         # Allow superusers to perform any action
#         return request.user and request.user.is_superuser
        
#superuser class for permission
#important
from rest_framework.permissions import IsAdminUser
class IsSuperUser(IsAdminUser):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)



class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class BranchPermission(permissions.BasePermission):
    """
    Custom permission to only allow users with specific object-level permissions.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True


        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Grant access if the user is a superuser
        if user_permissions.is_superuser:
            return True

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_brnch_mstr', 'delete_brnch_mstr', 'add_brnch_mstr', 'change_brnch_mstr']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False


class EmployeePermission(permissions.BasePermission):
    """
    Custom permission to only allow users with specific permissions to access company API.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Grant access if the user is a superuser in the user model
        if request.user.is_superuser:
            return True

        # Grant access if the user has is_ess=True in the user model
        if hasattr(request.user, 'is_ess') and request.user.is_ess:
            return True

        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_emp_master', 'delete_emp_master', 'add_emp_master', 'change_emp_master']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False
class DepartmentPermission(permissions.BasePermission):
    """
    Custom permission to only allow users with specific permissions to access company API.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Grant access if the user is a superuser
        if user_permissions.is_superuser:
            return True

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_dept_master', 'delete_dept_master', 'add_dept_master', 'change_dept_master']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False

    


class DesignationPermission(BasePermission):
    """
    Custom permission to only allow users with specific permissions or superuser status to access the company API.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Grant access if the user is a superuser
        if user_permissions.is_superuser:
            return True

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_desgntn_master', 'delete_desgntn_master', 'add_desgntn_master', 'change_desgntn_master']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False
    
class CategoryPermission(permissions.BasePermission):
    """
    Custom permission to only allow users with specific permissions to access company API.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Grant access if the user is a superuser
        if user_permissions.is_superuser:
            return True

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_ctgry_master', 'delete_ctgry_master', 'add_ctgry_master', 'change_ctgry_master']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False


class CountryPermission(permissions.BasePermission):
    """
    Custom permission to only allow users with specific permissions to access company API.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Grant access if the user is a superuser
        if user_permissions.is_superuser:
            return True

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_cntry_mstr', 'delete_cntry_mstr', 'add_cntry_mstr', 'change_cntry_mstr']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False

class StatePermission(permissions.BasePermission):
    """
    Custom permission to only allow users with specific permissions to access company API.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Grant access if the user is a superuser
        if user_permissions.is_superuser:
            return True

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_state_mstr', 'delete_state_mstr', 'add_state_mstr', 'change_state_mstr']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False


class DocTypePermission(permissions.BasePermission):
    """
    Custom permission to only allow users with specific permissions to access company API.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Retrieve UserTenantPermissions efficiently using get (if unique) or filter
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Grant access if the user is a superuser
        if user_permissions.is_superuser:
            return True

        # Check if the user's group has any of the necessary permissions
        required_permissions = ['view_document_type', 'delete_document_type', 'add_document_type', 'change_document_type']
        for group in user_permissions.groups.all():  # Access all related groups
            for permission in group.permissions.all():  # Access permissions of each group
                if permission.codename in required_permissions:
                    return True

        return False
