from django.shortcuts import render
from .models import (SalaryComponent,EmployeeSalaryStructure,PayrollFormula,PayrollRun,Payslip,PayslipComponent,LoanType,LoanApplication,
                     LoanRepayment,LoanApprovalLevels,LoanApproval)
from .serializer import (SalaryComponentSerializer,EmployeeSalaryStructureSerializer,PayrollFormulaSerializer,PayslipSerializer,PaySlipComponentSerializer,LoanTypeSerializer,LoanApplicationSerializer,LoanRepaymentSerializer,
                         LoanApprovalSerializer,LoanApprovalLevelsSerializer,PayrollRunSerializer)
from rest_framework import status,generics,viewsets,permissions
from EmpManagement.models import emp_master
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from .utils import process_payroll,generate_payslip_pdf 
import logging

# Set up logging
logger = logging.getLogger(__name__)
# Create your views here.


class SalaryComponentViewSet(viewsets.ModelViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer


class EmployeeSalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSalaryStructure.objects.all()
    serializer_class = EmployeeSalaryStructureSerializer

class PayrollFormulaViewSet(viewsets.ModelViewSet):
    queryset = PayrollFormula.objects.all()
    serializer_class = PayrollFormulaSerializer

class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
    @action(detail=False, methods=['get'], url_path='employee/(?P<employee_id>\d+)/download/(?P<year>\d{4})/(?P<month>\d{1,2})')
    def download_employee_payslip_by_month(self, request, employee_id=None, year=None, month=None):
        """Download a payslip for a specific employee for a given month and year."""
        try:
            # Ensure month is an integer between 1 and 12
            month = int(month)
            if not 1 <= month <= 12:
                return Response({"error": "Month must be between 1 and 12"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the payslip for the employee, year, and month
            payslip = Payslip.objects.get(
                employee_id=employee_id,
                payroll_run__year=year,
                payroll_run__month=month
            )
            return generate_payslip_pdf(request, payslip)  # Pass the request to the PDF generation function
        except Payslip.DoesNotExist:
            return Response({"error": f"No payslip found for employee {employee_id} for {month}/{year}"}, 
                           status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid year or month format"}, status=status.HTTP_400_BAD_REQUEST)
    
class PayslipComponentViewSet(viewsets.ModelViewSet):
    queryset = PayslipComponent.objects.all()
    serializer_class = PaySlipComponentSerializer


class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payroll_run = serializer.save()  # Save the PayrollRun instance

        # Trigger payslip generation
        try:
            process_payroll(payroll_run.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            # Rollback and return error if formula evaluation fails
            payroll_run.delete()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'], url_path='employee/(?P<employee_id>\d+)/download/(?P<payslip_id>\d+)')
    def download_employee_payslip(self, request, employee_id=None, payslip_id=None):
        """Download a specific payslip for a given employee."""
        try:
            payslip = Payslip.objects.get(employee_id=employee_id, id=payslip_id)
            return generate_payslip_pdf(payslip)
        except Payslip.DoesNotExist:
            return Response({"error": "Payslip not found for this employee"}, status=status.HTTP_404_NOT_FOUND)

class LoanTypeviewset(viewsets.ModelViewSet):
    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer

class LoanApplicationviewset(viewsets.ModelViewSet):
    queryset = LoanApplication.objects.all()
    serializer_class = LoanApplicationSerializer
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause loan repayments with a reason."""
        loan = self.get_object()
        pause_date = request.data.get('pause_start_date')
        reason = request.data.get('pause_reason')

        if not pause_date:
            return Response({"error": "Pause start date is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            loan.pause(start_date=pause_date, reason=reason)
            return Response({"status": "paused", "pause_date": pause_date, "reason": reason}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume loan repayments with a reason."""
        loan = self.get_object()
        resume_date = request.data.get('resume_date')
        reason = request.data.get('resume_reason')

        if not resume_date:
            return Response({"error": "Resume date is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            loan.resume(resume_date=resume_date, reason=reason)
            return Response({"status": "resumed", "resume_date": resume_date, "reason": reason}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class LoanRepaymentviewset(viewsets.ModelViewSet):
    queryset = LoanRepayment.objects.all()
    serializer_class = LoanRepaymentSerializer

class LoanApprovalLevelsviewset(viewsets.ModelViewSet):
    queryset = LoanApprovalLevels.objects.all()
    serializer_class = LoanApprovalLevelsSerializer

class LoanApprovalviewset(viewsets.ModelViewSet):
    queryset = LoanApproval.objects.all()
    serializer_class = LoanApprovalSerializer
    lookup_field = 'pk'

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approvals = self.get_object()
        note = request.data.get('note')  # Get the note from the request
        approvals.approve(note=note)
        return Response({'status': 'approved', 'note': note}, status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        approval = self.get_object()
        note = request.data.get('note')
        rejection_reason_id = request.data.get('rejection_reason')

        if not rejection_reason_id:
            raise ValidationError("Rejection reason is required.")

        # try:
        #     rejection_reason = LvRejectionReason.objects.get(id=rejection_reason_id)
        # except LvRejectionReason.DoesNotExist:
        #     raise ValidationError("Invalid rejection reason.")

        approval.reject(rejection_reason=rejection_reason_id, note=note)
        return Response({'status': 'rejected', 'note': note, 'rejection_reason': rejection_reason_id}, status=status.HTTP_200_OK)
