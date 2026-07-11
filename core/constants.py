"""
Centralized domain constants for the Hospital Management System.

Single source of truth for hospital-wide structures that were previously
duplicated across models (users.User, patient.Room, patient.Nurse):
staff roles, doctor specializations, and the floor -> department layout.
"""

# ---------------------------------------------------------------------------
# Staff roles
# ---------------------------------------------------------------------------
ADMIN = 'ADMIN'
DOCTOR = 'DOCTOR'
NURSE = 'NURSE'
RECEPTIONIST = 'RECEPTIONIST'
PHARMACIST = 'PHARMACIST'

ROLE_CHOICES = [
    (ADMIN, 'Administrator'),
    (DOCTOR, 'Doctor'),
    (NURSE, 'Nurse'),
    (RECEPTIONIST, 'Receptionist'),
    (PHARMACIST, 'Pharmacist'),
]

# ---------------------------------------------------------------------------
# Departments / doctor specializations (Multi-Specialty Hospital)
# ---------------------------------------------------------------------------
GENERAL_MEDICINE = 'GENERAL_MEDICINE'
CARDIOLOGY = 'CARDIOLOGY'
ORTHOPEDIC = 'ORTHOPEDIC'
NEUROLOGY = 'NEUROLOGY'
EMERGENCY = 'EMERGENCY'
ONCOLOGY = 'ONCOLOGY'

SPECIALIZATION_CHOICES = [
    (GENERAL_MEDICINE, 'General Medicine & Internal Medicine'),
    (CARDIOLOGY, 'Cardiology & Cardiovascular Surgery'),
    (ORTHOPEDIC, 'Orthopedic & Bone Surgery'),
    (NEUROLOGY, 'Neurology & Neurosurgery'),
    (EMERGENCY, 'Emergency Medicine & Critical Care'),
    (ONCOLOGY, 'Oncology & Cancer Treatment'),
]

DEPARTMENT_CHOICES = [
    (GENERAL_MEDICINE, 'General Medicine'),
    (CARDIOLOGY, 'Cardiology'),
    (ORTHOPEDIC, 'Orthopedic'),
    (NEUROLOGY, 'Neurology'),
    (ONCOLOGY, 'Oncology'),
    (EMERGENCY, 'Emergency'),
]

# Floor <-> department layout (6-floor multi-specialty hospital)
FLOOR_DEPARTMENT_MAP = {
    1: GENERAL_MEDICINE,
    2: CARDIOLOGY,
    3: ORTHOPEDIC,
    4: NEUROLOGY,
    5: EMERGENCY,
    6: ONCOLOGY,
}

# Reverse mapping: specialization/department -> floor
SPECIALIZATION_FLOORS = {dept: floor for floor, dept in FLOOR_DEPARTMENT_MAP.items()}

TOTAL_FLOORS = 6
FLOOR_CHOICES = [(i, f'Floor {i}') for i in range(1, TOTAL_FLOORS + 1)]
