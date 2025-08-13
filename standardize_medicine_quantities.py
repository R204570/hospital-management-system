import os
import sys
import django
from collections import defaultdict

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from pharmacy.models import MedicineItem
from django.db.models import Sum, Count
from django.db import transaction

def find_duplicate_medicines():
    """
    Find medicines with the same name and strength but different suppliers
    and print information about them
    """
    print("\nFinding medicines with the same name and strength but different suppliers...\n")
    
    # Group medicines by name and strength
    medicines = MedicineItem.objects.all()
    medicine_groups = defaultdict(list)
    
    for medicine in medicines:
        # Skip medicines without strength information
        if not medicine.strength:
            continue
            
        # Use name and strength as a key
        key = (medicine.name.lower(), medicine.strength.lower())
        medicine_groups[key].append(medicine)
    
    # Filter groups with more than one medicine (duplicates)
    duplicate_groups = {k: v for k, v in medicine_groups.items() if len(v) > 1}
    
    if not duplicate_groups:
        print("No duplicate medicines found!")
        return None
    
    print(f"Found {len(duplicate_groups)} groups of medicines with the same name and strength but different suppliers:\n")
    
    # Print information about each group
    for i, ((name, strength), group) in enumerate(duplicate_groups.items(), 1):
        total_stock = sum(med.stock_quantity for med in group)
        
        print(f"Group {i}: {name.title()} - {strength}")
        print(f"  Total items: {len(group)}")
        print(f"  Total stock: {total_stock}")
        print("  Individual medicines:")
        
        for j, med in enumerate(group, 1):
            print(f"    {j}. ID: {med.id}, Supplier: {med.supplier.name if med.supplier else 'None'}, Stock: {med.stock_quantity}, Manufacturer: {med.manufacturer}")
        
        print("")
    
    return duplicate_groups

def standardize_medicine_quantities():
    """
    Standardize quantities for medicines with the same name and strength
    by giving them all the same quantity (the maximum from each group)
    """
    duplicate_groups = find_duplicate_medicines()
    
    if not duplicate_groups:
        return
    
    print("\nStandardizing medicine quantities...\n")
    
    with transaction.atomic():
        for (name, strength), group in duplicate_groups.items():
            # Calculate the maximum stock in the group
            max_stock = max(med.stock_quantity for med in group)
            
            print(f"Setting all '{name.title()}' ({strength}) medicines to stock quantity: {max_stock}")
            
            # Update all medicines in this group to have the same quantity
            for medicine in group:
                old_stock = medicine.stock_quantity
                medicine.stock_quantity = max_stock
                medicine.save()
                print(f"  Updated ID: {medicine.id}, Supplier: {medicine.supplier.name if medicine.supplier else 'None'}, Stock: {old_stock} → {max_stock}")
    
    print("\nQuantity standardization complete!")

if __name__ == "__main__":
    print("Starting medicine quantity standardization process...")
    answer = input("Would you like to standardize the medicine quantities? (y/n): ")
    
    if answer.lower() == 'y':
        standardize_medicine_quantities()
    else:
        # Just show the duplicates without modifying them
        find_duplicate_medicines() 