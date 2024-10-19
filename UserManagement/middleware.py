from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from django_tenants.utils import tenant_context

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