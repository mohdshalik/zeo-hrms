from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (SalaryComponentViewSet,EmployeeSalaryStructureViewSet,PayslipViewSet,PayrollRunViewSet,PayslipComponentViewSet,LoanTypeviewset,LoanApplicationviewset,LoanRepaymentviewset,LoanApprovalviewset,LoanApprovalLevelsviewset,
                    EmpBulkuploadSalaryStructureViewSet
                    
                    )


router = DefaultRouter()
router.register(r'salarycomponent', SalaryComponentViewSet)
router.register(r'employeesalary', EmployeeSalaryStructureViewSet)
router.register(r'PayrollRun', PayrollRunViewSet)
router.register(r'bulk-upload-salary', EmpBulkuploadSalaryStructureViewSet,basename='bulk-upload-salary')
router.register(r'payslip', PayslipViewSet)
router.register(r'PayslipComponent', PayslipComponentViewSet)
router.register(r'loan-type', LoanTypeviewset, basename='loan-type')
router.register(r'loan-application', LoanApplicationviewset, basename='loan-application')
router.register(r'loan-repayment', LoanRepaymentviewset, basename='loan-repayment')
router.register(r'loan-approval-levels', LoanApprovalLevelsviewset, basename='loan-approval-levels')
router.register(r'loan-approval', LoanApprovalviewset, basename='loan-approval')

urlpatterns = [
    path('api/', include(router.urls)),
]