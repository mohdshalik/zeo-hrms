from django.shortcuts import render
from .models import (SalaryComponent,EmployeeSalaryStructure,PayrollFormula,PayrollTransaction,Payslip,PaySlipComponent,LoanType,LoanApplication,
                     LoanRepayment,LoanApprovalLevels,LoanApproval)
from .serializer import (SalaryComponentSerializer,EmployeeSalaryStructureSerializer,PayrollFormulaSerializer,PayrollTransactionSerializer,PayslipSerializer,PaySlipComponentSerializer,LoanTypeSerializer,LoanApplicationSerializer,LoanRepaymentSerializer,
                         LoanApprovalSerializer,LoanApprovalLevelsSerializer)
from rest_framework import status,generics,viewsets,permissions
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from EmpManagement .models import emp_master
from decimal import Decimal
from django.utils.dateparse import parse_date
from .utils import evaluate_payroll_formula
# Create your views here.


class SalaryComponentViewSet(viewsets.ModelViewSet):
    queryset = SalaryComponent.objects.all()
    serializer_class = SalaryComponentSerializer


class EmployeeSalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSalaryStructure.objects.all()
    serializer_class = EmployeeSalaryStructureSerializer

from rest_framework.renderers import JSONRenderer
class PayrollTransactionViewSet(viewsets.ModelViewSet):
    queryset = PayrollTransaction.objects.all()
    serializer_class = PayrollTransactionSerializer
    renderer_classes = [JSONRenderer]

    @action(detail=False, methods=['post'], url_path='process-payroll')
    def process_payroll(self, request):
        try:
            # Extract data from request
            employee_id = request.data.get('employee_id')
            pay_period_start = request.data.get('pay_period_start')
            pay_period_end = request.data.get('pay_period_end')
            payment_date = request.data.get('payment_date')
            formula_id = request.data.get('formula_id')

            # Validate required fields
            if not all([employee_id, pay_period_start, pay_period_end, payment_date, formula_id]):
                return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch employee and formula
            try:
                employee = emp_master.objects.get(id=employee_id)
                formula = PayrollFormula.objects.get(id=formula_id, is_active=True)
            except emp_master.DoesNotExist:
                return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
            except PayrollFormula.DoesNotExist:
                return Response({"error": "Payroll formula not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

            # Calculate gross pay (sum of all additions)
            additions = EmployeeSalaryStructure.objects.filter(
                employee=employee, component__component_type='addition', is_active=True
            )
            gross_pay = sum(structure.amount or Decimal('0.00') for structure in additions)

            # Calculate net pay using formula
            net_pay = evaluate_payroll_formula(employee, formula.formula_text)

            # Create PayrollTransaction
            payroll_transaction = PayrollTransaction.objects.create(
                employee=employee,
                pay_period_start=parse_date(pay_period_start),
                pay_period_end=parse_date(pay_period_end),
                gross_pay=gross_pay,
                net_pay=net_pay,
                payment_date=parse_date(payment_date),
                status="pending"
            )

            # Serialize and return response
            serializer = self.get_serializer(payroll_transaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PayrollFormulaViewSet(viewsets.ModelViewSet):
    queryset = PayrollFormula.objects.all()
    serializer_class = PayrollFormulaSerializer

class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer


class PayslipComponentViewSet(viewsets.ModelViewSet):
    queryset = PaySlipComponent.objects.all()
    serializer_class = PaySlipComponentSerializer

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
