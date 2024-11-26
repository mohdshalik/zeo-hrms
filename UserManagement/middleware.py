from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from django_tenants.utils import tenant_context
from django.utils import timezone
import pytz

class TenantSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        if session_key:
            request.session = SessionStore(session_key=session_key)
            tenant = request.session.get('tenant')
            if tenant:
                with tenant_context(tenant):
                    return None  # Return None to continue processing middleware
        return None
        
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import login
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection 

class SchemaAwareAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tenant = getattr(request, 'tenant', None)
        
        if tenant:
            # Switch to the tenant schema
            connection.set_schema(tenant.schema_name)
        else:
            # Assume we are in the public schema
            connection.set_schema_to_public()
        
        if request.user.is_authenticated:
            try:
                user = User.objects.get(username=request.user.username)
                login(request, user)
            except User.DoesNotExist:
                pass

        return None


class TenantTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(request, 'tenant', None)  # Get the current tenant

        if tenant and hasattr(tenant, 'country') and tenant.country:
            # Activate timezone based on the tenant's country
            tenant_timezone = tenant.country.timezone
            try:
                timezone.activate(pytz.timezone(tenant_timezone))
            except pytz.UnknownTimeZoneError:
                # Fallback to UTC if the tenant's timezone is invalid
                timezone.activate(pytz.utc)
        else:
            # Use the server's local timezone for public tenants
            from django.conf import settings
            timezone.activate(pytz.timezone(getattr(settings, 'TIME_ZONE', 'UTC')))

        response = self.get_response(request)

        # Deactivate timezone after the request is processed
        timezone.deactivate()
        return response