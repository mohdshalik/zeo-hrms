from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Attendance, leave_type,leave_entitlement
from .resource import AttendanceResource

@admin.register(Attendance)
class LeaveAdmin(ImportExportModelAdmin):
    resource_class = AttendanceResource

@admin.register(leave_type)
class LeavetypeAdmin(admin.ModelAdmin):
    pass
@admin.register(leave_entitlement)
class LeaveentitlementAdmin(admin.ModelAdmin):
    pass