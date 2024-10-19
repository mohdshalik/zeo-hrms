from django.apps import AppConfig


class LeavemanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'LeaveManagement'
    def ready(self):
        import LeaveManagement.signals  # Import the signal handlers
