from django.urls import path, include
from . views import (FiscalYearViewSet,PeriodViewSet,BranchViewSet,DepartmentViewSet,DocNumberingviewset,FiscalPeriodDatesView,
                     DesignationViewSet,CatogoryViewSet,CompanyFiscalData,permissionviewset,Groupviewset,permviewset,FiscalYearDatesView,DeptBulkUploadViewSet,DesignationBulkUploadViewSet,
                   save_notification_settings,CompanyPolicyViewSet,list_data_in_schema,AssetMasterViewSet,AssetTransactionViewSet,Asset_CustomFieldValueViewSet)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()



router.register(r'Branch', BranchViewSet)
router.register(r'Department', DepartmentViewSet)
router.register(r'Dept-bulkupload', DeptBulkUploadViewSet,basename='dept_bulkupload')
router.register(r'Designation', DesignationViewSet)
router.register(r'Desigtn-bulkupload', DesignationBulkUploadViewSet,basename='Desigtn_bulkupload')
router.register(r'Catogory', CatogoryViewSet)
router.register(r'fiscal-years', FiscalYearViewSet)
router.register(r'periods', PeriodViewSet)
router.register(r'permissions', permissionviewset)
router.register(r'Group', Groupviewset)
router.register(r'perm', permviewset)
router.register(r'document-numbering', DocNumberingviewset)
router.register(r'policies', CompanyPolicyViewSet, basename='companypolicy')
router.register(r'assets', AssetMasterViewSet, basename='asset-master')
router.register(r'asset-transactions', AssetTransactionViewSet, basename='asset-transaction')
router.register(r'asset-customfield', Asset_CustomFieldValueViewSet, basename='assets-customfield')
# router.register(r'e-attendance', AttendanceViewSet, basename='e-attendance')


urlpatterns = [
    # Other paths
    path('api/', include(router.urls)),

    path('company-fiscal-data/<int:company_id>/', CompanyFiscalData.as_view(), name='company-fiscal-data'),
    path('fiscal_periods/<int:fiscal_year_id>/<int:period_number>/dates/', FiscalPeriodDatesView.as_view(), name='fiscal-period-dates'),
    path('fiscal_years/<int:fiscal_year_id>/dates/', FiscalYearDatesView.as_view(), name='fiscal-year-dates'),
    path('save-notification-settings/', save_notification_settings, name='save-notification-settings'),
    path('policies/<int:policy_id>/download/', CompanyPolicyViewSet.as_view({'get': 'download_policy'}), name='download_policies'),
    path('api/schema-data/', list_data_in_schema, name='list_data_in_schema'),
    
    ]