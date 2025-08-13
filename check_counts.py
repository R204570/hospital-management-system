import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from pharmacy.models import Category, Supplier, MedicineItem, InventoryItem

def check_database():
    categories = Category.objects.count()
    suppliers = Supplier.objects.count()
    medicines = MedicineItem.objects.count()
    equipment = InventoryItem.objects.count()
    
    print(f"Categories: {categories}")
    print(f"Suppliers: {suppliers}")
    print(f"Medicines: {medicines}")
    print(f"Equipment/Supplies: {equipment}")
    print(f"Total inventory items: {medicines + equipment}")
    
    # Print a sample of medicines
    print("\nSample Medicines:")
    for medicine in MedicineItem.objects.all()[:5]:
        print(f"- {medicine.name} ({medicine.strength}) - {medicine.dosage_form} - Stock: {medicine.stock_quantity}")
    
    # Print a sample of equipment
    print("\nSample Equipment/Supplies:")
    for item in InventoryItem.objects.all()[:5]:
        print(f"- {item.name} - Stock: {item.stock_quantity} - Disposable: {'Yes' if item.is_disposable else 'No'}")

if __name__ == "__main__":
    check_database() 