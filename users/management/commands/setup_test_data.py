import os
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from users.models import User
from patient.models import Patient
from appointment.models import Appointment, DoctorAvailability

class Command(BaseCommand):
    help = 'Sets up initial test data for the HMS application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up test data...')
        
        # Create users
        self.create_users()
        
        # Get doctor reference
        doctor = User.objects.get(username='doctor')
        
        # Create patients
        patients = self.create_patients(doctor)
        
        # Create doctor availability
        self.create_doctor_availability(doctor)
        
        # Create appointments
        self.create_appointments(doctor, patients)
        
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write('\nLogin Credentials:')
        self.stdout.write('-----------------')
        self.stdout.write('Admin: username=admin, password=Admin@123')
        self.stdout.write('Doctor: username=doctor, password=Doctor@123')
        self.stdout.write('Nurse: username=nurse, password=Nurse@123')
        self.stdout.write('Receptionist: username=receptionist, password=Reception@123')
        self.stdout.write('Pharmacist: username=pharmacist, password=Pharmacy@123')
    
    def create_users(self):
        """Create user accounts for all roles"""
        # User data
        users = [
            {
                "username": "admin",
                "password": make_password("Admin@123"),
                "email": "admin@hospital.com",
                "first_name": "System",
                "last_name": "Administrator",
                "role": "ADMIN",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "date_joined": timezone.now(),
                "phone_number": "555-000-0000",
                "address": "Hospital Admin Office"
            },
            {
                "username": "doctor",
                "password": make_password("Doctor@123"),
                "email": "doctor@hospital.com",
                "first_name": "John",
                "last_name": "Smith",
                "role": "DOCTOR",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "date_joined": timezone.now(),
                "phone_number": "555-123-4567",
                "address": "123 Medical Dr",
                "specialization": "General Medicine",
                "qualification": "MD, General Medicine"
            },
            {
                "username": "nurse",
                "password": make_password("Nurse@123"),
                "email": "nurse@hospital.com",
                "first_name": "Emily",
                "last_name": "Johnson",
                "role": "NURSE",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "date_joined": timezone.now(),
                "phone_number": "555-234-5678",
                "address": "456 Nursing Ave"
            },
            {
                "username": "receptionist",
                "password": make_password("Reception@123"),
                "email": "receptionist@hospital.com",
                "first_name": "Sarah",
                "last_name": "Wilson",
                "role": "RECEPTIONIST",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "date_joined": timezone.now(),
                "phone_number": "555-345-6789",
                "address": "789 Front Desk Rd"
            },
            {
                "username": "pharmacist",
                "password": make_password("Pharmacy@123"),
                "email": "pharmacist@hospital.com",
                "first_name": "Michael",
                "last_name": "Brown",
                "role": "PHARMACIST",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "date_joined": timezone.now(),
                "phone_number": "555-456-7890",
                "address": "101 Medication Blvd"
            }
        ]
        
        # Create users
        created_users = []
        for user_data in users:
            user, created = User.objects.update_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            created_users.append(user)
            self.stdout.write(f"Created user '{user.username}'")
        
        return created_users
    
    def create_patients(self, doctor):
        """Create sample patients"""
        patients_data = [
            {
                "first_name": "Robert",
                "last_name": "Johnson",
                "date_of_birth": "1985-06-15",
                "gender": "M",
                "phone": "555-111-2222",
                "email": "robert.johnson@example.com",
                "address": "123 Main St, Anytown, USA",
                "emergency_contact_name": "Jennifer Johnson",
                "emergency_contact_phone": "555-333-4444",
                "emergency_contact_relation": "Spouse",
                "blood_group": "A+",
                "allergies": "Penicillin",
                "chronic_diseases": "None"
            },
            {
                "first_name": "Susan",
                "last_name": "Miller",
                "date_of_birth": "1992-03-28",
                "gender": "F",
                "phone": "555-222-3333",
                "email": "susan.miller@example.com",
                "address": "456 Oak St, Anytown, USA",
                "emergency_contact_name": "David Miller",
                "emergency_contact_phone": "555-444-5555",
                "emergency_contact_relation": "Brother",
                "blood_group": "O-",
                "allergies": "Sulfa drugs",
                "chronic_diseases": "Asthma"
            },
            {
                "first_name": "Michael",
                "last_name": "Davis",
                "date_of_birth": "1970-11-05",
                "gender": "M",
                "phone": "555-333-4444",
                "email": "michael.davis@example.com",
                "address": "789 Pine St, Anytown, USA",
                "emergency_contact_name": "Linda Davis",
                "emergency_contact_phone": "555-555-6666",
                "emergency_contact_relation": "Wife",
                "blood_group": "B+",
                "allergies": "None",
                "chronic_diseases": "Hypertension"
            }
        ]
        
        # Create patients
        created_patients = []
        for patient_data in patients_data:
            # Parse the date of birth
            dob = datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d').date()
            patient_data['date_of_birth'] = dob
            
            patient, created = Patient.objects.update_or_create(
                email=patient_data['email'],
                defaults=patient_data
            )
            created_patients.append(patient)
            self.stdout.write(f"Created patient '{patient.first_name} {patient.last_name}'")
        
        return created_patients
    
    def create_doctor_availability(self, doctor):
        """Create doctor availability slots"""
        # Create availability for all days of the week
        days_created = []
        for day in range(7):  # 0=Monday, 6=Sunday
            # Skip weekends
            if day == 5 or day == 6:  # Saturday, Sunday
                continue
                
            # Create morning slot
            morning, created = DoctorAvailability.objects.update_or_create(
                doctor=doctor,
                day_of_week=day,
                start_time=datetime.strptime('08:00', '%H:%M').time(),
                defaults={
                    'end_time': datetime.strptime('12:00', '%H:%M').time()
                }
            )
            days_created.append(morning)
            
            # Create afternoon slot
            afternoon, created = DoctorAvailability.objects.update_or_create(
                doctor=doctor,
                day_of_week=day,
                start_time=datetime.strptime('13:00', '%H:%M').time(),
                defaults={
                    'end_time': datetime.strptime('17:00', '%H:%M').time()
                }
            )
            days_created.append(afternoon)
            
            # Create evening slot
            evening, created = DoctorAvailability.objects.update_or_create(
                doctor=doctor,
                day_of_week=day,
                start_time=datetime.strptime('17:00', '%H:%M').time(),
                defaults={
                    'end_time': datetime.strptime('20:00', '%H:%M').time()
                }
            )
            days_created.append(evening)
        
        self.stdout.write(f"Created {len(days_created)} availability slots")
        return days_created
    
    def create_appointments(self, doctor, patients):
        """Create sample appointments"""
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Use the first patient for appointments
        first_patient = patients[0]
        
        # Create a couple of appointments
        appointments_data = [
            {
                "patient": first_patient,
                "doctor": doctor,
                "date": today,
                "start_time": datetime.strptime('10:00', '%H:%M').time(),
                "end_time": datetime.strptime('10:30', '%H:%M').time(),
                "appointment_type": Appointment.REGULAR,
                "status": Appointment.SCHEDULED,
                "reason": "Annual checkup",
                "notes": "Patient has been feeling well overall",
                "created_by": doctor
            },
            {
                "patient": first_patient,
                "doctor": doctor,
                "date": tomorrow,
                "start_time": datetime.strptime('14:30', '%H:%M').time(),
                "end_time": datetime.strptime('15:00', '%H:%M').time(),
                "appointment_type": Appointment.FOLLOW_UP,
                "status": Appointment.SCHEDULED,
                "reason": "Lab results review",
                "notes": "Follow up on blood test results",
                "created_by": doctor
            }
        ]
        
        # Create appointments
        created_appointments = []
        for appt_data in appointments_data:
            appt, created = Appointment.objects.update_or_create(
                patient=appt_data['patient'],
                doctor=appt_data['doctor'],
                date=appt_data['date'],
                start_time=appt_data['start_time'],
                defaults=appt_data
            )
            created_appointments.append(appt)
            self.stdout.write(f"Created appointment on {appt.date} at {appt.start_time}")
        
        return created_appointments 