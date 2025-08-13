from django.contrib import admin
from django import forms
from .models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission


class NurseAdminForm(forms.ModelForm):
    """Custom form for Nurse admin with better JSONField handling"""
    
    FLOOR_CHOICES = [
        (1, 'Floor 1 - General Medicine'),
        (2, 'Floor 2 - Cardiology'),
        (3, 'Floor 3 - Orthopedic'),
        (4, 'Floor 4 - Neurology'),
        (5, 'Floor 5 - Oncology'),
        (6, 'Floor 6 - Emergency/ICU'),
    ]
    
    assigned_floors = forms.MultipleChoiceField(
        choices=FLOOR_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the floors this nurse is assigned to work on."
    )
    
    class Meta:
        model = Nurse
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.assigned_floors:
            # Convert stored integers to strings for form display
            self.initial['assigned_floors'] = [str(floor) for floor in self.instance.assigned_floors]
    
    def clean_assigned_floors(self):
        """Convert selected floor strings back to integers"""
        floors = self.cleaned_data.get('assigned_floors', [])
        return [int(floor) for floor in floors] if floors else []


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'first_name', 'last_name', 'gender', 'phone', 'registration_date')
    list_filter = ('gender', 'registration_date')
    search_fields = ('patient_id', 'first_name', 'last_name', 'phone', 'email')
    readonly_fields = ('patient_id', 'registration_date', 'last_updated')
    fieldsets = (
        ('Personal Information', {
            'fields': ('patient_id', 'first_name', 'last_name', 'gender', 'date_of_birth', 'blood_group')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation')
        }),
        ('Medical Information', {
            'fields': ('allergies', 'chronic_diseases')
        }),
        ('Registration Information', {
            'fields': ('registration_date', 'last_updated')
        }),
    )


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'report_date', 'diagnosis')
    list_filter = ('report_date', 'doctor')
    search_fields = ('patient__first_name', 'patient__last_name', 'diagnosis')
    readonly_fields = ('report_date', 'last_updated')
    date_hierarchy = 'report_date'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'floor', 'get_department_display', 'room_type', 'is_active', 'bed_count', 'occupied_beds')
    list_filter = ('floor', 'department', 'room_type', 'is_active')
    search_fields = ('room_number',)
    
    def bed_count(self, obj):
        return obj.beds.count()
    
    def occupied_beds(self, obj):
        return obj.beds.filter(is_occupied=True).count()
    
    bed_count.short_description = 'Total Beds'
    occupied_beds.short_description = 'Occupied Beds'


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'room', 'is_occupied', 'last_sanitized')
    list_filter = ('is_occupied', 'room__floor', 'room__department')
    search_fields = ('bed_number', 'room__room_number')
    date_hierarchy = 'last_sanitized'


@admin.register(Nurse)
class NurseAdmin(admin.ModelAdmin):
    form = NurseAdminForm
    list_display = ('nurse', 'get_specialization_display', 'get_assigned_floors_display', 'is_on_duty', 'max_patients', 'current_patients_count')
    list_filter = ('is_on_duty', 'specialization')
    search_fields = ('nurse__first_name', 'nurse__last_name', 'nurse__email')
    
    fieldsets = (
        ('Nurse Information', {
            'fields': ('nurse', 'specialization')
        }),
        ('Floor Assignment', {
            'fields': ('assigned_floors',),
            'description': 'Assign floors to the nurse. Each floor corresponds to a specific medical department.'
        }),
        ('Work Details', {
            'fields': ('is_on_duty', 'max_patients', 'shift_start', 'shift_end')
        }),
    )
    
    def get_assigned_floors_display(self, obj):
        if obj.assigned_floors:
            floors_with_dept = []
            for floor in obj.assigned_floors:
                dept = obj.FLOOR_SPECIALIZATION_MAP.get(floor, 'Unknown')
                floors_with_dept.append(f'Floor {floor} ({dept.replace("_", " ").title()})')
            return ', '.join(floors_with_dept)
        return 'No floors assigned'
    
    def current_patients_count(self, obj):
        return obj.current_patients_count
    
    get_assigned_floors_display.short_description = 'Assigned Floors & Departments'
    current_patients_count.short_description = 'Current Patients'


@admin.register(PatientAdmission)
class PatientAdmissionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'admitting_doctor', 'admission_date', 'discharge_date', 
                   'admission_type', 'is_critical')
    list_filter = ('admission_type', 'is_critical', 'admission_date')
    search_fields = ('patient__first_name', 'patient__last_name', 'primary_diagnosis')
    readonly_fields = ('admission_date', 'doctor_availability_time', 'last_updated')
    date_hierarchy = 'admission_date'
    
    fieldsets = (
        ('Patient and Doctor Information', {
            'fields': ('patient', 'admitting_doctor', 'assigned_nurse')
        }),
        ('Admission Details', {
            'fields': ('bed', 'admission_date', 'discharge_date', 'admission_type', 'is_critical')
        }),
        ('Medical Details', {
            'fields': ('primary_diagnosis', 'secondary_diagnosis', 'treatment_plan', 'notes')
        }),
        ('Emergency Information', {
            'fields': ('doctor_availability_time',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'last_updated'),
            'classes': ('collapse',)
        }),
    ) 