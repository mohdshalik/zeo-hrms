from celery import shared_task
from django.core.mail import send_mail

@shared_task
def simple_task():
    send_mail(
        'Document Expiry Notification',
        'testing',
        'approver312@gmail.com',  # The 'from' email address
        ['subinasunil23@gmail.com'],  # Send to the employee's email
        fail_silently=False,
    )