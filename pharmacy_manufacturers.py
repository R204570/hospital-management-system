import os
import django
import random

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms_project.settings")
django.setup()

from pharmacy.models import MedicineItem

# List of real pharmaceutical manufacturers
MANUFACTURERS = [
    'Pfizer',                  # United States
    'Johnson & Johnson',       # United States
    'Roche',                   # Switzerland
    'Novartis',                # Switzerland
    'Merck & Co.',             # United States
    'GlaxoSmithKline',         # United Kingdom
    'Sanofi',                  # France
    'Gilead Sciences',         # United States
    'AstraZeneca',             # United Kingdom
    'AbbVie',                  # United States
    'Bayer',                   # Germany
    'Eli Lilly',               # United States
    'Bristol-Myers Squibb',    # United States
    'Amgen',                   # United States
    'Boehringer Ingelheim',    # Germany
    'Teva Pharmaceutical',     # Israel
    'Novo Nordisk',            # Denmark
    'Takeda Pharmaceutical',   # Japan
    'Biogen',                  # United States
    'Allergan',                # Ireland
    'Sun Pharmaceutical',      # India
    'Cipla',                   # India
    'Lupin Limited',           # India
    'Dr. Reddy\'s Laboratories', # India
    'Astellas Pharma',         # Japan
    'Eisai',                   # Japan
    'Daiichi Sankyo',          # Japan
    'CSL Limited',             # Australia
    'Grifols',                 # Spain
    'Regeneron Pharmaceuticals', # United States
]

# Common medicines with their typical manufacturers
MEDICINE_MANUFACTURER_MAPPING = {
    'Lipitor': 'Pfizer',
    'Advil': 'Pfizer',
    'Viagra': 'Pfizer',
    'Celebrex': 'Pfizer',
    'Zithromax': 'Pfizer',
    'Tylenol': 'Johnson & Johnson',
    'Remicade': 'Johnson & Johnson',
    'Xarelto': 'Johnson & Johnson',
    'Prezista': 'Johnson & Johnson',
    'Invokana': 'Johnson & Johnson',
    'Herceptin': 'Roche',
    'Avastin': 'Roche',
    'Actemra': 'Roche',
    'Rituxan': 'Roche',
    'Tamiflu': 'Roche',
    'Gleevec': 'Novartis',
    'Diovan': 'Novartis',
    'Lucentis': 'Novartis',
    'Gilenya': 'Novartis',
    'Entresto': 'Novartis',
    'Keytruda': 'Merck & Co.',
    'Januvia': 'Merck & Co.',
    'Gardasil': 'Merck & Co.',
    'Zetia': 'Merck & Co.',
    'Isentress': 'Merck & Co.',
    'Advair': 'GlaxoSmithKline',
    'Ventolin': 'GlaxoSmithKline',
    'Augmentin': 'GlaxoSmithKline',
    'Flovent': 'GlaxoSmithKline',
    'Tivicay': 'GlaxoSmithKline',
    'Lantus': 'Sanofi',
    'Plavix': 'Sanofi',
    'Lovenox': 'Sanofi',
    'Ambien': 'Sanofi',
    'Allegra': 'Sanofi',
    'Harvoni': 'Gilead Sciences',
    'Truvada': 'Gilead Sciences',
    'Sovaldi': 'Gilead Sciences',
    'Atripla': 'Gilead Sciences',
    'Biktarvy': 'Gilead Sciences',
    'Crestor': 'AstraZeneca',
    'Nexium': 'AstraZeneca',
    'Symbicort': 'AstraZeneca',
    'Brilinta': 'AstraZeneca',
    'Faslodex': 'AstraZeneca',
    'Humira': 'AbbVie',
    'Imbruvica': 'AbbVie',
    'Viekira Pak': 'AbbVie',
    'Mavyret': 'AbbVie',
    'Rinvoq': 'AbbVie',
    'Aspirin': 'Bayer',
    'Xarelto': 'Bayer',
    'Mirena': 'Bayer',
    'Kogenate': 'Bayer',
    'Aleve': 'Bayer',
    'Humalog': 'Eli Lilly',
    'Cialis': 'Eli Lilly',
    'Trulicity': 'Eli Lilly',
    'Cymbalta': 'Eli Lilly',
    'Jardiance': 'Eli Lilly',
    'Eliquis': 'Bristol-Myers Squibb',
    'Opdivo': 'Bristol-Myers Squibb',
    'Orencia': 'Bristol-Myers Squibb',
    'Sprycel': 'Bristol-Myers Squibb',
    'Yervoy': 'Bristol-Myers Squibb',
    'Enbrel': 'Amgen',
    'Neulasta': 'Amgen',
    'Epogen': 'Amgen',
    'Prolia': 'Amgen',
    'Xgeva': 'Amgen',
}

def update_manufacturers():
    """Update all medicine items with appropriate manufacturers"""
    medicines = MedicineItem.objects.all()
    updated_count = 0
    
    for medicine in medicines:
        # Check if this medicine has a specific manufacturer mapping
        if medicine.name in MEDICINE_MANUFACTURER_MAPPING:
            manufacturer = MEDICINE_MANUFACTURER_MAPPING[medicine.name]
        else:
            # If not found in mapping, assign a random manufacturer
            manufacturer = random.choice(MANUFACTURERS)
        
        # Update the manufacturer field
        medicine.manufacturer = manufacturer
        medicine.save()
        updated_count += 1
        print(f"Updated {medicine.name} with manufacturer: {manufacturer}")
    
    print(f"\nSuccessfully updated {updated_count} medicines with real manufacturer data.")

if __name__ == "__main__":
    update_manufacturers() 