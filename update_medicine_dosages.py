import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from pharmacy.models import MedicineItem, Category

# Common dosage strengths by medicine type/category
DOSAGE_MAPPINGS = {
    # Antibiotics
    'Amoxicillin': ['250mg', '500mg', '875mg'],
    'Azithromycin': ['250mg', '500mg', '600mg'],
    'Ciprofloxacin': ['250mg', '500mg', '750mg'],
    'Doxycycline': ['50mg', '100mg'],
    'Cephalexin': ['250mg', '500mg'],
    'Metronidazole': ['250mg', '500mg'],
    'Trimethoprim': ['80mg', '160mg'],
    'Clarithromycin': ['250mg', '500mg'],
    'Levofloxacin': ['250mg', '500mg', '750mg'],
    'Moxifloxacin': ['400mg'],
    
    # Pain relievers/Analgesics
    'Acetaminophen': ['325mg', '500mg', '650mg'],
    'Ibuprofen': ['200mg', '400mg', '600mg', '800mg'],
    'Naproxen': ['220mg', '250mg', '275mg', '500mg'],
    'Aspirin': ['81mg', '325mg', '500mg'],
    'Diclofenac': ['25mg', '50mg', '75mg', '100mg'],
    'Meloxicam': ['7.5mg', '15mg'],
    'Celecoxib': ['100mg', '200mg'],
    'Tramadol': ['50mg', '100mg'],
    'Oxycodone': ['5mg', '10mg', '15mg', '20mg', '30mg'],
    'Hydrocodone': ['5mg', '7.5mg', '10mg'],
    
    # Antihypertensives
    'Lisinopril': ['2.5mg', '5mg', '10mg', '20mg', '40mg'],
    'Amlodipine': ['2.5mg', '5mg', '10mg'],
    'Losartan': ['25mg', '50mg', '100mg'],
    'Metoprolol': ['25mg', '50mg', '100mg', '200mg'],
    'Atenolol': ['25mg', '50mg', '100mg'],
    'Hydrochlorothiazide': ['12.5mg', '25mg', '50mg'],
    'Valsartan': ['40mg', '80mg', '160mg', '320mg'],
    'Carvedilol': ['3.125mg', '6.25mg', '12.5mg', '25mg'],
    'Enalapril': ['2.5mg', '5mg', '10mg', '20mg'],
    'Furosemide': ['20mg', '40mg', '80mg'],
    
    # Antidiabetics
    'Metformin': ['500mg', '850mg', '1000mg'],
    'Glipizide': ['5mg', '10mg'],
    'Glyburide': ['1.25mg', '2.5mg', '5mg'],
    'Sitagliptin': ['25mg', '50mg', '100mg'],
    'Empagliflozin': ['10mg', '25mg'],
    'Pioglitazone': ['15mg', '30mg', '45mg'],
    'Glimepiride': ['1mg', '2mg', '4mg'],
    
    # Antihistamines
    'Cetirizine': ['5mg', '10mg'],
    'Loratadine': ['10mg'],
    'Fexofenadine': ['30mg', '60mg', '120mg', '180mg'],
    'Diphenhydramine': ['25mg', '50mg'],
    'Desloratadine': ['5mg'],
    
    # Corticosteroids
    'Prednisone': ['1mg', '2.5mg', '5mg', '10mg', '20mg', '50mg'],
    'Dexamethasone': ['0.5mg', '0.75mg', '1mg', '1.5mg', '4mg', '6mg'],
    'Budesonide': ['0.25mg', '0.5mg', '1mg', '3mg'],
    'Fluticasone': ['50mcg', '100mcg', '250mcg', '500mcg'],
    
    # Vaccines
    'Influenza Vaccine': ['0.5mL'],
    'Pneumococcal Vaccine': ['0.5mL'], 
    'Hepatitis B Vaccine': ['0.5mL', '1mL'],
    'Tetanus Vaccine': ['0.5mL'],
    'COVID-19 Vaccine': ['0.3mL', '0.5mL'],
    'HPV Vaccine': ['0.5mL'],
    
    # Injections
    'Insulin': ['100units/mL'],
    'Heparin': ['1000units/mL', '5000units/mL', '10000units/mL'],
    'Epinephrine': ['0.3mg/mL', '1mg/mL'],
    'Vitamin B12': ['1000mcg/mL'],
    
    # Syrups
    'Cough Syrup': ['100mL', '200mL'],
    'Paracetamol Syrup': ['120mg/5mL', '250mg/5mL'],
    'Amoxicillin Suspension': ['125mg/5mL', '250mg/5mL'],
    'Cetirizine Syrup': ['5mg/5mL'],
    'Multivitamin Syrup': ['100mL', '200mL']
}

# Default dosage forms by medicine type
DEFAULT_DOSAGE_FORMS = {
    'Tablet': ['25mg', '50mg', '100mg', '200mg', '250mg', '500mg'],
    'Capsule': ['25mg', '50mg', '100mg', '200mg', '250mg', '500mg'],
    'Suspension': ['125mg/5mL', '250mg/5mL'],
    'Syrup': ['5mg/5mL', '10mg/5mL', '100mL', '150mL'],
    'Injection': ['10mg/mL', '20mg/mL', '50mg/mL', '0.5mL', '1mL'],
    'Cream': ['0.5%', '1%', '2%', '5%'],
    'Ointment': ['0.5%', '1%', '2%', '5%'],
    'Gel': ['0.5%', '1%', '2%', '5%'],
    'Liquid': ['100mL', '200mL', '10mg/mL'],
    'Drops': ['0.5%', '1%', '10mL'],
    'Inhaler': ['100mcg', '250mcg']
}

def check_current_strengths():
    """Check and print the current state of medicine strengths"""
    medicines = MedicineItem.objects.all()
    
    total_count = medicines.count()
    with_strength = 0
    without_strength = 0
    
    print(f"Checking current strengths for {total_count} medicines...\n")
    
    # Count medicines with and without strength
    for medicine in medicines:
        if medicine.strength and medicine.strength.strip():
            with_strength += 1
        else:
            without_strength += 1
            print(f"Medicine without strength: {medicine.name} (ID: {medicine.id})")
    
    print(f"\nSummary:")
    print(f"Total medicines: {total_count}")
    print(f"Medicines with strength: {with_strength}")
    print(f"Medicines without strength: {without_strength}")
    
    return total_count, with_strength, without_strength

def update_medicine_strengths(force_update=False):
    """Update all medicine items with appropriate strengths based on their names"""
    medicines = MedicineItem.objects.all()
    updated_count = 0
    not_updated_count = 0
    
    for medicine in medicines:
        # Skip if strength is already set and not empty, unless force_update is True
        if not force_update and medicine.strength and medicine.strength.strip():
            continue
            
        # Try to find a matching dosage in our mappings
        strength = None
        
        # Check if the medicine name is in our mappings
        for med_name, strengths in DOSAGE_MAPPINGS.items():
            if med_name.lower() in medicine.name.lower():
                strength = random.choice(strengths)
                break
        
        # If no specific mapping found, use default based on dosage form
        if not strength and medicine.dosage_form:
            dosage_form = medicine.dosage_form
            for form_name, strengths in DEFAULT_DOSAGE_FORMS.items():
                if form_name.lower() in dosage_form.lower():
                    strength = random.choice(strengths)
                    break
        
        # If still no strength found, assign a generic one based on category
        if not strength:
            if medicine.category:
                category_name = medicine.category.name.lower()
                if 'antibiotics' in category_name:
                    strength = random.choice(['250mg', '500mg'])
                elif 'analgesics' in category_name or 'pain' in category_name:
                    strength = random.choice(['325mg', '500mg'])
                elif 'antidiabetics' in category_name or 'diabetes' in category_name:
                    strength = random.choice(['500mg', '850mg', '1000mg'])
                elif 'injection' in category_name:
                    strength = random.choice(['10mg/mL', '20mg/mL', '0.5mL'])
                elif 'syrup' in category_name:
                    strength = random.choice(['100mL', '125mg/5mL'])
                elif 'vaccine' in category_name:
                    strength = '0.5mL'
                else:
                    # Generic fallback
                    strength = random.choice(['50mg', '100mg', '200mg', '500mg'])
            else:
                # Last resort
                strength = random.choice(['100mg', '250mg', '500mg'])
        
        # Update the medicine with the new strength
        if strength:
            old_strength = medicine.strength or "None"
            medicine.strength = strength
            medicine.save()
            print(f"Updated {medicine.name} with strength: {strength} (was: {old_strength})")
            updated_count += 1
        else:
            print(f"Could not find appropriate strength for {medicine.name}")
            not_updated_count += 1
    
    print(f"\nSuccess! Updated {updated_count} medicines with specific strengths.")
    print(f"Could not update {not_updated_count} medicines.")

if __name__ == "__main__":
    print("Checking current medicine strengths in the database...")
    total, with_strength, without_strength = check_current_strengths()
    
    # Force update all medicines automatically
    force_update = True
    
    print("\nUpdating all medicine strengths...")
    update_medicine_strengths(force_update=force_update) 