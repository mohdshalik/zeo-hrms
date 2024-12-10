from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (EmpFamViewSet, EmpJobHistoryvSet, EmpViewSet,NotificationViewset,
                    Emp_QualificationViewSet, Emp_DocumentViewSet, EmpLeaveRequestViewSet,EmpbulkuploadViewSet,
                    CustomFieldViewset,EmpFam_CustomFieldViewset,EmpJobHistory_UdfViewset,EmpQf_UdfViewset,EmpDoc_UdfViewset,
                    Bulkupload_DocumentViewSet,LanguageSkillViewSet,ReportViewset,Doc_ReportViewset,GeneralReportViewset,
                    MarketingSkillViewSet,ProgrammingLanguageSkillViewSet,EmployeeSkillViewSet,LanguageBlkupldViewSet,MarketingBlkupldViewSet,
                    ProLangBlkupldViewSet,RequestTypeViewset,GeneralRequestViewset,EmpMarketSkillViewSet,EmpPrgrmSkillViewSet,
                    EmpLangSkillViewSet,ApprovalViewset,ApprovalLevelViewset,UserNotificationsViewSet,Emp_CustomFieldValueViewSet,EmailTemplateViewset,
                    EmailConfigurationViewSet,UpdateESSUserView,ESSUserListView,NotificationSettingsViewSet,DocExpEmailTemplateViewset,CommonWorkflowViewSet,)

# Define the main router for top-level routes
router = DefaultRouter()
router.register(r'Employee', EmpViewSet, basename='employee')
router.register(r'emp-BulkUpload', EmpbulkuploadViewSet, basename='emp_bulk_upload')
router.register(r'emp-report', ReportViewset, basename='emp_report')
router.register(r'doc-report',Doc_ReportViewset, basename='doc_report')
router.register(r'report-general-request', GeneralReportViewset, basename='report-general-request')
router.register(r'custom-field', CustomFieldViewset, basename='custom-field')
router.register(r'custom-field-value', Emp_CustomFieldValueViewSet, basename='custom-field-value')

router.register(r'emp-Family', EmpFamViewSet, basename='emp_family')
router.register(r'empfamily-UDF', EmpFam_CustomFieldViewset, basename='emp_fam_udf')
router.register(r'emp-JobHistory', EmpJobHistoryvSet, basename='emp_job_history')
router.register(r'empjob-history-UDF', EmpJobHistory_UdfViewset, basename='emp_job_history_udf')
router.register(r'emp-Qualification', Emp_QualificationViewSet, basename='emp_qualification')
router.register(r'empQualification-UDF', EmpQf_UdfViewset, basename='emp_qualification_udf')
router.register(r'emp-Documents', Emp_DocumentViewSet, basename='emp_document')
router.register(r'Bulkupload-Documents', Bulkupload_DocumentViewSet, basename='bulk_upload_document')
router.register(r'emp-Documents-UDF', EmpDoc_UdfViewset, basename='emp_document_udf')
router.register(r'emp-leave-request', EmpLeaveRequestViewSet)
router.register(r'notification', NotificationViewset, basename='employee-document-notification')
router.register(r'language_skill', LanguageSkillViewSet, basename='employee-language_skill')
router.register(r'marketing-skill', MarketingSkillViewSet, basename='employee-marketing_skill')
router.register(r'programming-skill', ProgrammingLanguageSkillViewSet, basename='employee-programming_skill')
router.register(r'employee-skill', EmployeeSkillViewSet, basename='employee_skill')
router.register(r'emp-market-skill',EmpMarketSkillViewSet, basename='emp_market_skill')
router.register(r'emp-program-skill',EmpPrgrmSkillViewSet, basename='emp_prgrm_skill')
router.register(r'emp-language-skill',EmpLangSkillViewSet, basename='emp_lang_skill')
router.register(r'language_bulkupload', LanguageBlkupldViewSet, basename='employee-language_bulkupload')
router.register(r'marketing_bulkupload', MarketingBlkupldViewSet, basename='employee-marketing_bulkupload')
router.register(r'programming_bulkupload', ProLangBlkupldViewSet, basename='employee-programming_bulkupload')
router.register(r'request-type', RequestTypeViewset, basename='request-type')
router.register(r'email-template', EmailTemplateViewset, basename='email-template')
router.register(r'general-request', GeneralRequestViewset, basename='general-request')
router.register(r'request-approvals', ApprovalViewset,basename='request_approvals')
router.register(r'request-approvals-levels', ApprovalLevelViewset,basename='request_approvals_levels')
router.register(r'request-notifications', UserNotificationsViewSet,basename='request-notifications')
router.register(r'email-config', EmailConfigurationViewSet, basename='email_config')
router.register(r'notification-settings', NotificationSettingsViewSet, basename='notification-settings')
router.register(r'doc-exp-emailtemplate', DocExpEmailTemplateViewset, basename='doc-exp-emailtemplate')
router.register(r'common-workflow', CommonWorkflowViewSet, basename='common_workflow')





# Define nested routes for accessing related resources under each employee
employee_router = DefaultRouter()
employee_router.register(r'emp-family', EmpFamViewSet, basename='employee-family')
employee_router.register(r'emp-jobhistory', EmpJobHistoryvSet, basename='employee-jobhistory')
employee_router.register(r'emp-qualification', Emp_QualificationViewSet, basename='employee-qualification')
employee_router.register(r'emp-documents', Emp_DocumentViewSet, basename='employee-documents')
employee_router.register(r'emp-leave-request', EmpLeaveRequestViewSet, basename='employee-leave-request')
employee_router.register(r'notification', NotificationViewset, basename='employee-document-notification')

# Define the URL patterns
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/Employee/<int:pk>/', include(employee_router.urls)),  # Nested routes for individual employees
    # path('link-user-to-employee/', LinkUserToEmployee.as_view(), name='link-user-to-employee'),
    path('api/ess-users/', ESSUserListView.as_view(), name='ess-user-list'),
    path('api/update-ess-user/', UpdateESSUserView.as_view(), name='update-ess-user'),


    

]
