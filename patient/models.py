from django.db import models
from django.utils import timezone
import uuid
from django.urls import reverse
import json


class Patient(models.Model):
    """Patient model for storing patient data"""
    MALE = 'M'
    FEMALE = 'F'
    OTHER = 'O'
    
    GENDER_CHOICES = [
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (OTHER, 'Other'),
    ]
    
    BLOOD_GROUPS = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    # Auto-generated patient ID (unique identifier)
    patient_id = models.CharField(
        max_length=10, 
        unique=True, 
        default=None, 
        editable=False
    )
    
    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True)
    profile_picture = models.ImageField(upload_to='patients/', blank=True, null=True)
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=15)
    emergency_contact_relation = models.CharField(max_length=50)
    
    # Medical Information
    allergies = models.TextField(blank=True)
    chronic_diseases = models.TextField(blank=True)
    
    # Registration Information
    registration_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"
    
    def save(self, *args, **kwargs):
        # Generate patient ID if it's a new patient
        if not self.patient_id:
            year = timezone.now().year
            # Get the count of patients and add 1
            count = Patient.objects.count() + 1
            # Format: P-YEAR-COUNT (e.g., P-2023-0001)
            self.patient_id = f"P-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('patient_detail', args=[str(self.id)])
    
    @property
    def age(self):
        """Calculate patient's age based on date of birth"""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def full_name(self):
        """Return patient's full name"""
        return f"{self.first_name} {self.last_name}"


class MedicalRecord(models.Model):
    """Medical record/report for a patient"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='patient_records')
    appointment = models.OneToOneField('appointment.Appointment', on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_record')
    
    # Vital signs
    blood_pressure = models.CharField(max_length=20, blank=True, help_text="e.g., 120/80 mmHg")
    sugar_level = models.CharField(max_length=20, blank=True, help_text="Blood glucose level")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Body temperature in °C")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    
    # Report details
    report_date = models.DateTimeField(default=timezone.now)
    symptoms = models.TextField()
    diagnosis = models.TextField()
    treatment_plan = models.TextField(blank=True, help_text="Detailed treatment plan")
    prescription = models.TextField()  # Legacy text prescription
    blood_test_results = models.TextField(blank=True, help_text="Results of any blood tests performed")
    notes = models.TextField(blank=True)
    
    # X-ray and other images
    xray_image = models.ImageField(upload_to='medical_records/xrays/', blank=True, null=True, help_text="Upload X-ray images if available")
    
    # Additional care instructions
    precautions = models.TextField(blank=True)
    diet = models.TextField(blank=True)
    exercise = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Document tracking
    is_final = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_records'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Medical Record {self.id} - {self.patient.full_name} - {self.report_date.strftime('%Y-%m-%d')}"
    
    def get_structured_prescriptions(self):
        """Get structured prescriptions for this record"""
        return self.prescriptions.all()


class Prescription(models.Model):
    """Structured prescription model"""
    TIMING_CHOICES = [
        ('BEFORE_MEAL', 'Before Meal'),
        ('AFTER_MEAL', 'After Meal'),
        ('WITH_MEAL', 'With Meal'),
        ('EMPTY_STOMACH', 'Empty Stomach'),
        ('BEDTIME', 'At Bedtime'),
        ('AS_NEEDED', 'As Needed (PRN)'),
    ]
    
    FREQUENCY_CHOICES = [
        ('ONCE', 'Once a day'),
        ('TWICE', 'Twice a day'),
        ('THRICE', 'Three times a day'),
        ('FOUR', 'Four times a day'),
        ('HOURLY_4', 'Every 4 hours'),
        ('HOURLY_6', 'Every 6 hours'),
        ('HOURLY_8', 'Every 8 hours'),
        ('HOURLY_12', 'Every 12 hours'),
        ('WEEKLY', 'Once a week'),
        ('MONTHLY', 'Once a month'),
        ('AS_DIRECTED', 'As directed'),
    ]
    
    DURATION_UNIT_CHOICES = [
        ('DAYS', 'Days'),
        ('WEEKS', 'Weeks'),
        ('MONTHS', 'Months'),
    ]
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    timing = models.CharField(max_length=15, choices=TIMING_CHOICES, default='AFTER_MEAL')
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, default='THRICE')
    duration = models.PositiveIntegerField(default=7)
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default='DAYS')
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'prescriptions'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.medication_name} {self.dosage} - {self.get_frequency_display()} ({self.get_timing_display()})"
    
    @property
    def full_instructions(self):
        """Generate full instructions for this prescription"""
        instructions = f"{self.medication_name} {self.dosage}, {self.get_frequency_display()}, {self.get_timing_display()}"
        if self.duration:
            instructions += f" for {self.duration} {self.get_duration_unit_display().lower()}"
        if self.special_instructions:
            instructions += f". Special instructions: {self.special_instructions}"
        return instructions


class Room(models.Model):
    """Enhanced model for hospital rooms with comprehensive amenities"""
    
    # Room types with specific amenities and pricing
    STANDARD = 'STANDARD'
    DELUXE = 'DELUXE'
    LUXURY = 'LUXURY'
    ICU = 'ICU'
    SUITE = 'SUITE'
    OPERATION_ROOM = 'OPERATION_ROOM'
    
    ROOM_TYPE_CHOICES = [
        (STANDARD, 'Standard Room'),
        (DELUXE, 'Deluxe Room with TV'),
        (LUXURY, 'Luxury Large Room'),
        (ICU, 'ICU Room'),
        (SUITE, 'Executive Suite'),
        (OPERATION_ROOM, 'Operation Theater'),
    ]
    
    # Room amenities based on type
    ROOM_AMENITIES = {
        STANDARD: {
            'amenities': ['Basic bed', 'Private bathroom', 'Window view', 'Reading light'],
            'capacity': 1,
            'daily_rate': 2500,
            'description': 'Comfortable standard room with essential amenities'
        },
        DELUXE: {
            'amenities': ['Comfortable bed', 'Private bathroom', 'LCD TV', 'Window view', 'Mini fridge', 'AC', 'Reading light'],
            'capacity': 1,
            'daily_rate': 4000,
            'description': 'Deluxe room with entertainment and comfort features'
        },
        LUXURY: {
            'amenities': ['Premium king bed', 'Luxury bathroom', '42" Smart TV', 'City view', 'Mini bar', 'AC', 'Sofa set', 'Work desk', 'Safe'],
            'capacity': 2,
            'daily_rate': 6500,
            'description': 'Spacious luxury room with premium amenities'
        },
        ICU: {
            'amenities': ['ICU bed', 'Life support systems', 'Monitoring equipment', 'Emergency access', '24/7 nursing'],
            'capacity': 1,
            'daily_rate': 8000,
            'description': 'Intensive care unit with advanced medical equipment'
        },
        SUITE: {
            'amenities': ['Master bedroom', 'Living area', 'Luxury bathroom', '55" Smart TV', 'Kitchenette', 'Balcony', 'Premium bedding', 'Concierge service'],
            'capacity': 3,
            'daily_rate': 12000,
            'description': 'Executive suite with separate living area and premium services'
        },
        OPERATION_ROOM: {
            'amenities': ['Surgical table', 'Anesthesia machine', 'Surgical lights', 'Monitoring equipment', 'Surgical instruments', 'Ventilator', 'Sterile environment'],
            'capacity': 1,
            'daily_rate': 15000,
            'description': 'Fully equipped operation theater with advanced surgical equipment'
        }
    }
    
    # Hospital departments by floor
    GENERAL_MEDICINE = 'GENERAL_MEDICINE'
    CARDIOLOGY = 'CARDIOLOGY'
    ORTHOPEDIC = 'ORTHOPEDIC'
    NEUROLOGY = 'NEUROLOGY'
    ONCOLOGY = 'ONCOLOGY'
    EMERGENCY = 'EMERGENCY'
    
    DEPARTMENT_CHOICES = [
        (GENERAL_MEDICINE, 'General Medicine'),
        (CARDIOLOGY, 'Cardiology'),
        (ORTHOPEDIC, 'Orthopedic'),
        (NEUROLOGY, 'Neurology'),
        (ONCOLOGY, 'Oncology'),
        (EMERGENCY, 'Emergency'),
    ]
    
    # Multi-Specialty Hospital Floor Layout - 6 floors total
    FLOOR_DEPARTMENT_MAP = {
        1: GENERAL_MEDICINE,    # Floor 1: General Medicine & Internal Medicine
        2: CARDIOLOGY,          # Floor 2: Cardiology & Cardiovascular Surgery
        3: ORTHOPEDIC,          # Floor 3: Orthopedic & Bone Surgery
        4: NEUROLOGY,           # Floor 4: Neurology & Neurosurgery
        5: EMERGENCY,           # Floor 5: Emergency & Critical Care
        6: ONCOLOGY,            # Floor 6: Oncology & Cancer Treatment
    }
    
    # Multi-Specialty Hospital Room Distribution (24 rooms per floor)
    # Each floor has 2 Operation Rooms + 2 ICU Rooms + 20 Patient Rooms
    FLOOR_ROOM_DISTRIBUTION = {
        1: {OPERATION_ROOM: 2, ICU: 2, STANDARD: 12, DELUXE: 8},                    # Floor 1: General Medicine
        2: {OPERATION_ROOM: 2, ICU: 2, STANDARD: 6, DELUXE: 10, LUXURY: 4},        # Floor 2: Cardiology  
        3: {OPERATION_ROOM: 2, ICU: 2, STANDARD: 6, DELUXE: 8, LUXURY: 6},         # Floor 3: Orthopedic
        4: {OPERATION_ROOM: 2, ICU: 2, DELUXE: 8, LUXURY: 8, SUITE: 4},            # Floor 4: Neurology
        5: {OPERATION_ROOM: 2, ICU: 2, DELUXE: 6, LUXURY: 8, SUITE: 6},            # Floor 5: Emergency
        6: {OPERATION_ROOM: 2, ICU: 2, DELUXE: 4, LUXURY: 10, SUITE: 6},           # Floor 6: Oncology
    }
    
    # Room identification
    room_number = models.CharField(max_length=10, unique=True)
    floor = models.IntegerField(choices=[(i, f'Floor {i}') for i in range(1, 7)])
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default=STANDARD)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default=GENERAL_MEDICINE)
    
    # Room status and features
    is_active = models.BooleanField(default=True)
    is_occupied = models.BooleanField(default=False)
    bed_count = models.IntegerField(default=1)
    
    # Maintenance and cleaning
    last_cleaned = models.DateTimeField(default=timezone.now)
    maintenance_notes = models.TextField(blank=True)
    
    # Pricing
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'rooms'
        ordering = ['floor', 'room_number']
        indexes = [
            models.Index(fields=['floor', 'room_type']),
            models.Index(fields=['is_occupied', 'room_type']),
        ]
    
    def __str__(self):
        return f"Room {self.room_number} - {self.get_room_type_display()} (Floor {self.floor})"
    
    def save(self, *args, **kwargs):
        # Auto-set department based on floor
        if self.floor in self.FLOOR_DEPARTMENT_MAP:
            self.department = self.FLOOR_DEPARTMENT_MAP[self.floor]
        
        # Auto-set daily rate based on room type
        if self.room_type in self.ROOM_AMENITIES:
            self.daily_rate = self.ROOM_AMENITIES[self.room_type]['daily_rate']
        
        # Auto-set bed count based on room type capacity
        if self.room_type in self.ROOM_AMENITIES:
            self.bed_count = self.ROOM_AMENITIES[self.room_type]['capacity']
        
        # Generate room number if not explicitly set
        if not self.room_number:
            # Create room number in format: F{floor}-{type_code}{number}
            type_codes = {
                'STANDARD': 'S',
                'DELUXE': 'D', 
                'LUXURY': 'L',
                'ICU': 'I',
                'SUITE': 'X',
                'OPERATION_ROOM': 'O'
            }
            type_code = type_codes.get(self.room_type, 'R')
            
            # Count existing rooms of same type on same floor
            existing_count = Room.objects.filter(
                floor=self.floor, 
                room_type=self.room_type
            ).count()
            
            self.room_number = f"F{self.floor}-{type_code}{existing_count + 1:02d}"
        
        super().save(*args, **kwargs)
    
    @property
    def amenities_list(self):
        """Get list of amenities for this room type"""
        return self.ROOM_AMENITIES.get(self.room_type, {}).get('amenities', [])
    
    @property
    def room_description(self):
        """Get description for this room type"""
        return self.ROOM_AMENITIES.get(self.room_type, {}).get('description', '')
    
    @property
    def available_beds(self):
        """Get count of available beds in this room"""
        occupied_beds = self.beds.filter(is_occupied=True).count()
        return self.bed_count - occupied_beds
    
    @property
    def is_fully_occupied(self):
        """Check if all beds in room are occupied"""
        return self.available_beds == 0


class Bed(models.Model):
    """Enhanced model for individual beds in rooms"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=10)
    
    # Bed status and features
    is_occupied = models.BooleanField(default=False)
    is_functional = models.BooleanField(default=True)
    last_sanitized = models.DateTimeField(default=timezone.now)
    
    # Bed maintenance
    maintenance_required = models.BooleanField(default=False)
    maintenance_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'beds'
        unique_together = ['room', 'bed_number']
        ordering = ['room', 'bed_number']
    
    def __str__(self):
        return f"Bed {self.bed_number} in {self.room}"
    
    def save(self, *args, **kwargs):
        # Generate bed number if not explicitly set
        if not self.bed_number:
            # Create bed number by count in room (e.g., B01, B02)
            count = Bed.objects.filter(room=self.room).count() + 1
            self.bed_number = f"B{count:02d}"
        
        super().save(*args, **kwargs)


class Nurse(models.Model):
    """Enhanced model for nurses and their assignments"""
    
    # Specializations based on hospital departments
    GENERAL_MEDICINE = 'GENERAL_MEDICINE'
    CARDIOLOGY = 'CARDIOLOGY'
    ORTHOPEDIC = 'ORTHOPEDIC'
    NEUROLOGY = 'NEUROLOGY'
    ONCOLOGY = 'ONCOLOGY'
    EMERGENCY = 'EMERGENCY'
    GENERAL_NURSING = 'GENERAL_NURSING'
    
    SPECIALIZATION_CHOICES = [
        (GENERAL_MEDICINE, 'General Medicine Nursing'),
        (CARDIOLOGY, 'Cardiac Nursing'),
        (ORTHOPEDIC, 'Orthopedic Nursing'),
        (NEUROLOGY, 'Neurological Nursing'),
        (ONCOLOGY, 'Oncology Nursing'),
        (EMERGENCY, 'Emergency & Critical Care'),
        (GENERAL_NURSING, 'General Nursing'),
    ]
    
    # Map floor numbers to specializations
    FLOOR_SPECIALIZATION_MAP = {
        1: GENERAL_MEDICINE,    # Floor 1: General Medicine & Internal Medicine
        2: CARDIOLOGY,          # Floor 2: Cardiology & Cardiovascular Surgery
        3: ORTHOPEDIC,          # Floor 3: Orthopedic & Bone Surgery
        4: NEUROLOGY,           # Floor 4: Neurology & Neurosurgery
        5: EMERGENCY,           # Floor 5: Emergency & Critical Care
        6: ONCOLOGY,            # Floor 6: Oncology & Cancer Treatment
    }
    
    nurse = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='nurse_assignments')
    assigned_floors = models.JSONField(default=list, help_text="List of floor numbers assigned to this nurse")
    is_on_duty = models.BooleanField(default=True)
    max_patients = models.IntegerField(default=5)
    specialization = models.CharField(
        max_length=20, 
        choices=SPECIALIZATION_CHOICES, 
        default=GENERAL_NURSING,
        help_text="Primary specialization of the nurse"
    )
    
    # Shift information
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'nurses'

    def __str__(self):
        floors_str = ', '.join([f'Floor {floor}' for floor in self.assigned_floors]) if self.assigned_floors else 'No floors assigned'
        return f"{self.nurse.get_full_name()} - {self.get_specialization_display()} ({floors_str})"

    @property
    def current_patients_count(self):
        """Get current number of patients assigned to this nurse"""
        return PatientAdmission.objects.filter(
            assigned_nurse=self.nurse,
            discharge_date__isnull=True
        ).count()

    @property
    def is_available(self):
        """Check if nurse is available to take new patients"""
        return self.is_on_duty and self.current_patients_count < self.max_patients
    
    @property
    def primary_floor_specialization(self):
        """Get the specialization based on the primary assigned floor"""
        if self.assigned_floors:
            primary_floor = self.assigned_floors[0]
            return self.FLOOR_SPECIALIZATION_MAP.get(primary_floor, self.GENERAL_NURSING)
        return self.specialization
    
    @property
    def assigned_departments(self):
        """Get list of departments this nurse covers based on assigned floors"""
        departments = []
        for floor in self.assigned_floors:
            dept = Room.FLOOR_DEPARTMENT_MAP.get(floor)
            if dept and dept not in departments:
                departments.append(dept)
        return departments
    
    def can_handle_floor(self, floor_number):
        """Check if nurse can handle patients on a specific floor"""
        return floor_number in self.assigned_floors
    
    def save(self, *args, **kwargs):
        # Auto-set specialization based on primary assigned floor
        if self.assigned_floors and not self.specialization:
            primary_floor = self.assigned_floors[0]
            self.specialization = self.FLOOR_SPECIALIZATION_MAP.get(primary_floor, self.GENERAL_NURSING)
        
        super().save(*args, **kwargs)


class AdmissionRequest(models.Model):
    """Model for doctor's admission requests"""
    
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    COMPLETED = 'COMPLETED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending Review'),
        (APPROVED, 'Approved - Awaiting Room Assignment'),
        (REJECTED, 'Rejected'),
        (COMPLETED, 'Completed - Patient Admitted'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('CRITICAL', 'Critical/Emergency'),
    ]
    
    # Request details
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admission_requests')
    requesting_doctor = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='admission_requests')
    
    # Medical details
    primary_diagnosis = models.TextField()
    secondary_diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField()
    estimated_length_of_stay = models.PositiveIntegerField(help_text="Estimated days")
    
    # Room preferences
    preferred_room_type = models.CharField(max_length=20, choices=Room.ROOM_TYPE_CHOICES, default=Room.STANDARD)
    preferred_floor = models.IntegerField(choices=[(i, f'Floor {i}') for i in range(1, 7)], null=True, blank=True)
    special_requirements = models.TextField(blank=True, help_text="Any special room or care requirements")
    
    # Request status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Approval workflow
    reviewed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_admission_requests')
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Related admission (once processed)
    patient_admission = models.OneToOneField('PatientAdmission', on_delete=models.SET_NULL, null=True, blank=True, related_name='admission_request')
    
    class Meta:
        db_table = 'admission_requests'
        ordering = ['-created_at', 'priority']
    
    def __str__(self):
        return f"Admission Request for {self.patient.full_name} by Dr. {self.requesting_doctor.get_full_name()}"


class PatientAdmission(models.Model):
    """Enhanced model for patient hospital admissions"""
    
    # Admission types
    REGULAR = 'REGULAR'
    EMERGENCY = 'EMERGENCY'
    TRANSFER = 'TRANSFER'
    SCHEDULED = 'SCHEDULED'
    
    ADMISSION_TYPE_CHOICES = [
        (REGULAR, 'Regular Admission'),
        (EMERGENCY, 'Emergency Admission'),
        (TRANSFER, 'Transfer from Another Hospital'),
        (SCHEDULED, 'Scheduled Surgery/Procedure'),
    ]
    
    # Patient, doctor and room info
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    admitting_doctor = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='admitted_patients')
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name='admissions')
    assigned_nurse = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='assigned_patients')
    
    # Admission details
    admission_date = models.DateTimeField(default=timezone.now)
    discharge_date = models.DateTimeField(null=True, blank=True)
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES, default=REGULAR)
    
    # Medical details
    primary_diagnosis = models.TextField()
    secondary_diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_critical = models.BooleanField(default=False)
    
    # Billing information
    estimated_discharge_date = models.DateField(null=True, blank=True)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Emergency admission tracking
    doctor_availability_time = models.DateTimeField(null=True, blank=True)
    
    # Workflow tracking
    assigned_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='room_assignments_made')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_admissions')
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patient_admissions'
        ordering = ['-admission_date']
        indexes = [
            models.Index(fields=['admission_date', 'discharge_date']),
            models.Index(fields=['bed', 'discharge_date']),
        ]
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.bed.room} - admitted on {self.admission_date.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Mark bed as occupied
        if self.bed and not self.bed.is_occupied:
            self.bed.is_occupied = True
            self.bed.save()
            
            # Update room occupancy status
            self.bed.room.is_occupied = self.bed.room.is_fully_occupied
            self.bed.room.save()
        
        # Calculate daily charges based on room type
        if self.bed and self.bed.room.daily_rate:
            if self.discharge_date:
                days_stayed = (self.discharge_date.date() - self.admission_date.date()).days
                if days_stayed == 0:
                    days_stayed = 1  # Minimum 1 day charge
                self.total_charges = self.bed.room.daily_rate * days_stayed
        
        # If this is an emergency admission, set doctor availability time
        if self.admission_type == self.EMERGENCY and not self.doctor_availability_time:
            # Emergency doctors are unavailable for 30 minutes
            self.doctor_availability_time = timezone.now() + timezone.timedelta(minutes=30)
        
        super().save(*args, **kwargs)
    
    def discharge(self, discharge_notes=''):
        """Discharge the patient"""
        self.discharge_date = timezone.now()
        if discharge_notes:
            self.notes += f"\n\nDischarge Notes ({self.discharge_date.strftime('%Y-%m-%d %H:%M')}): {discharge_notes}"
        self.save()
        
        # Free up the bed and room
        self.bed.is_occupied = False
        self.bed.last_sanitized = timezone.now()
        self.bed.save()
        
        # Update room occupancy status
        self.bed.room.is_occupied = self.bed.room.is_fully_occupied
        self.bed.room.last_cleaned = timezone.now()
        self.bed.room.save()
    
    @property
    def length_of_stay(self):
        """Calculate length of stay in days"""
        end_date = self.discharge_date or timezone.now()
        return (end_date.date() - self.admission_date.date()).days + 1
    
    @property
    def is_active(self):
        """Check if admission is currently active"""
        return self.discharge_date is None 