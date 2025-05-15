import re
from decimal import Decimal
from django.db import transaction
from .models import PayrollRun, Payslip, PayslipComponent, EmployeeSalaryStructure, SalaryComponent
import calendar
import logging

# Set up logging
logger = logging.getLogger(__name__)

def eval_formula(formula, components_dict):
    """Evaluate the payroll formula, defaulting missing components to 0."""
    import re
    # Extract variables from the formula
    variables = set(re.findall(r'[a-zA-Z_]+', formula))
    
    # Check for missing components
    missing_vars = [var for var in variables if var not in components_dict and var not in ['+', '-', '*', '/', '(', ')']]
    if missing_vars:
        logger.warning(f"Missing components in formula: {missing_vars}. Defaulting to 0.")
        for var in missing_vars:
            components_dict[var] = Decimal('0.00')
    
    # Replace component names with their values
    for name, value in components_dict.items():
        formula = formula.replace(name, str(value))
    
    try:
        return Decimal(str(eval(formula)))
    except Exception as e:
        raise ValueError(f"Error evaluating formula '{formula}': {e}")

# PayrollManagement/utils.py or PayrollManagement/pdf_utils.py
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from .models import Payslip, PayslipComponent
from calendars.models import EmployeeOvertime
import io
def generate_payslip_pdf(request, payslip):
    """Generate a PDF payslip for the given Payslip instance."""
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']

    company_name = request.tenant.name if hasattr(request, 'tenant') else "Default Company Name"
    elements.append(Paragraph(f"Company Name: {company_name}", title_style))
    elements.append(Paragraph(f"Payslip for {payslip.employee.emp_first_name} {payslip.employee.emp_last_name or ''}", normal_style))
    payroll_period = f"{payslip.payroll_run.start_date.strftime('%d %b %Y')} to {payslip.payroll_run.end_date.strftime('%d %b %Y')}"
    elements.append(Paragraph(f"Payroll Period: {payroll_period}", normal_style))
    elements.append(Paragraph(f"Working Days: {payslip.days_worked}/{payslip.total_working_days}", normal_style))

    # Add overtime hours if applicable
    overtime_component = PayslipComponent.objects.filter(payslip=payslip, component__code='OT').first()
    if overtime_component:
        overtime_records = EmployeeOvertime.objects.filter(
            employee=payslip.employee,
            date__gte=payslip.payroll_run.start_date,
            date__lte=payslip.payroll_run.end_date,
            approved=True
        )
        total_overtime_hours = sum(record.hours for record in overtime_records)
        elements.append(Paragraph(f"Overtime Hours: {total_overtime_hours}", normal_style))
    elements.append(Spacer(1, 12))

    # Employee details
    employee_details = [
        ["Employee Code", payslip.employee.emp_code],
        ["First Name", payslip.employee.emp_first_name],
        ["Last Name", payslip.employee.emp_last_name or "N/A"],
        ["Department", payslip.employee.emp_dept_id.dept_name if payslip.employee.emp_dept_id else "N/A"],
        ["Branch", payslip.employee.emp_branch_id.branch_name if payslip.employee.emp_branch_id else "N/A"],
        ["Designation", payslip.employee.emp_desgntn_id.desgntn_name if payslip.employee.emp_desgntn_id else "N/A"],
        ["Joining Date", payslip.employee.emp_joined_date.strftime("%Y-%m-%d")],
    ]
    employee_table = Table(employee_details, colWidths=[200, 200])
    employee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(employee_table)
    elements.append(Spacer(1, 12))

    # Salary components table
    components = PayslipComponent.objects.filter(payslip=payslip)
    data = [["Component", "Type", "Amount"]]
    for component in components:
        data.append([component.component.name, component.component.get_component_type_display(), f"{component.amount:.2f}"])

    data.append(["", "", ""])
    data.append(["Gross Salary", "", f"{payslip.gross_salary:.2f}"])
    data.append(["Total Additions", "", f"{payslip.total_additions:.2f}"])
    data.append(["Total Deductions", "", f"{payslip.total_deductions:.2f}"])
    data.append(["Net Salary", "", f"{payslip.net_salary:.2f}"])

    salary_table = Table(data, colWidths=[200, 100, 200])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
    ]))
    elements.append(salary_table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Generated by ZEO HRMS", normal_style))
    pdf.build(elements)

    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    filename = f"payslip_{payslip.employee.emp_code}_{payslip.payroll_run.start_date.strftime('%Y%m')}.pdf"
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response