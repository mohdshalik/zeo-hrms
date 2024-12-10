# EmpManagement/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from .models import Emp_Documents,notification,SelectedEmpNotify,NotificationSettings,DocExpEmailTemplate
import logging
from django_tenants.utils import schema_context
from django_tenants.utils import get_tenant_model
from django.template import Template, Context
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import strip_tags
from celery import group
logger = logging.getLogger(__name__)
from django.contrib.auth import get_user_model


@shared_task
def send_document_expiry_notifications_for_all_tenants():
    tenants = get_all_tenant_schemas()
    for tenant_schema_name in tenants:
        with schema_context(tenant_schema_name):
            today = timezone.now().date()
            documents = Emp_Documents.objects.filter(is_active=True)

            preference = SelectedEmpNotify.objects.first()
            selected_employees = preference.selected_employees.all() if preference else []

            employee_expiry_notifications = {emp.id: [] for emp in selected_employees}

            if documents.exists():
                for document in documents:
                    expiry_date = document.emp_doc_expiry_date
                    if document.emp_id and document.emp_id.emp_branch_id:
                        branch = document.emp_id.emp_branch_id

                        try:
                            notification_settings = NotificationSettings.objects.get(branch=branch)
                            days_before_expiry = notification_settings.days_before_expiry
                            days_after_expiry = notification_settings.days_after_expiry
                        except NotificationSettings.DoesNotExist:
                            days_before_expiry = 7
                            days_after_expiry = 0

                        days_until_expiry = (expiry_date - today).days
                        days_since_expiry = (today - expiry_date).days

                        # Handle document expiring before the expiry date
                        if days_until_expiry == days_before_expiry:
                            send_document_notification(document, expiry_date, f"expiring in {days_before_expiry} days")
                            for emp in selected_employees:
                                employee_expiry_notifications[emp.id].append(
                                    f"- Document: {document.document_type} for {document.emp_id.emp_first_name} {document.emp_id.emp_last_name}, expiring in {days_before_expiry} days"
                                )

                        # Handle document expiring today
                        elif today == expiry_date:
                            send_document_notification(document, expiry_date, 'expired today')
                            for emp in selected_employees:
                                employee_expiry_notifications[emp.id].append(
                                    f"- Document: {document.document_type} for {document.emp_id.emp_first_name} {document.emp_id.emp_last_name}, expired today"
                                )

                        # Handle document already expired and within grace period
                        elif days_since_expiry == days_after_expiry and days_since_expiry > 0:
                            send_document_notification(document, expiry_date, 'expired')
                            for emp in selected_employees:
                                employee_expiry_notifications[emp.id].append(
                                    f"- Document: {document.document_type} for {document.emp_id.emp_first_name} {document.emp_id.emp_last_name}, expired {days_since_expiry} days ago"
                                )

                # Send the email notifications for each selected employee
                for emp in selected_employees:
                    if employee_expiry_notifications[emp.id]:
                        context = {
                            'ess_user_first_name': emp.emp_first_name,
                            'documents': "\n".join(employee_expiry_notifications[emp.id])
                        }
                        send_template_email('ESS User Notification', emp.emp_personal_email, context)

            else:
                print("No documents found that are expiring.")

def send_document_notification(document, expiry_date, status):
     # Message for the notification model
    notification_message = (
        f"The document '{document.document_type}' of '{document.emp_id.emp_first_name} {document.emp_id.emp_last_name}' "
        f"is {status} on {expiry_date}."
    )
    context = {
        'employee_first_name': document.emp_id.emp_first_name,
        'document_type': document.document_type,
        'status': status,
        'expiry_date': expiry_date
    }
    # Create a notification object in the Notification model
    notification.objects.create(
        message=notification_message,
        document_id=document
    )
    send_template_email('Employee Notification', document.emp_id.emp_personal_email, context)


def send_template_email(template_name, recipient_email, context):
    try:
        # Fetch the email template from the model
        email_template = DocExpEmailTemplate.objects.get(template_name=template_name)
        subject = email_template.subject
        template = Template(email_template.body)
        html_message = template.render(Context(context))
    except DocExpEmailTemplate.DoesNotExist:
        # If template is not found, fallback to default
        subject = "Notification"
        html_message = "This is a fallback notification."
        logger.error(f"Template {template_name} not found in the model.")

    logger.debug(f"Subject: {subject}")
    logger.debug(f"HTML Message: {html_message}")

    # Plain message for non-HTML clients
    plain_message = strip_tags(html_message)

    # Send the email
    send_mail(
        subject,
        plain_message,
        'approver312@gmail.com',  # Replace with your 'from' email
        [recipient_email],
        html_message=html_message,  # Send as HTML email
        fail_silently=False,
    )


def get_all_tenant_schemas():
    # Implement this function based on your tenant management system
    TenantModel = get_tenant_model()
    return TenantModel.objects.values_list('schema_name', flat=True)

