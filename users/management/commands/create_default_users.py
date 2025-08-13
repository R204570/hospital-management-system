from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User


class Command(BaseCommand):
    help = 'Creates default users for each role in the HMS system'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            # Create Admin
            admin_user, admin_created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'email': 'admin@hospital.com',
                    'role': User.ADMIN,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            if admin_created:
                admin_user.set_password('Admin@123')
                admin_user.save()
                self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Admin user already exists: {admin_user.username}'))
            
            # Create Doctor
            doctor_user, doctor_created = User.objects.get_or_create(
                username='doctor',
                defaults={
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'email': 'doctor@hospital.com',
                    'role': User.DOCTOR,
                    'specialization': 'General Medicine',
                    'qualification': 'MD, General Medicine',
                    'phone_number': '555-123-4567',
                }
            )
            
            if doctor_created:
                doctor_user.set_password('Doctor@123')
                doctor_user.save()
                self.stdout.write(self.style.SUCCESS(f'Created doctor user: {doctor_user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Doctor user already exists: {doctor_user.username}'))
            
            # Create Nurse
            nurse_user, nurse_created = User.objects.get_or_create(
                username='nurse',
                defaults={
                    'first_name': 'Emily',
                    'last_name': 'Johnson',
                    'email': 'nurse@hospital.com',
                    'role': User.NURSE,
                    'phone_number': '555-234-5678',
                }
            )
            
            if nurse_created:
                nurse_user.set_password('Nurse@123')
                nurse_user.save()
                self.stdout.write(self.style.SUCCESS(f'Created nurse user: {nurse_user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Nurse user already exists: {nurse_user.username}'))
            
            # Create Receptionist
            receptionist_user, receptionist_created = User.objects.get_or_create(
                username='receptionist',
                defaults={
                    'first_name': 'Sarah',
                    'last_name': 'Wilson',
                    'email': 'receptionist@hospital.com',
                    'role': User.RECEPTIONIST,
                    'phone_number': '555-345-6789',
                }
            )
            
            if receptionist_created:
                receptionist_user.set_password('Reception@123')
                receptionist_user.save()
                self.stdout.write(self.style.SUCCESS(f'Created receptionist user: {receptionist_user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Receptionist user already exists: {receptionist_user.username}'))
            
            # Create Pharmacist
            pharmacist_user, pharmacist_created = User.objects.get_or_create(
                username='pharmacist',
                defaults={
                    'first_name': 'Michael',
                    'last_name': 'Brown',
                    'email': 'pharmacist@hospital.com',
                    'role': User.PHARMACIST,
                    'phone_number': '555-456-7890',
                }
            )
            
            if pharmacist_created:
                pharmacist_user.set_password('Pharmacy@123')
                pharmacist_user.save()
                self.stdout.write(self.style.SUCCESS(f'Created pharmacist user: {pharmacist_user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Pharmacist user already exists: {pharmacist_user.username}'))
                
        # Summary message
        self.stdout.write(self.style.SUCCESS('Default users created successfully!'))
        self.stdout.write('\nLogin Credentials:')
        self.stdout.write('-----------------')
        self.stdout.write('Admin: username=admin, password=Admin@123')
        self.stdout.write('Doctor: username=doctor, password=Doctor@123')
        self.stdout.write('Nurse: username=nurse, password=Nurse@123')
        self.stdout.write('Receptionist: username=receptionist, password=Reception@123')
        self.stdout.write('Pharmacist: username=pharmacist, password=Pharmacy@123') 