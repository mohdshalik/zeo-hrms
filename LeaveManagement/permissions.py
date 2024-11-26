from rest_framework import permissions

from tenant_users.tenants.models import UserTenantPermissions

class LeaveTypePermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for leave_type.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for leave_type model actions
        required_permissions = ['view_leave_type', 'add_leave_type', 'change_leave_type', 'delete_leave_type']

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [p.codename for group in user_permissions.groups.all() for p in group.permissions.all()]
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False

class LeaveEntitlementPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for leave_entitlement.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for leave_entitlement model actions
        required_permissions = [
            'view_leave_entitlement',
            'add_leave_entitlement',
            'change_leave_entitlement',
            'delete_leave_entitlement'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]
        
        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False

class EmpLeaveBalancePermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for emp_leave_balance.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for emp_leave_balance model actions
        required_permissions = [
            'view_emp_leave_balance',
            'add_emp_leave_balance',
            'change_emp_leave_balance',
            'delete_emp_leave_balance'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class ApplicabilityCriteriaPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for applicability_criteria.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for applicability_criteria model actions
        required_permissions = [
            'view_applicability_criteria',
            'add_applicability_criteria',
            'change_applicability_criteria',
            'delete_applicability_criteria'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False



class EmployeeLeaveRequestPermission(permissions.BasePermission):
    """
    Custom permission to allow specific users to access and create leave requests.
    ESS users can only access and create requests for their own employee ID.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Grant access if the user is a superuser
        if request.user.is_superuser:
            return True

        # Check if the user has is_ess=True
        if hasattr(request.user, 'is_ess') and request.user.is_ess:
            # If accessing or creating, ensure they are limited to their own employee record
            employee_id = request.user.username  # Assuming username represents the employee ID

            # For read actions, ensure user only sees their own employee details
            if view.action in ['retrieve', 'list']:
                requested_employee_id = view.kwargs.get('pk')
                return str(requested_employee_id) == str(employee_id)
            
            # For create actions, ensure the leave request is for the user's own employee ID
            if view.action == 'create':
                # In the viewset, ensure `employee_id` is automatically set to the user's employee ID
                return True

        # Retrieve permissions for other users
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for employee model actions
        required_permissions = ['view_employee_leave_request', 'delete_employee_leave_request', 'add_employee_leave_request', 'change_employee_leave_request']
        user_group_permissions = [p.codename for group in user_permissions.groups.all() for p in group.permissions.all()]

        # Allow access if the user's group has any of the necessary permissions
        return any(permission in user_group_permissions for permission in required_permissions)

class LvEmailTemplatePermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for LvEmailTemplate.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for LvEmailTemplate model actions
        required_permissions = [
            'view_lvemailtemplate',
            'add_lvemailtemplate',
            'change_lvemailtemplate',
            'delete_lvemailtemplate'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class LvCommonWorkflowPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for LvCommonWorkflow.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for LvCommonWorkflow model actions
        required_permissions = [
            'view_lvcommonworkflow',
            'add_lvcommonworkflow',
            'change_lvcommonworkflow',
            'delete_lvcommonworkflow'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class LvRejectionReasonPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for LvRejectionReason.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for LvRejectionReason model actions
        required_permissions = [
            'view_lvrejectionreason',
            'add_lvrejectionreason',
            'change_lvrejectionreason',
            'delete_lvrejectionreason'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False

class LeaveApprovalLevelsPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for LeaveApprovalLevels.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for LeaveApprovalLevels model actions
        required_permissions = [
            'view_leaveapprovallevels',
            'add_leaveapprovallevels',
            'change_leaveapprovallevels',
            'delete_leaveapprovallevels'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class EmployeeMachineMappingPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for EmployeeMachineMapping.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for EmployeeMachineMapping model actions
        required_permissions = [
            'view_employeemachinemapping',
            'add_employeemachinemapping',
            'change_employeemachinemapping',
            'delete_employeemachinemapping'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False

class ShiftPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for Shift.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for Shift model actions
        required_permissions = [
            'view_shift',
            'add_shift',
            'change_shift',
            'delete_shift'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class WeeklyShiftSchedulePermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for WeeklyShiftSchedule.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for WeeklyShiftSchedule model actions
        required_permissions = [
            'view_weeklyshiftschedule',
            'add_weeklyshiftschedule',
            'change_weeklyshiftschedule',
            'delete_weeklyshiftschedule'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False

class AttendancePermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for Attendance.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for Attendance model actions
        required_permissions = [
            'view_attendance',
            'add_attendance',
            'change_attendance',
            'delete_attendance'
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class LeaveReportPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for LeaveReport.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for LeaveReport model actions
        required_permissions = [
            'view_leavereport',
            'add_leavereport',
            'change_leavereport',
            'delete_leavereport',
            # 'export_report'  # Custom permission for exporting reports
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False

class LeaveApprovalReportPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for LeaveApprovalReport.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for LeaveApprovalReport model actions
        required_permissions = [
            'view_leaveapprovalreport',
            'add_leaveapprovalreport',
            'change_leaveapprovalreport',
            'delete_leaveapprovalreport',
            # 'export_report'  # Custom permission for exporting reports
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class AttendanceReportPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for AttendanceReport.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for AttendanceReport model actions
        required_permissions = [
            'view_attendancereport',
            'add_attendancereport',
            'change_attendancereport',
            'delete_attendancereport',
            # 'export_report'  # Custom permission for exporting reports
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False


class LvBalanceReportPermission(permissions.BasePermission):
    """
    Custom permission to allow users with specific permissions for LvBalanceReport.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Attempt to retrieve user permissions
        try:
            user_permissions = UserTenantPermissions.objects.get(profile=request.user)
        except UserTenantPermissions.DoesNotExist:
            return False

        # Define required permissions for lvBalanceReport model actions
        required_permissions = [
            'view_lvbalancereport',
            'add_lvbalancereport',
            'change_lvbalancereport',
            'delete_lvbalancereport',
            'export_report'  # Custom permission for exporting reports
        ]

        # Check if any group the user belongs to has the required permissions
        user_group_permissions = [
            p.codename for group in user_permissions.groups.all() for p in group.permissions.all()
        ]

        # Check if user has at least one of the required permissions
        if any(permission in user_group_permissions for permission in required_permissions):
            return True

        return False