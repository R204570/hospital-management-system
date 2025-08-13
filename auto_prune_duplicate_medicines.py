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

def select_best_medicine(group):
    """
    Select the best medicine to keep from a group of duplicates.
    Strategy: Keep the one with highest stock quantity.
    """
    return max(group, key=lambda med: med.stock_quantity)

def prune_duplicate_medicines():
    """
    Prune duplicate medicines, keeping only one from each group 
    (same name and strength but different suppliers)
    """
    duplicate_groups = find_duplicate_medicines()
    
    if not duplicate_groups:
        return
    
    print("\nPruning duplicate medicines...\n")
    
    total_removed = 0
    with transaction.atomic():
        for (name, strength), group in duplicate_groups.items():
            # Select the best medicine to keep (highest stock)
            medicine_to_keep = select_best_medicine(group)
            
            # Build list of medicines to remove
            medicines_to_remove = [med for med in group if med.id != medicine_to_keep.id]
            
            print(f"For '{name.title()}' ({strength}):")
            print(f"  KEEPING: ID: {medicine_to_keep.id}, Supplier: {medicine_to_keep.supplier.name if medicine_to_keep.supplier else 'None'}, Stock: {medicine_to_keep.stock_quantity}, Manufacturer: {medicine_to_keep.manufacturer}")
            print(f"  Removing {len(medicines_to_remove)} duplicate(s):")
            
            for med in medicines_to_remove:
                print(f"    - ID: {med.id}, Supplier: {med.supplier.name if med.supplier else 'None'}, Stock: {med.stock_quantity}, Manufacturer: {med.manufacturer}")
                med.delete()
                total_removed += 1
    
    print(f"\nPruning complete! Removed {total_removed} duplicate medicines, keeping one version of each unique medicine.")

if __name__ == "__main__":
    print("Starting automatic medicine duplicate pruning process...")
    prune_duplicate_medicines() 