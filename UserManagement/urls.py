from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from . import views
from .views import RegisterUserAPIView,CompanyViewSet,DomainViewSet,TenantUserListView




router = DefaultRouter()

router.register(r'user', RegisterUserAPIView)
router.register(r'company', CompanyViewSet)
router.register(r'domain', DomainViewSet)
# router.register(r'request', ApprovalViewset,basename='request')
# router.register(r'Role-Grouping', UserRolesViewSet)
# router.register(r'permissions', PermissionViewSet)
# router.register(r'UserandPermissionGrouping', UserandPermissionGrouping)
# Create a nested router for approvals
# approval_router = routers.NestedDefaultRouter(user_router, r'users', lookup='user')
# nested_router = routers.NestedDefaultRouter(router, r'user', lookup='user')
# nested_router.register(r'request-approvals', ApprovalViewset, basename='user-request-approvals')


urlpatterns = [
    # Other paths
    path('api/', include(router.urls)),
    path("token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('tenant-users/', TenantUserListView.as_view(), name='tenant-user-list'),
    

    # path('api/userregister/',RegisterUserAPIView.as_view()),
    # path('api/userlist/', UserListView.as_view(), ),
    # path('company-fiscal-data/<int:company_id>/', CompanyFiscalData.as_view(), name='company-fiscal-data'),
    # path('profile_pic/<str:filename>/', profile_pic_view, name='profile_pic'),
    # path('countries/<int:pk>/', StateByCountryAPIView.as_view(), name='states-by-country'),

]