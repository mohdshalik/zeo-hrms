from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
# from . import views
from .views import RegisterUserAPIView, CompanyViewSet, DomainViewset, TenantUserListView, CustomTokenObtainPairView, UserDetailView
from . import views
router = DefaultRouter()

router.register(r'user', RegisterUserAPIView)

router.register(r'company', CompanyViewSet)
router.register(r'domain', DomainViewset)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/user/<str:tenant_id>/', UserDetailView.as_view(), name='user-detail'),  # New path
    path("oauth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("oauth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('tenant-users/', TenantUserListView.as_view(), name='tenant-user-list'),
    
]