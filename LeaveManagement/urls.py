from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (Applicableviewset,LeaveTypeviewset,LeaveEntitlementviewset,LeaveRequestviewset,LeaveTypeViewSet,leave_balance_viewset,Acrualviewset,Resetviewset,
                    AttendanceViewSet,ShiftViewSet,ImportAttendanceViewSet,EmployeeMachineMappingViewset,Leave_ReportViewset,LvApprovalLevelViewset,
                    LvApprovalViewset,LvEmailTemplateviewset,LvApprovalNotifyviewset,LvCommonWorkflowViewset,LvRejectionViewset,Lv_Approval_ReportViewset,
                    AttendanceReportViewset,LvBalanceReportViewset,EmployeeYearlyCalendarViewset,ShiftPatternViewSet,EmployeeShiftScheduleViewSet,WeekPatternAssignmentVSet,
                    ShiftOverrideViewSet
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
router.register(r'emp-leave-request', LeaveRequestviewset, basename='emp_leave-request')
router.register(r'emp-foreign', LeaveTypeViewSet, basename='emp_foreign')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'shifts', ShiftViewSet,basename='shifts')
router.register(r'shiftpattern', ShiftPatternViewSet, basename='shiftpattern')
router.register(r'employee-shift', EmployeeShiftScheduleViewSet, basename='employee-shift')
router.register(r'weekpattern-assignment', WeekPatternAssignmentVSet, basename='weekpattern-assignment')
router.register(r'shift-overrides', ShiftOverrideViewSet, basename='shift-overrides')

router.register(r'import-attendance', ImportAttendanceViewSet,basename='import-attendance')
router.register(r'employee-mapping', EmployeeMachineMappingViewset, basename='employee-mapping')
router.register(r'leave-report', Leave_ReportViewset, basename='leave-report')
router.register(r'leave-approval-levels', LvApprovalLevelViewset, basename='leave-approval-levels')
router.register(r'leave-approvals', LvApprovalViewset, basename='leave-approvals')
router.register(r'leave-template', LvEmailTemplateviewset, basename='leave-template')
router.register(r'leave-ApprovalNotify', LvApprovalNotifyviewset, basename='leave-ApprovalNotify')
router.register(r'leave-common-workflow', LvCommonWorkflowViewset, basename='leave-common-workflow')
router.register(r'leave-rejection-reason', LvRejectionViewset, basename='leave-rejection-reason')
router.register(r'Lv_Approval_Report', Lv_Approval_ReportViewset, basename='Lv_Approval_Report')
router.register(r'AttendanceReport', AttendanceReportViewset, basename='AttendanceReport')
router.register(r'lvBalanceReport', LvBalanceReportViewset, basename='lvBalanceReport')
router.register(r'EmployeeYearlyCalendarViewset',EmployeeYearlyCalendarViewset , basename='EmployeeYearlyCalendarViewset')


urlpatterns = [
    # Other paths
    path('api/', include(router.urls)),
   

   
]
