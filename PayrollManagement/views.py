from django.shortcuts import render
from .models import (SalaryComponent,EmployeeSalaryStructure,PayslipComponent,Payslip,PayrollRun,LoanType,LoanApplication,
                     LoanRepayment,LoanApprovalLevels,LoanApproval)
from .serializer import (SalaryComponentSerializer,EmployeeSalaryStructureSerializer,PayrollRunSerializer,PayslipSerializer,PaySlipComponentSerializer,LoanTypeSerializer,LoanApplicationSerializer,LoanRepaymentSerializer,
                         LoanApprovalSerializer,LoanApprovalLevelsSerializer,EmpBulkuploadSalaryStructureSerializer)
from django.shortcuts import render
from .models import (SalaryComponent,EmployeeSalaryStructure,PayrollRun,Payslip,PayslipComponent,LoanType,LoanApplication,
                     LoanRepayment,LoanApprovalLevels,LoanApproval)
from .serializer import (SalaryComponentSerializer,EmployeeSalaryStructureSerializer,PayslipSerializer,PaySlipComponentSerializer,LoanTypeSerializer,LoanApplicationSerializer,LoanRepaymentSerializer,
                         LoanApprovalSerializer,LoanApprovalLevelsSerializer,PayrollRunSerializer,PayslipConfirmedSerializer)
from rest_framework import status,generics,viewsets,permissions
from .permissions import(SalaryComponentPermission,EmployeeSalaryStructurePermission,PayrollRunPermission,PayslipComponentPermission,PayslipPermission)
from .resource import EmployeeSalaryStructureResource
from EmpManagement.models import emp_master
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from tablib import Dataset
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from .utils import generate_payslip_pdf,send_payslip_email
from .models import (SalaryComponent,EmployeeSalaryStructure,PayrollRun,Payslip,PayslipComponent,LoanType,LoanApplication,
                     LoanRepayment,LoanApprovalLevels,LoanApproval)
from .serializer import (SalaryComponentSerializer,EmployeeSalaryStructureSerializer,PayslipSerializer,PaySlipComponentSerializer,LoanTypeSerializer,LoanApplicationSerializer,LoanRepaymentSerializer,
                         LoanApprovalSerializer,LoanApprovalLevelsSerializer,PayrollRunSerializer)
from rest_framework import status,generics,viewsets,permissions
import datetime
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

class PayslipViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer

    @action(detail=False, methods=['get'], url_path='employee/(?P<emp_code>[^/.]+)/download/(?P<year>\d{4})/(?P<month>\d{1,2})')
    def download_employee_payslip_by_month(self, request, emp_code=None, year=None, month=None):
        """Download a payslip for a specific employee for a given month and year."""
        try:
            # Ensure month and year are integers
            month = int(month)
            year = int(year)
            if not 1 <= month <= 12:
                return Response({"error": "Month must be between 1 and 12"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the employee by emp_code
            try:
                employee = emp_master.objects.get(emp_code=emp_code)
            except emp_master.DoesNotExist:
                return Response(
                    {"error": f"No employee found with emp_code {emp_code}"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Fetch the payslip for the employee, month, and year
            payslip = Payslip.objects.get(
                employee=employee,
                payroll_run__month=month,
                payroll_run__year=year
            )
            return generate_payslip_pdf(request, payslip)
        except Payslip.DoesNotExist:
            return Response(
                {"error": f"No payslip found for employee {emp_code} for {month}/{year}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response({"error": "Invalid year or month format"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='employee/(?P<employee_id>\d+)/filter/(?P<year>\d{4})/(?P<month>\d{1,2})')
    def filter_employee_payslip_by_month(self, request, employee_id=None, year=None, month=None):
        """Retrieve payslip data for a specific employee for a given month and year."""
        try:
            # Ensure month and year are integers
            month = int(month)
            year = int(year)
            if not 1 <= month <= 12:
                return Response({"error": "Month must be between 1 and 12"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the payslip for the employee, month, and year
            payslip = Payslip.objects.get(
                employee_id=employee_id,
                payroll_run__month=month,
                payroll_run__year=year
            )
            serializer = self.get_serializer(payslip)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Payslip.DoesNotExist:
            return Response(
                {"error": f"No payslip found for employee {employee_id} for {month}/{year}"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response({"error": "Invalid year or month format"}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=True, methods=['post'], url_path='upload-pdf')
    def upload_pdf(self, request, pk=None):
        payslip = self.get_object()
        pdf_file = request.FILES.get('payslip_pdf')
        send_email = request.data.get('send_email', False)

        if not pdf_file:
            return Response({'error': 'PDF file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        payslip.payslip_pdf.save(pdf_file.name, pdf_file, save=True)

        email_sent = False
        if send_email:
            try:
                email_sent = send_payslip_email(payslip)
            except Exception as e:
                # Catch any uncaught exceptions and just log
                logger.exception(f"Unhandled error sending email for payslip {payslip.id}: {str(e)}")

        message = "PDF uploaded."
        if send_email:
            if email_sent:
                message += " Email sent successfully."
            else:
                if payslip.employee.emp_personal_email:
                    message += " Email failed."
                else:
                    message += " Email skipped (no personal email)."

        return Response({'message': message}, status=status.HTTP_200_OK)

class PayslipComponentViewSet(viewsets.ModelViewSet):
    queryset = PayslipComponent.objects.all()
    serializer_class = PaySlipComponentSerializer


class PayrollRunViewSet(viewsets.ModelViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer

class EmpBulkuploadSalaryStructureViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSalaryStructure.objects.all()
    serializer_class = EmpBulkuploadSalaryStructureSerializer
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        if request.method == 'POST' and request.FILES.get('file'):
            excel_file = request.FILES['file']
            if excel_file.name.endswith('.xlsx'):
                try:
                    dataset = Dataset()
                    dataset.load(excel_file.read(), format='xlsx')
                    resource = EmployeeSalaryStructureResource()
                    all_errors = []
                    valid_rows = []
                    with transaction.atomic():
                        for row_idx, row in enumerate(dataset.dict, start=2):
                            row_errors = []
                            try:
                                resource.before_import_row(row, row_idx=row_idx)
                            except ValidationError as e:
                                row_errors.extend([f"Row {row_idx}: {error}" for error in e.messages])
                            if row_errors:
                                all_errors.extend(row_errors)
                            else:
                                valid_rows.append(row)

                    if all_errors:
                        return Response({"errors": all_errors}, status=400)

                    with transaction.atomic():
                        result = resource.import_data(dataset, dry_run=False, raise_errors=True)

                    return Response({"message": f"{result.total_rows} records created successfully"})
                except Exception as e:
                    return Response({"error": str(e)}, status=400)
            else:
                return Response({"error": "Invalid file format. Only Excel files (.xlsx) are supported."}, status=400)
        else:
            return Response({"error": "Please provide an Excel file."}, status=400)
class PayslipConfirmedViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipConfirmedSerializer
    def get_queryset(self):
        return Payslip.objects.filter(status='processed')

class LoanTypeviewset(viewsets.ModelViewSet):
    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer

class LoanApplicationviewset(viewsets.ModelViewSet):
    queryset = LoanApplication.objects.all()
    serializer_class = LoanApplicationSerializer
    @action(detail=False, methods=['get'], url_path='paused-loans')
    def paused_loans(self, request):
        paused_loans = self.queryset.filter(status='Paused')
        serializer = self.get_serializer(paused_loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
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
class PayslipConfirmedViewSet(viewsets.ModelViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipConfirmedSerializer
    def get_queryset(self):
        return Payslip.objects.filter(status='processed')
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
