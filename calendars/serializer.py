from rest_framework import serializers
from .models import weekend_calendar,assign_weekend,holiday_calendar,holiday,assign_holiday,WeekendDetail
from OrganisationManager.serializer import BranchSerializer,CtgrySerializer,DeptSerializer
from OrganisationManager.models import brnch_mstr,dept_master,ctgry_master
from EmpManagement.models import emp_master
from EmpManagement.serializer import EmpSerializer

class WeekendDetailSerializer(serializers.ModelSerializer):
    week_of_month = serializers.ChoiceField(choices=[(i, i) for i in range(1, 6)], required=False, allow_null=True, allow_blank=True)
    month_of_year = serializers.ChoiceField(choices=[(i, i) for i in range(1, 13)], required=False, allow_null=True, allow_blank=True)
    class Meta:
        model = WeekendDetail
        fields = '__all__'

class WeekendCalendarSerailizer(serializers.ModelSerializer):
    year = serializers.ChoiceField(choices=[(year, year) for year in range(2000, 2040)])
    # details = WeekendDetailSerializer(many=True)
    details = WeekendDetailSerializer(many=True, read_only=True)
    
    details = WeekendDetailSerializer(many=True, read_only=True)
    class Meta:
        model = weekend_calendar
        fields = '__all__'

    # def create(self, validated_data):
    #     details_data = validated_data.pop('details')
    #     weekend_calendar = weekend_calendar.objects.create(**validated_data)
    #     for detail_data in details_data:
    #         WeekendDetail.objects.create(weekend_calendar=weekend_calendar, **detail_data)
    #     return weekend_calendar

    # def update(self, instance, validated_data):
    #     details_data = validated_data.pop('details')
    #     instance.description = validated_data.get('description', instance.description)
    #     instance.calendar_code = validated_data.get('calendar_code', instance.calendar_code)
    #     instance.year = validated_data.get('year', instance.year)
    #     instance.save()

    #     # Update or create details
    #     for detail_data in details_data:
    #         detail_id = detail_data.get('id')
    #         if detail_id:
    #             detail_instance = WeekendDetail.objects.get(id=detail_id, weekend_calendar=instance)
    #             detail_instance.weekday = detail_data.get('weekday', detail_instance.weekday)
    #             detail_instance.day_type = detail_data.get('day_type', detail_instance.day_type)
    #             detail_instance.week_of_month = detail_data.get('week_of_month', detail_instance.week_of_month)
    #             detail_instance.save()
    #         else:
    #             WeekendDetail.objects.create(weekend_calendar=instance, **detail_data)

    #     return instance
        


class WeekendAssignSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = assign_weekend
        fields = '__all__'
    


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = holiday
        fields = '__all__'

class HolidayCalandarSerializer(serializers.ModelSerializer):
    year = serializers.ChoiceField(choices=[(year, year) for year in range(2000, 2040)])
    holiday = HolidaySerializer(many=True,)
    class Meta:
        model = holiday_calendar
        fields = '__all__'


class HolidayAssignSerializer(serializers.ModelSerializer):
    class Meta:
        model = assign_holiday
        fields = '__all__'
    
    