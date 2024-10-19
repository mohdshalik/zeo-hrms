from django.shortcuts import render
from .models import weekend_calendar,assign_weekend,holiday,holiday_calendar,assign_holiday,WeekendDetail
from . serializer import WeekendCalendarSerailizer,WeekendAssignSerializer,HolidayAssignSerializer,HolidayCalandarSerializer,HolidaySerializer,WeekendDetailSerializer
from rest_framework import viewsets,filters,status
from rest_framework.response import Response
from rest_framework.decorators import action
from OrganisationManager.models import brnch_mstr,dept_master,ctgry_master
from OrganisationManager.serializer import BranchSerializer,DeptSerializer,CtgrySerializer
from EmpManagement.models import emp_master



# Create your views here.

class WeekendDetailsViewset(viewsets.ModelViewSet):
    queryset = WeekendDetail.objects.all()
    serializer_class = WeekendDetailSerializer
    
class WeekendViewset(viewsets.ModelViewSet):
    queryset = weekend_calendar.objects.all()
    serializer_class = WeekendCalendarSerailizer
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        weekend_calendar = self.get_object()
        serializer = self.get_serializer(weekend_calendar)
        return Response(serializer.data)
    # @action(detail=False, methods=['post'])
    # @action(detail=False, methods=['post'])
    # def set_monthly_weekends(self, request):
    #     data = request.data
    #     calendar_code = data.get('calendar_code')
    #     year = data.get('year')
    #     weekday = data.get('weekday')
    #     day_type = data.get('day_type')
    #     week_of_month = data.get('week_of_month')

    #     weekend_calendar, created = weekend_calendar.objects.get_or_create(calendar_code=calendar_code, year=year)
    #     for month in range(1, 13):
    #         for week in range(1, 6):  # Assuming up to 5 weeks in a month
    #             if week == week_of_month:
    #                 WeekendDetail.objects.create(
    #                     weekend_calendar=weekend_calendar,
    #                     weekday=weekday,
    #                     day_type=day_type,
    #                     week_of_month=week
    #                 )
        
    #     serializer = self.get_serializer(weekend_calendar)
    #     return Response(serializer.data)


class AssignWeekendViewset(viewsets.ModelViewSet):
    queryset = assign_weekend.objects.all()
    serializer_class = WeekendAssignSerializer

class HolidayViewset(viewsets.ModelViewSet):
    queryset = holiday.objects.all()
    serializer_class = HolidaySerializer

class HolidayCalendarViewset(viewsets.ModelViewSet):
    queryset = holiday_calendar.objects.all()
    serializer_class = HolidayCalandarSerializer

class HolidayAssignViewset(viewsets.ModelViewSet):
    queryset = assign_holiday.objects.all()
    serializer_class = HolidayAssignSerializer
