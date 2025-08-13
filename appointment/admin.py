from django.contrib import admin
from .models import Appointment, DoctorAvailability


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date', 'appointment_type')
    search_fields = ('patient__first_name', 'patient__last_name', 'patient__patient_id', 'doctor__username')
    raw_id_fields = ('patient', 'doctor', 'created_by')
    date_hierarchy = 'date'
    list_per_page = 20


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'get_day_of_week_display', 'start_time', 'end_time')
    list_filter = ('day_of_week',)
    search_fields = ('doctor__username', 'doctor__first_name', 'doctor__last_name')
    raw_id_fields = ('doctor',) 