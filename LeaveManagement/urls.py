from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (Applicableviewset,LeaveTypeviewset,LeaveEntitlementviewset,LeaveRequestviewset,LeaveTypeViewSet,leave_balance_viewset,Acrualviewset,Resetviewset,
                    AttendanceViewSet,ShiftViewSet,WeeklyShiftScheduleViewSet,ImportAttendanceViewSet,EmployeeMachineMappingViewset,Leave_ReportViewset,LvApprovalLevelViewset,
                    LvApprovalViewset
                   
)

router = DefaultRouter()
router.register(r'applicable_to', Applicableviewset, basename='leave_applicable')
router.register(r'Leave_balance', leave_balance_viewset, basename='accrual')
router.register(r'accrual', Acrualviewset, basename='acruak')
router.register(r'reset', Resetviewset, basename='reset')
# router.register(r'enchash', Enchashviewset, basename='enchash')
router.register(r'leave-type', LeaveTypeviewset, basename='leave_type')
router.register(r'leave-entitlement', LeaveEntitlementviewset, basename='leave_entitlement')
# router.register(r'leave-policy', LeavePolicyviewset, basename='leave_policy')
router.register(r'emp-leave', LeaveRequestviewset, basename='emp_leave')
router.register(r'emp-foreign', LeaveTypeViewSet, basename='emp_foreign')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'shifts', ShiftViewSet,basename='shifts')
router.register(r'schedule-weekly-shifts', WeeklyShiftScheduleViewSet,basename='schedule-weekly_shifts')
router.register(r'import-attendance', ImportAttendanceViewSet,basename='import-attendance')
router.register(r'employee-mapping', EmployeeMachineMappingViewset, basename='employee-mapping')
router.register(r'leave-report', Leave_ReportViewset, basename='leave-report')
router.register(r'leave-approval-levels', LvApprovalLevelViewset, basename='leave-approval-levels')
router.register(r'leave-approvals', LvApprovalViewset, basename='leave-approvals')
urlpatterns = [
    # Other paths
    path('api/', include(router.urls)),
   

   
]
