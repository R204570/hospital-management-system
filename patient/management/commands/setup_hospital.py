from django.core.management.base import BaseCommand
from patient.models import Room, Bed
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup hospital with 6 floors, rooms and beds'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing rooms and beds before setup',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing rooms and beds...')
            Bed.objects.all().delete()
            Room.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        with transaction.atomic():
            self.create_hospital_structure()
            
        self.stdout.write(
            self.style.SUCCESS('Successfully set up hospital structure!')
        )

    def create_hospital_structure(self):
        """Create 6-floor hospital with 20 rooms per floor and multiple beds per room"""
        
        # Floor room distribution as defined in the model
        floor_room_distribution = {
            1: {Room.STANDARD: 12, Room.DELUXE: 8},                           # Floor 1: 12 Standard, 8 Deluxe
            2: {Room.STANDARD: 8, Room.DELUXE: 10, Room.LUXURY: 2},          # Floor 2: 8 Standard, 10 Deluxe, 2 Luxury
            3: {Room.STANDARD: 6, Room.DELUXE: 10, Room.LUXURY: 4},          # Floor 3: 6 Standard, 10 Deluxe, 4 Luxury
            4: {Room.DELUXE: 8, Room.LUXURY: 8, Room.SUITE: 4},              # Floor 4: 8 Deluxe, 8 Luxury, 4 Suite
            5: {Room.DELUXE: 6, Room.LUXURY: 10, Room.SUITE: 4},             # Floor 5: 6 Deluxe, 10 Luxury, 4 Suite
            6: {Room.ICU: 12, Room.LUXURY: 6, Room.SUITE: 2},                # Floor 6: 12 ICU, 6 Luxury, 2 Suite
        }

        # Department mapping by floor
        floor_departments = {
            1: Room.GENERAL_MEDICINE,    # Floor 1: General Medicine
            2: Room.CARDIOLOGY,          # Floor 2: Cardiology
            3: Room.ORTHOPEDIC,          # Floor 3: Orthopedic
            4: Room.NEUROLOGY,           # Floor 4: Neurology
            5: Room.ONCOLOGY,            # Floor 5: Oncology
            6: Room.EMERGENCY,           # Floor 6: Emergency & ICU
        }

        total_rooms = 0
        total_beds = 0

        for floor_num in range(1, 7):  # 6 floors
            department = floor_departments[floor_num]
            room_types = floor_room_distribution[floor_num]
            
            room_counter = 1
            
            self.stdout.write(f'Creating Floor {floor_num} - {department}')
            
            for room_type, count in room_types.items():
                for i in range(count):
                    # Create room with auto-generated room number
                    room = Room.objects.create(
                        floor=floor_num,
                        room_type=room_type,
                        department=department,
                        is_active=True
                    )
                    
                    total_rooms += 1
                    
                    # Create beds for this room based on room type capacity
                    bed_capacity = Room.ROOM_AMENITIES[room_type]['capacity']
                    
                    for bed_num in range(1, bed_capacity + 1):
                        bed = Bed.objects.create(
                            room=room,
                            is_occupied=False,
                            is_functional=True
                        )
                        total_beds += 1
                    
                    room_counter += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Floor {floor_num}: {sum(room_types.values())} rooms created'
                )
            )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('HOSPITAL SETUP COMPLETE'))
        self.stdout.write('='*50)
        self.stdout.write(f'Total Floors: 6')
        self.stdout.write(f'Total Rooms: {total_rooms}')
        self.stdout.write(f'Total Beds: {total_beds}')
        self.stdout.write('\nFloor Distribution:')
        
        for floor_num in range(1, 7):
            rooms_on_floor = Room.objects.filter(floor=floor_num)
            beds_on_floor = Bed.objects.filter(room__floor=floor_num)
            department = floor_departments[floor_num]
            
            self.stdout.write(
                f'  Floor {floor_num} ({department}): '
                f'{rooms_on_floor.count()} rooms, {beds_on_floor.count()} beds'
            )
            
            # Show room type breakdown
            for room_type in [Room.STANDARD, Room.DELUXE, Room.LUXURY, Room.ICU, Room.SUITE]:
                type_count = rooms_on_floor.filter(room_type=room_type).count()
                if type_count > 0:
                    self.stdout.write(
                        f'    - {Room.ROOM_AMENITIES[room_type]["description"]}: {type_count} rooms'
                    )

        self.stdout.write('\nRoom Types & Amenities:')
        for room_type, details in Room.ROOM_AMENITIES.items():
            self.stdout.write(
                f'  {details["description"]} (₹{details["daily_rate"]}/day):'
            )
            self.stdout.write(f'    Capacity: {details["capacity"]} bed(s)')
            self.stdout.write(f'    Amenities: {", ".join(details["amenities"])}') 