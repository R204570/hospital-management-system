from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from patient.models import Nurse
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup floor assignments for nurses and create sample nurse staff'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='Create sample nurse users with floor assignments',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing nurses with appropriate floor assignments',
        )

    def handle(self, *args, **options):
        if options['create_sample']:
            self.create_sample_nurses()
        
        if options['update_existing']:
            self.update_existing_nurses()
        
        if not options['create_sample'] and not options['update_existing']:
            # Default behavior: do both
            self.create_sample_nurses()
            self.update_existing_nurses()

    def create_sample_nurses(self):
        """Create sample nurse users with appropriate floor assignments"""
        self.stdout.write('Creating sample nurses with floor assignments...')
        
        # Floor and specialization mapping
        floor_assignments = [
            # Floor 1: General Medicine
            {
                'floors': [1],
                'specialization': Nurse.GENERAL_MEDICINE,
                'nurses': [
                    {'name': 'Sarah Johnson', 'email': 'nurse.sarah@hospital.com', 'shift': '08:00-16:00'},
                    {'name': 'Michael Brown', 'email': 'nurse.michael@hospital.com', 'shift': '16:00-00:00'},
                    {'name': 'Lisa Davis', 'email': 'nurse.lisa@hospital.com', 'shift': '00:00-08:00'},
                ]
            },
            # Floor 2: Cardiology
            {
                'floors': [2],
                'specialization': Nurse.CARDIOLOGY,
                'nurses': [
                    {'name': 'Jennifer Wilson', 'email': 'nurse.jennifer@hospital.com', 'shift': '08:00-16:00'},
                    {'name': 'Robert Martinez', 'email': 'nurse.robert@hospital.com', 'shift': '16:00-00:00'},
                ]
            },
            # Floor 3: Orthopedic
            {
                'floors': [3],
                'specialization': Nurse.ORTHOPEDIC,
                'nurses': [
                    {'name': 'Emily Anderson', 'email': 'nurse.emily@hospital.com', 'shift': '08:00-16:00'},
                    {'name': 'David Thompson', 'email': 'nurse.david@hospital.com', 'shift': '16:00-00:00'},
                ]
            },
            # Floor 4: Neurology
            {
                'floors': [4],
                'specialization': Nurse.NEUROLOGY,
                'nurses': [
                    {'name': 'Amanda Garcia', 'email': 'nurse.amanda@hospital.com', 'shift': '08:00-16:00'},
                    {'name': 'Christopher Lee', 'email': 'nurse.christopher@hospital.com', 'shift': '16:00-00:00'},
                ]
            },
            # Floor 5: Oncology
            {
                'floors': [5],
                'specialization': Nurse.ONCOLOGY,
                'nurses': [
                    {'name': 'Jessica Rodriguez', 'email': 'nurse.jessica@hospital.com', 'shift': '08:00-16:00'},
                    {'name': 'Matthew White', 'email': 'nurse.matthew@hospital.com', 'shift': '16:00-00:00'},
                ]
            },
            # Floor 6: Emergency/ICU
            {
                'floors': [6],
                'specialization': Nurse.EMERGENCY,
                'nurses': [
                    {'name': 'Ashley Taylor', 'email': 'nurse.ashley@hospital.com', 'shift': '08:00-16:00'},
                    {'name': 'James Moore', 'email': 'nurse.james@hospital.com', 'shift': '16:00-00:00'},
                    {'name': 'Nicole Jackson', 'email': 'nurse.nicole@hospital.com', 'shift': '00:00-08:00'},
                ]
            },
            # Multi-floor supervisors
            {
                'floors': [1, 2, 3],
                'specialization': Nurse.GENERAL_NURSING,
                'nurses': [
                    {'name': 'Karen Supervisor', 'email': 'nurse.karen@hospital.com', 'shift': '08:00-16:00'},
                ]
            },
            {
                'floors': [4, 5, 6],
                'specialization': Nurse.GENERAL_NURSING,
                'nurses': [
                    {'name': 'Mark Supervisor', 'email': 'nurse.mark@hospital.com', 'shift': '16:00-00:00'},
                ]
            },
        ]
        
        created_count = 0
        
        for assignment in floor_assignments:
            for nurse_data in assignment['nurses']:
                # Check if user already exists
                if User.objects.filter(email=nurse_data['email']).exists():
                    self.stdout.write(f"  Nurse {nurse_data['name']} already exists, skipping...")
                    continue
                
                # Create nurse user
                names = nurse_data['name'].split(' ')
                first_name = names[0]
                last_name = ' '.join(names[1:]) if len(names) > 1 else ''
                
                user = User.objects.create_user(
                    username=nurse_data['email'].split('@')[0],
                    email=nurse_data['email'],
                    first_name=first_name,
                    last_name=last_name,
                    role=User.NURSE,
                    phone_number=f"+1{random.randint(1000000000, 9999999999)}"
                )
                user.set_password('nurse123')  # Default password
                user.save()
                
                # Parse shift times
                shift_times = nurse_data['shift'].split('-')
                shift_start = shift_times[0]
                shift_end = shift_times[1] if len(shift_times) > 1 else '08:00'
                
                # Create nurse assignment
                nurse_assignment = Nurse.objects.create(
                    nurse=user,
                    specialization=assignment['specialization'],
                    assigned_floors=assignment['floors'],
                    is_on_duty=True,
                    max_patients=15 if assignment['specialization'] == Nurse.EMERGENCY else 10,
                    shift_start=shift_start,
                    shift_end=shift_end
                )
                
                created_count += 1
                self.stdout.write(
                    f"  ✓ Created nurse: {nurse_data['name']} - "
                    f"Floors {assignment['floors']} - "
                    f"{assignment['specialization'].replace('_', ' ').title()}"
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} nurses with floor assignments!')
        )

    def update_existing_nurses(self):
        """Update existing nurses with appropriate floor assignments"""
        self.stdout.write('Updating existing nurses with floor assignments...')
        
        # Get all existing nurse users without assignments
        nurse_users = User.objects.filter(role=User.NURSE)
        updated_count = 0
        
        for user in nurse_users:
            # Check if nurse assignment already exists
            nurse_assignment, created = Nurse.objects.get_or_create(
                nurse=user,
                defaults={
                    'specialization': Nurse.GENERAL_NURSING,
                    'assigned_floors': [1, 2],  # Default assignment
                    'is_on_duty': True,
                    'max_patients': 10,
                    'shift_start': '08:00',
                    'shift_end': '16:00'
                }
            )
            
            if created:
                updated_count += 1
                self.stdout.write(f"  ✓ Created assignment for existing nurse: {user.get_full_name()}")
            elif not nurse_assignment.assigned_floors:
                # Update existing nurse assignment if no floors assigned
                nurse_assignment.assigned_floors = [1, 2]
                nurse_assignment.save()
                updated_count += 1
                self.stdout.write(f"  ✓ Updated floor assignment for: {user.get_full_name()}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} nurse assignments!')
        )
        
        # Display summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('NURSE FLOOR ASSIGNMENT SUMMARY')
        self.stdout.write('='*50)
        
        for floor in range(1, 7):
            # Use Python filtering instead of database filtering for JSONField
            all_nurses = Nurse.objects.all()
            nurses_on_floor = [nurse for nurse in all_nurses if nurse.assigned_floors and floor in nurse.assigned_floors]
            
            dept_name = {
                1: 'General Medicine',
                2: 'Cardiology', 
                3: 'Orthopedic',
                4: 'Neurology',
                5: 'Oncology',
                6: 'Emergency/ICU'
            }.get(floor, f'Floor {floor}')
            
            self.stdout.write(f'\nFloor {floor} ({dept_name}):')
            if nurses_on_floor:
                for nurse in nurses_on_floor:
                    shift_info = f"{nurse.shift_start}-{nurse.shift_end}" if nurse.shift_start and nurse.shift_end else "Not set"
                    self.stdout.write(
                        f"  • {nurse.nurse.get_full_name()} - "
                        f"{nurse.get_specialization_display()} - "
                        f"Shift: {shift_info}"
                    )
            else:
                self.stdout.write('  • No nurses assigned') 