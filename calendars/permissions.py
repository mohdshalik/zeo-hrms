from rest_framework import permissions

from tenant_users.tenants.models import UserTenantPermissions

class WeekendCalendarPermission(permissions.BasePermission):
    """
    Custom permission for the weekend_calendar model.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for weekend_calendar actions
        required_permissions = [
            'view_weekendcalendar',
            'add_weekendcalendar',
            'change_weekendcalendar',
            'delete_weekendcalendar'
        ]

        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        return any(permission in user_group_permissions for permission in required_permissions)


class WeekendDetailPermission(permissions.BasePermission):
    """
    Custom permission for the WeekendDetail model.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        required_permissions = [
            'view_weekenddetail',
            'add_weekenddetail',
            'change_weekenddetail',
            'delete_weekenddetail'
        ]

        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        return any(permission in user_group_permissions for permission in required_permissions)


class AssignWeekendPermission(permissions.BasePermission):
    """
    Custom permission for the assign_weekend model.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        required_permissions = [
            'view_assignweekend',
            'add_assignweekend',
            'change_assignweekend',
            'delete_assignweekend'
        ]

        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        return any(permission in user_group_permissions for permission in required_permissions)


class HolidayPermission(permissions.BasePermission):
    """
    Custom permission for the holiday model.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        required_permissions = [
            'view_holiday',
            'add_holiday',
            'change_holiday',
            'delete_holiday'
        ]

        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        return any(permission in user_group_permissions for permission in required_permissions)


class HolidayCalendarPermission(permissions.BasePermission):
    """
    Custom permission for the holiday_calendar model.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        required_permissions = [
            'view_holidaycalendar',
            'add_holidaycalendar',
            'change_holidaycalendar',
            'delete_holidaycalendar'
        ]

        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        return any(permission in user_group_permissions for permission in required_permissions)

class AssignHolidayPermission(permissions.BasePermission):
    """
    Custom permission for the assign_holiday model.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        required_permissions = [
            'view_assignholiday',
            'add_assignholiday',
            'change_assignholiday',
            'delete_assignholiday'
        ]

        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        return any(permission in user_group_permissions for permission in required_permissions)

