from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

class BranchEmailBackend(EmailBackend):
    def __init__(self, *args, **kwargs):
        self.branch_email_config = kwargs.pop('branch_email_config', {})
        super().__init__(*args, **kwargs)

    def open(self):
        if self.connection:
            return False

        # Set the email configuration dynamically
        self.host = self.branch_email_config.get('EMAIL_HOST', settings.EMAIL_HOST)
        self.port = self.branch_email_config.get('EMAIL_PORT', settings.EMAIL_PORT)
        self.username = self.branch_email_config.get('EMAIL_HOST_USER', settings.EMAIL_HOST_USER)
        self.password = self.branch_email_config.get('EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD)
        self.use_tls = self.branch_email_config.get('EMAIL_USE_TLS', settings.EMAIL_USE_TLS)
        self.use_ssl = self.branch_email_config.get('EMAIL_USE_SSL', settings.EMAIL_USE_SSL)

        return super().open()
