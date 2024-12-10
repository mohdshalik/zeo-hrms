from django.contrib import admin
from .models import weekend_calendar,assign_weekend,holiday,holiday_calendar,assign_holiday

@admin.register(weekend_calendar)
class CalendarAdmin(admin.ModelAdmin):
    pass
@admin.register(assign_weekend)
class Assign_weekendAdmin(admin.ModelAdmin):
    pass
@admin.register(holiday)
class HolidayAdmin(admin.ModelAdmin):
    pass
@admin.register(holiday_calendar)
class Holiday_calendarAdmin(admin.ModelAdmin):
    pass
@admin.register(assign_holiday)
class Assign_holidayAdmin(admin.ModelAdmin):
    pass