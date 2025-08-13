from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from patient.models import Patient


class DoctorAvailability(models.Model):
    """Model to store doctor availability slots"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        db_table = 'doctor_availability'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"
    
    def clean(self):
        """Validate that start_time is before end_time"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Check for overlapping slots for the same doctor on same day
        overlapping = DoctorAvailability.objects.filter(
            doctor=self.doctor,
            day_of_week=self.day_of_week,
        ).exclude(id=self.id)
        
        for slot in overlapping:
            if (self.start_time <= slot.end_time and self.end_time >= slot.start_time):
                raise ValidationError(f"This time slot overlaps with an existing slot: {slot}")


class DoctorLeaveRequest(models.Model):
    """Model for doctor leave requests"""
    # Status options
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (CANCELLED, 'Cancelled'),
    ]
    
    doctor = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    # Admin response
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leave_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctor_leave_requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Leave request: Dr. {self.doctor.get_full_name()} ({self.start_date} to {self.end_date}) - {self.get_status_display()}"
    
    def clean(self):
        """Validate leave request times"""
        if self.start_date > self.end_date:
            raise ValidationError("Start date must be before or equal to end date")
            
        # Special case for full-day leave (00:00 to 23:59)
        if self.start_time and self.end_time and self.start_time.hour == 0 and self.start_time.minute == 0 and self.end_time.hour == 23 and self.end_time.minute == 59:
            # This is a valid full-day leave request
            pass
        # Normal time validation    
        elif self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
            
        # Check if there are any scheduled appointments during the leave period
        # Skip this check if doctor is not set yet or if this is not a pending request
        if hasattr(self, 'doctor') and self.doctor is not None and self.status == self.PENDING:
            overlapping_appointments = Appointment.objects.filter(
                doctor=self.doctor,
                date__range=(self.start_date, self.end_date),
                status__in=[Appointment.SCHEDULED, Appointment.CONFIRMED]
            )
            
            if overlapping_appointments.exists():
                # We'll allow the request, but add a warning that will be shown to the admin
                pass
    
    def save(self, *args, **kwargs):
        """Override save to handle approval status changes"""
        if self.pk:
            old_instance = DoctorLeaveRequest.objects.get(pk=self.pk)
            if old_instance.status != self.APPROVED and self.status == self.APPROVED:
                self.reviewed_at = timezone.now()
                
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if leave is current/active"""
        today = timezone.now().date()
        return (
            self.status == self.APPROVED and 
            self.start_date <= today <= self.end_date
        )
    
    @property
    def has_conflicts(self):
        """Check if there are scheduled appointments during this leave period"""
        if not hasattr(self, 'doctor') or self.doctor is None:
            return False
            
        return Appointment.objects.filter(
            doctor=self.doctor,
            date__range=(self.start_date, self.end_date),
            status__in=[Appointment.SCHEDULED, Appointment.CONFIRMED]
        ).exists()
    
    @property
    def conflicting_appointments(self):
        """Get all conflicting appointments during this leave period"""
        if not hasattr(self, 'doctor') or self.doctor is None:
            return Appointment.objects.none()
            
        return Appointment.objects.filter(
            doctor=self.doctor,
            date__range=(self.start_date, self.end_date),
            status__in=[Appointment.SCHEDULED, Appointment.CONFIRMED]
        )


class Appointment(models.Model):
    """Model for patient appointments"""
    # Status options
    SCHEDULED = 'SCHEDULED'
    CONFIRMED = 'CONFIRMED'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    MISSED = 'MISSED'
    
    STATUS_CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (CONFIRMED, 'Confirmed'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
        (MISSED, 'Missed'),
    ]
    
    # Appointment type options
    REGULAR = 'REGULAR'
    FOLLOW_UP = 'FOLLOW_UP'
    EMERGENCY = 'EMERGENCY'
    
    TYPE_CHOICES = [
        (REGULAR, 'Regular Checkup'),
        (FOLLOW_UP, 'Follow Up'),
        (EMERGENCY, 'Emergency'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='appointments')
    
    # Appointment details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=REGULAR)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SCHEDULED)
    is_emergency = models.BooleanField(default=False, help_text="Emergency appointments are available 24/7")
    
    # Additional info
    reason = models.TextField()
    notes = models.TextField(blank=True)
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_appointments')
    
    class Meta:
        db_table = 'appointments'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"Appointment for {self.patient.full_name} with Dr. {self.doctor.get_full_name()} on {self.date} at {self.start_time.strftime('%H:%M')}"
    
    def clean(self):
        """Validate appointment times and availability"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Appointment start time must be before end time")
        
        # Emergency appointments bypass most validation checks
        is_emergency = self.appointment_type == self.EMERGENCY or self.is_emergency
        
        # First check for approved leave requests that would make the doctor unavailable
        leave_requests = DoctorLeaveRequest.objects.filter(
            doctor=self.doctor,
            status=DoctorLeaveRequest.APPROVED,
            start_date__lte=self.date,
            end_date__gte=self.date
        )
        
        for leave in leave_requests:
            # Check if appointment time conflicts with leave time
            if (self.start_time < leave.end_time and self.end_time > leave.start_time):
                if not is_emergency:
                    raise ValidationError(f"Doctor is on approved leave during this time")
        
        # Define standard working hours
        import datetime
        standard_start = datetime.time(8, 0)  # 8:00 AM
        standard_end = datetime.time(22, 0)   # 10:00 PM (updated from 8:00 PM)
        
        # Only check availability slots if the doctor has defined them
        doctor_has_availability_slots = DoctorAvailability.objects.filter(doctor=self.doctor).exists()
        
        if doctor_has_availability_slots:
            # If doctor has explicit availability slots, check them
            day_of_week = self.date.weekday()
            
            # Find a matching availability slot for the doctor
            availability = DoctorAvailability.objects.filter(
                doctor=self.doctor,
                day_of_week=day_of_week,
                start_time__lte=self.start_time,
                end_time__gte=self.end_time
            ).exists()
            
            if not availability and not is_emergency:
                raise ValidationError("Doctor is not available during this time slot")
        else:
            # If no explicit availability slots are defined, use standard hours (8 AM - 10 PM)
            # but only check for non-emergency appointments
            if (self.start_time < standard_start or self.end_time > standard_end) and not is_emergency:
                raise ValidationError("Appointment time is outside standard hours (8:00 AM - 10:00 PM)")
        
        # Check for overlapping appointments for the doctor
        overlapping_doctor = Appointment.objects.filter(
            doctor=self.doctor,
            date=self.date,
            status__in=[self.SCHEDULED, self.CONFIRMED]
        ).exclude(id=self.id)
        
        for appt in overlapping_doctor:
            if (self.start_time < appt.end_time and self.end_time > appt.start_time):
                raise ValidationError(f"Doctor already has an appointment during this time: {appt}")
        
        # Check for overlapping appointments for the patient
        overlapping_patient = Appointment.objects.filter(
            patient=self.patient,
            date=self.date,
            status__in=[self.SCHEDULED, self.CONFIRMED]
        ).exclude(id=self.id)
        
        for appt in overlapping_patient:
            if (self.start_time < appt.end_time and self.end_time > appt.start_time):
                raise ValidationError(f"Patient already has an appointment during this time: {appt}")
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is called"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_past(self):
        """Check if appointment is in the past"""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.end_time)
        )
        return now > appointment_datetime 