from django.urls import path, include
from .  views import (WeekendViewset,AssignWeekendViewset,HolidayViewset,HolidayCalendarViewset,HolidayAssignViewset,WeekendDetailsViewset)

from rest_framework.routers import DefaultRouter
router = DefaultRouter()

router.register(r'weekend', WeekendViewset)
router.register(r'assign-days', WeekendDetailsViewset)
router.register(r'assign-weekend', AssignWeekendViewset)
router.register(r'holiday', HolidayViewset)
router.register(r'holiday-calendar', HolidayCalendarViewset)
router.register(r'assign-holiday', HolidayAssignViewset)


urlpatterns = [
    # Other paths
    path('api/', include(router.urls)),

]