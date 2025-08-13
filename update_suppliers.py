import os
import django
import random

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms_project.settings")
django.setup()

from pharmacy.models import Supplier

# List of sample countries for pharmaceutical suppliers
COUNTRIES = [
    'United States',
    'Switzerland',
    'United Kingdom',
    'Germany',
    'France',
    'Japan',
    'India',
    'Israel',
    'Denmark',
    'Canada',
    'Italy',
    'Australia',
    'Spain',
    'Sweden',
    'Belgium',
    'Netherlands',
    'Ireland',
    'China',
    'South Korea',
    'Brazil'
]

# List of sample websites
WEBSITE_FORMATS = [
    'https://www.{company}.com',
    'https://www.{company}.co',
    'https://www.{company}-pharma.com',
    'https://www.{company}pharmaceuticals.com',
    'https://www.{company}.net',
    'https://www.{company}-group.com',
    'https://www.{company}health.com',
    'https://www.{company}med.com',
]

def update_suppliers():
    """Update all suppliers with realistic country and representative information"""
    suppliers = Supplier.objects.all()
    updated_count = 0
    
    for supplier in suppliers:
        # Generate a random country if not set
        if not supplier.country:
            supplier.country = random.choice(COUNTRIES)
        
        # Generate a representative name if not set
        if not supplier.representative:
            first_names = ['John', 'David', 'Michael', 'Robert', 'James', 'William', 'Richard', 
                          'Sarah', 'Jennifer', 'Maria', 'Emily', 'Jessica', 'Elizabeth', 'Michelle']
            last_names = ['Smith', 'Johnson', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 
                         'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin']
            
            supplier.representative = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Generate a website if not set
        if not supplier.website:
            company_name = supplier.name.lower().replace('&', '').replace(' ', '')
            website_format = random.choice(WEBSITE_FORMATS)
            supplier.website = website_format.format(company=company_name)
        
        # Save the updated supplier
        supplier.save()
        updated_count += 1
        print(f"Updated {supplier.name} ({supplier.country}) - Rep: {supplier.representative}")
    
    print(f"\nSuccessfully updated {updated_count} suppliers with country and representative data.")

if __name__ == "__main__":
    update_suppliers() 