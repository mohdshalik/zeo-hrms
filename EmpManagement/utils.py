def get_current_schema_from_domain(request):
    # Assuming the schema name is the first part of the domain name
    domain = request.get_host()
    schema_name = domain.split('.')[0]
    return schema_name



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_dynamic_email(subject, template_name, context, from_email, to_email, smtp_server, smtp_port, smtp_user, smtp_password):
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    part1 = MIMEText(plain_message, 'plain')
    part2 = MIMEText(html_message, 'html')

    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()
