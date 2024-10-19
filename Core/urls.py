from django.urls import path, include
from .  views import (CountryViewSet,StateViewSet,CurrencyViewSet,LanguageViewSet,
                      DocumentViewSet,CountryBulkuploadViewSet,NationalityBlkupldViewSet)

from rest_framework.routers import DefaultRouter
router = DefaultRouter()

router.register(r'Country', CountryViewSet)
router.register(r'State', StateViewSet)
router.register(r'Bulk-Upload', CountryBulkuploadViewSet,basename='bulk_upload')
router.register(r'Nationality-Bulkupload', NationalityBlkupldViewSet,basename="nationality_bulkupload")
router.register(r'Currency', CurrencyViewSet)
router.register(r'Documents', DocumentViewSet)
router.register(r'language', LanguageViewSet)

urlpatterns = [
    # Other paths
    path('api/', include(router.urls)),
    # path('api/CountryBulkuploadViewSet')

]