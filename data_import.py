import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from pharmacy.models import Category, Supplier, MedicineItem, InventoryItem

# Create categories first
def create_categories():
    print("Creating categories...")
    categories = [
        # Medicine categories
        {"name": "Antibiotics", "type": Category.MEDICINE, "description": "Medicines that combat bacterial infections"},
        {"name": "Analgesics", "type": Category.MEDICINE, "description": "Pain relievers"},
        {"name": "Antipyretics", "type": Category.MEDICINE, "description": "Fever reducers"},
        {"name": "Antihypertensives", "type": Category.MEDICINE, "description": "Blood pressure medications"},
        {"name": "Antidiabetics", "type": Category.MEDICINE, "description": "Diabetes medications"},
        {"name": "Antihistamines", "type": Category.MEDICINE, "description": "Allergy medications"},
        {"name": "Antacids", "type": Category.MEDICINE, "description": "Heartburn and indigestion relief"},
        {"name": "Antidepressants", "type": Category.MEDICINE, "description": "Depression medications"},
        {"name": "Antipsychotics", "type": Category.MEDICINE, "description": "Mental health medications"},
        {"name": "Antivirals", "type": Category.MEDICINE, "description": "Virus-fighting medications"},
        {"name": "Antifungals", "type": Category.MEDICINE, "description": "Fungal infection treatments"},
        {"name": "Bronchodilators", "type": Category.MEDICINE, "description": "Asthma and COPD medications"},
        {"name": "Cardiovascular", "type": Category.MEDICINE, "description": "Heart-related medications"},
        {"name": "Corticosteroids", "type": Category.MEDICINE, "description": "Anti-inflammatory steroids"},
        {"name": "Decongestants", "type": Category.MEDICINE, "description": "Nasal congestion relief"},
        {"name": "Diuretics", "type": Category.MEDICINE, "description": "Water pills"},
        {"name": "Expectorants", "type": Category.MEDICINE, "description": "Cough medicines"},
        {"name": "Hormones", "type": Category.MEDICINE, "description": "Hormone replacements and treatments"},
        {"name": "Immunosuppressants", "type": Category.MEDICINE, "description": "Immune system suppressors"},
        {"name": "Laxatives", "type": Category.MEDICINE, "description": "Constipation relief"},
        {"name": "Multivitamins", "type": Category.MEDICINE, "description": "Nutritional supplements"},
        {"name": "Muscle Relaxants", "type": Category.MEDICINE, "description": "Muscle spasm treatments"},
        {"name": "Sedatives", "type": Category.MEDICINE, "description": "Sleep aids and anxiety relievers"},
        {"name": "Statins", "type": Category.MEDICINE, "description": "Cholesterol-lowering medications"},
        {"name": "Vaccines", "type": Category.MEDICINE, "description": "Disease prevention"},
        {"name": "Syrups", "type": Category.MEDICINE, "description": "Liquid medication for ease of consumption"},
        {"name": "Injections", "type": Category.MEDICINE, "description": "Injectable medications"},
        {"name": "Topical Medications", "type": Category.MEDICINE, "description": "External use medications"},
        {"name": "IV Fluids", "type": Category.MEDICINE, "description": "Intravenous solutions"},
        
        # Equipment categories
        {"name": "Diagnostic Equipment", "type": Category.EQUIPMENT, "description": "Tools for diagnosis"},
        {"name": "Monitoring Equipment", "type": Category.EQUIPMENT, "description": "Patient monitoring devices"},
        {"name": "Surgical Instruments", "type": Category.SURGICAL, "description": "Tools for surgical procedures"},
        {"name": "Medical Supplies", "type": Category.CONSUMABLE, "description": "General medical supplies"},
        {"name": "Respiratory Equipment", "type": Category.EQUIPMENT, "description": "Breathing assistance devices"},
        {"name": "Orthopedic Supplies", "type": Category.EQUIPMENT, "description": "Bone and joint related equipment"},
        {"name": "First Aid Supplies", "type": Category.CONSUMABLE, "description": "Emergency treatment supplies"},
        {"name": "Laboratory Equipment", "type": Category.EQUIPMENT, "description": "Lab testing equipment"},
        {"name": "Sterilization Supplies", "type": Category.CONSUMABLE, "description": "Cleaning and sterilizing items"},
        {"name": "Personal Protective Equipment", "type": Category.CONSUMABLE, "description": "Protection gear"}
    ]
    
    category_objects = []
    for cat_data in categories:
        cat, created = Category.objects.get_or_create(
            name=cat_data["name"],
            defaults={
                "type": cat_data["type"],
                "description": cat_data["description"]
            }
        )
        category_objects.append(cat)
        if created:
            print(f"Created category: {cat.name}")
        else:
            print(f"Category already exists: {cat.name}")
    
    return category_objects

# Create suppliers
def create_suppliers():
    print("Creating suppliers...")
    suppliers = [
        {
            "name": "MediPharm Distributors",
            "contact_person": "John Smith",
            "phone": "123-456-7890",
            "email": "john@medipharm.com",
            "address": "123 Pharma St, Medical City"
        },
        {
            "name": "Global Healthcare Supplies",
            "contact_person": "Emily Johnson",
            "phone": "234-567-8901",
            "email": "emily@globalhealthcare.com",
            "address": "456 Health Ave, Wellness Town"
        },
        {
            "name": "MediTech Equipment Co.",
            "contact_person": "Robert Davis",
            "phone": "345-678-9012",
            "email": "robert@meditech.com",
            "address": "789 Tech Blvd, Innovation City"
        },
        {
            "name": "Sunrise Pharmaceuticals",
            "contact_person": "Sarah Williams",
            "phone": "456-789-0123",
            "email": "sarah@sunrisepharma.com",
            "address": "101 Sunrise Rd, Health Valley"
        },
        {
            "name": "MedEquip Solutions",
            "contact_person": "Michael Brown",
            "phone": "567-890-1234",
            "email": "michael@medequip.com",
            "address": "202 Equipment Lane, Supply City"
        }
    ]
    
    supplier_objects = []
    for sup_data in suppliers:
        sup, created = Supplier.objects.get_or_create(
            name=sup_data["name"],
            defaults={
                "contact_person": sup_data["contact_person"],
                "phone": sup_data["phone"],
                "email": sup_data["email"],
                "address": sup_data["address"],
                "is_active": True
            }
        )
        supplier_objects.append(sup)
        if created:
            print(f"Created supplier: {sup.name}")
        else:
            print(f"Supplier already exists: {sup.name}")
    
    return supplier_objects

# Helper functions for creating random data
def random_price(min_price, max_price):
    price = random.uniform(min_price, max_price)
    return Decimal(str(round(price, 2)))

def random_future_date(min_days=30, max_days=730):
    days = random.randint(min_days, max_days)
    return (datetime.now() + timedelta(days=days)).date()

def get_category_by_name(categories, name):
    for category in categories:
        if category.name == name:
            return category
    return None

def get_random_supplier(suppliers):
    return random.choice(suppliers)

# Create medicines
def create_medicines(categories, suppliers):
    print("Creating medicines...")
    
    # Define forms of medicine
    forms = ["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Ointment", "Gel", "Solution", "Suspension", "Powder", "Drops", "Inhaler", "Patch", "Suppository", "Lozenge"]
    
    # Define common manufacturers
    manufacturers = ["Pfizer", "Johnson & Johnson", "Merck", "Novartis", "Roche", "GlaxoSmithKline", "Sanofi", "AbbVie", "Bayer", "Eli Lilly", "Bristol-Myers Squibb", "AstraZeneca", "Amgen", "Gilead Sciences", "Teva"]
    
    # Define antibiotics
    antibiotics = [
        {"name": "Amoxicillin", "forms": ["Tablet", "Capsule", "Syrup"], "strengths": ["250mg", "500mg", "875mg"]},
        {"name": "Azithromycin", "forms": ["Tablet", "Capsule", "Syrup"], "strengths": ["250mg", "500mg"]},
        {"name": "Ciprofloxacin", "forms": ["Tablet", "Injection"], "strengths": ["250mg", "500mg", "750mg"]},
        {"name": "Doxycycline", "forms": ["Tablet", "Capsule"], "strengths": ["50mg", "100mg"]},
        {"name": "Cephalexin", "forms": ["Tablet", "Capsule", "Syrup"], "strengths": ["250mg", "500mg"]},
        {"name": "Metronidazole", "forms": ["Tablet", "Injection", "Gel"], "strengths": ["250mg", "500mg", "0.75%"]},
        {"name": "Clindamycin", "forms": ["Capsule", "Injection", "Solution"], "strengths": ["150mg", "300mg", "2%"]},
        {"name": "Trimethoprim-Sulfamethoxazole", "forms": ["Tablet", "Suspension"], "strengths": ["80/400mg", "160/800mg"]},
        {"name": "Vancomycin", "forms": ["Injection", "Capsule"], "strengths": ["125mg", "250mg", "500mg", "1g"]},
        {"name": "Gentamicin", "forms": ["Injection", "Cream", "Drops"], "strengths": ["40mg/ml", "0.1%", "0.3%"]}
    ]
    
    # Define pain relievers
    pain_relievers = [
        {"name": "Acetaminophen", "forms": ["Tablet", "Capsule", "Syrup"], "strengths": ["325mg", "500mg", "650mg"]},
        {"name": "Ibuprofen", "forms": ["Tablet", "Capsule", "Syrup", "Gel"], "strengths": ["200mg", "400mg", "600mg", "800mg", "5%"]},
        {"name": "Naproxen", "forms": ["Tablet", "Suspension"], "strengths": ["220mg", "375mg", "500mg"]},
        {"name": "Aspirin", "forms": ["Tablet", "Capsule"], "strengths": ["81mg", "325mg", "500mg"]},
        {"name": "Diclofenac", "forms": ["Tablet", "Gel", "Patch"], "strengths": ["50mg", "75mg", "100mg", "1%", "1.3%"]},
        {"name": "Morphine", "forms": ["Tablet", "Solution", "Injection"], "strengths": ["15mg", "30mg", "10mg/5ml", "10mg/ml"]},
        {"name": "Oxycodone", "forms": ["Tablet", "Capsule", "Solution"], "strengths": ["5mg", "10mg", "15mg", "20mg", "5mg/5ml"]},
        {"name": "Tramadol", "forms": ["Tablet", "Capsule"], "strengths": ["50mg", "100mg", "200mg"]},
        {"name": "Fentanyl", "forms": ["Patch", "Injection", "Lozenge"], "strengths": ["12mcg/hr", "25mcg/hr", "50mcg/hr", "100mcg/hr", "100mcg"]},
        {"name": "Celecoxib", "forms": ["Capsule"], "strengths": ["100mg", "200mg", "400mg"]}
    ]
    
    # Define antihypertensives
    antihypertensives = [
        {"name": "Lisinopril", "forms": ["Tablet"], "strengths": ["2.5mg", "5mg", "10mg", "20mg", "40mg"]},
        {"name": "Amlodipine", "forms": ["Tablet"], "strengths": ["2.5mg", "5mg", "10mg"]},
        {"name": "Metoprolol", "forms": ["Tablet"], "strengths": ["25mg", "50mg", "100mg", "200mg"]},
        {"name": "Losartan", "forms": ["Tablet"], "strengths": ["25mg", "50mg", "100mg"]},
        {"name": "Valsartan", "forms": ["Tablet", "Capsule"], "strengths": ["40mg", "80mg", "160mg", "320mg"]},
        {"name": "Hydrochlorothiazide", "forms": ["Tablet"], "strengths": ["12.5mg", "25mg", "50mg"]},
        {"name": "Carvedilol", "forms": ["Tablet"], "strengths": ["3.125mg", "6.25mg", "12.5mg", "25mg"]},
        {"name": "Furosemide", "forms": ["Tablet", "Solution", "Injection"], "strengths": ["20mg", "40mg", "80mg", "10mg/ml"]},
        {"name": "Atenolol", "forms": ["Tablet"], "strengths": ["25mg", "50mg", "100mg"]},
        {"name": "Diltiazem", "forms": ["Tablet", "Capsule"], "strengths": ["30mg", "60mg", "90mg", "120mg"]}
    ]

    # Define antidiabetics
    antidiabetics = [
        {"name": "Metformin", "forms": ["Tablet"], "strengths": ["500mg", "850mg", "1000mg"]},
        {"name": "Glipizide", "forms": ["Tablet"], "strengths": ["5mg", "10mg"]},
        {"name": "Glyburide", "forms": ["Tablet"], "strengths": ["1.25mg", "2.5mg", "5mg"]},
        {"name": "Insulin Regular", "forms": ["Injection"], "strengths": ["100units/ml"]},
        {"name": "Insulin NPH", "forms": ["Injection"], "strengths": ["100units/ml"]},
        {"name": "Insulin Glargine", "forms": ["Injection"], "strengths": ["100units/ml", "300units/ml"]},
        {"name": "Insulin Lispro", "forms": ["Injection"], "strengths": ["100units/ml"]},
        {"name": "Sitagliptin", "forms": ["Tablet"], "strengths": ["25mg", "50mg", "100mg"]},
        {"name": "Empagliflozin", "forms": ["Tablet"], "strengths": ["10mg", "25mg"]},
        {"name": "Liraglutide", "forms": ["Injection"], "strengths": ["6mg/ml"]}
    ]
    
    # Get categories
    antibiotic_cat = get_category_by_name(categories, "Antibiotics")
    analgesic_cat = get_category_by_name(categories, "Analgesics")
    antihypertensive_cat = get_category_by_name(categories, "Antihypertensives")
    antidiabetic_cat = get_category_by_name(categories, "Antidiabetics")
    syrup_cat = get_category_by_name(categories, "Syrups")
    injection_cat = get_category_by_name(categories, "Injections")
    
    # Combine all medicine lists
    all_medicines = []
    
    # Process antibiotics
    for med in antibiotics:
        for form in med["forms"]:
            for strength in med["strengths"]:
                all_medicines.append({
                    "name": f"{med['name']}",
                    "generic_name": med["name"].lower(),
                    "strength": strength,
                    "dosage_form": form,
                    "category": antibiotic_cat if form != "Syrup" and form != "Injection" else (syrup_cat if form == "Syrup" else injection_cat),
                    "manufacturer": random.choice(manufacturers),
                    "requires_prescription": random.choice([True, False]),
                    "purchase_price": random_price(2, 15),
                    "stock_quantity": random.randint(20, 200)
                })
    
    # Process pain relievers
    for med in pain_relievers:
        for form in med["forms"]:
            for strength in med["strengths"]:
                all_medicines.append({
                    "name": f"{med['name']}",
                    "generic_name": med["name"].lower(),
                    "strength": strength,
                    "dosage_form": form,
                    "category": analgesic_cat if form != "Syrup" and form != "Injection" else (syrup_cat if form == "Syrup" else injection_cat),
                    "manufacturer": random.choice(manufacturers),
                    "requires_prescription": random.choice([True, False]),
                    "purchase_price": random_price(1, 10),
                    "stock_quantity": random.randint(30, 250)
                })
    
    # Process antihypertensives
    for med in antihypertensives:
        for form in med["forms"]:
            for strength in med["strengths"]:
                all_medicines.append({
                    "name": f"{med['name']}",
                    "generic_name": med["name"].lower(),
                    "strength": strength,
                    "dosage_form": form,
                    "category": antihypertensive_cat if form != "Syrup" and form != "Injection" else (syrup_cat if form == "Syrup" else injection_cat),
                    "manufacturer": random.choice(manufacturers),
                    "requires_prescription": True,
                    "purchase_price": random_price(3, 20),
                    "stock_quantity": random.randint(25, 180)
                })
    
    # Process antidiabetics
    for med in antidiabetics:
        for form in med["forms"]:
            for strength in med["strengths"]:
                all_medicines.append({
                    "name": f"{med['name']}",
                    "generic_name": med["name"].lower(),
                    "strength": strength,
                    "dosage_form": form,
                    "category": antidiabetic_cat if form != "Syrup" and form != "Injection" else (syrup_cat if form == "Syrup" else injection_cat),
                    "manufacturer": random.choice(manufacturers),
                    "requires_prescription": True,
                    "purchase_price": random_price(5, 30),
                    "stock_quantity": random.randint(15, 150)
                })
    
    # Create medicines in the database
    created_count = 0
    for med_data in all_medicines:
        purchase_price = med_data.pop("purchase_price")
        stock_qty = med_data.pop("stock_quantity")
        
        # Add markup for selling price (30-50% markup)
        markup = random.uniform(1.3, 1.5)
        selling_price = purchase_price * Decimal(str(markup))
        selling_price = Decimal(str(round(selling_price, 2)))
        
        try:
            med, created = MedicineItem.objects.get_or_create(
                name=med_data["name"],
                strength=med_data["strength"],
                dosage_form=med_data["dosage_form"],
                defaults={
                    "generic_name": med_data["generic_name"],
                    "category": med_data["category"],
                    "supplier": get_random_supplier(suppliers),
                    "manufacturer": med_data["manufacturer"],
                    "requires_prescription": med_data["requires_prescription"],
                    "purchase_price": purchase_price,
                    "selling_price": selling_price,
                    "stock_quantity": stock_qty,
                    "reorder_level": max(10, int(stock_qty * 0.2)),  # 20% of stock as reorder level
                    "batch_number": f"B{random.randint(10000, 99999)}",
                    "expiry_date": random_future_date()
                }
            )
            
            if created:
                created_count += 1
                if created_count % 50 == 0:
                    print(f"Created {created_count} medicines...")
        except Exception as e:
            print(f"Error creating medicine {med_data['name']}: {str(e)}")
    
    print(f"Total medicines created: {created_count}")

# Create equipment and supplies
def create_equipment(categories, suppliers):
    print("Creating equipment and medical supplies...")
    
    # Get relevant categories
    diagnostic_cat = get_category_by_name(categories, "Diagnostic Equipment")
    monitoring_cat = get_category_by_name(categories, "Monitoring Equipment")
    surgical_cat = get_category_by_name(categories, "Surgical Instruments")
    medical_supplies_cat = get_category_by_name(categories, "Medical Supplies")
    respiratory_cat = get_category_by_name(categories, "Respiratory Equipment")
    orthopedic_cat = get_category_by_name(categories, "Orthopedic Supplies")
    first_aid_cat = get_category_by_name(categories, "First Aid Supplies")
    lab_cat = get_category_by_name(categories, "Laboratory Equipment")
    sterilization_cat = get_category_by_name(categories, "Sterilization Supplies")
    ppe_cat = get_category_by_name(categories, "Personal Protective Equipment")
    
    # Define equipment and supplies
    equipment_list = [
        # Diagnostic Equipment
        {"name": "Stethoscope", "category": diagnostic_cat, "is_disposable": False, "price_range": (20, 150)},
        {"name": "Digital Thermometer", "category": diagnostic_cat, "is_disposable": False, "price_range": (10, 50)},
        {"name": "Otoscope", "category": diagnostic_cat, "is_disposable": False, "price_range": (100, 300)},
        {"name": "Ophthalmoscope", "category": diagnostic_cat, "is_disposable": False, "price_range": (150, 400)},
        {"name": "Blood Pressure Monitor", "category": diagnostic_cat, "is_disposable": False, "price_range": (30, 200)},
        {"name": "Pulse Oximeter", "category": diagnostic_cat, "is_disposable": False, "price_range": (20, 100)},
        {"name": "Glucose Meter", "category": diagnostic_cat, "is_disposable": False, "price_range": (25, 80)},
        {"name": "Digital Scale", "category": diagnostic_cat, "is_disposable": False, "price_range": (50, 200)},
        {"name": "Height Measuring Stand", "category": diagnostic_cat, "is_disposable": False, "price_range": (40, 150)},
        {"name": "Reflex Hammer", "category": diagnostic_cat, "is_disposable": False, "price_range": (5, 30)},
        
        # Monitoring Equipment
        {"name": "ECG Machine", "category": monitoring_cat, "is_disposable": False, "price_range": (1000, 5000)},
        {"name": "Patient Monitor", "category": monitoring_cat, "is_disposable": False, "price_range": (1500, 4000)},
        {"name": "Fetal Doppler", "category": monitoring_cat, "is_disposable": False, "price_range": (300, 800)},
        {"name": "Holter Monitor", "category": monitoring_cat, "is_disposable": False, "price_range": (1000, 2500)},
        {"name": "Vital Signs Monitor", "category": monitoring_cat, "is_disposable": False, "price_range": (800, 2000)},
        
        # Surgical Instruments
        {"name": "Surgical Scissors", "category": surgical_cat, "is_disposable": False, "price_range": (15, 100)},
        {"name": "Forceps", "category": surgical_cat, "is_disposable": False, "price_range": (10, 80)},
        {"name": "Scalpel Handle", "category": surgical_cat, "is_disposable": False, "price_range": (15, 60)},
        {"name": "Needle Holder", "category": surgical_cat, "is_disposable": False, "price_range": (20, 90)},
        {"name": "Retractor", "category": surgical_cat, "is_disposable": False, "price_range": (30, 150)},
        {"name": "Surgical Clamp", "category": surgical_cat, "is_disposable": False, "price_range": (25, 120)},
        {"name": "Sterilization Tray", "category": surgical_cat, "is_disposable": False, "price_range": (100, 300)},
        {"name": "Surgical Blade", "category": surgical_cat, "is_disposable": True, "price_range": (1, 5)},
        {"name": "Suture Kit", "category": surgical_cat, "is_disposable": True, "price_range": (10, 30)},
        {"name": "Surgical Gloves", "category": surgical_cat, "is_disposable": True, "price_range": (0.5, 2)},
        
        # Medical Supplies
        {"name": "Syringe 1ml", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.2, 0.8)},
        {"name": "Syringe 5ml", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.3, 1.0)},
        {"name": "Syringe 10ml", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.4, 1.2)},
        {"name": "Syringe 20ml", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.5, 1.5)},
        {"name": "IV Catheter 18G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (1, 3)},
        {"name": "IV Catheter 20G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (1, 3)},
        {"name": "IV Catheter 22G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (1, 3)},
        {"name": "IV Catheter 24G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (1, 3)},
        {"name": "IV Administration Set", "category": medical_supplies_cat, "is_disposable": True, "price_range": (2, 6)},
        {"name": "Blood Collection Tube", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.3, 1)},
        {"name": "Needle 18G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Needle 21G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Needle 23G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Needle 25G", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Insulin Syringe", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.3, 1)},
        {"name": "Urine Container", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.5, 1.5)},
        {"name": "Specimen Container", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.5, 1.5)},
        {"name": "Tongue Depressor", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.1, 0.3)},
        {"name": "Medical Tape", "category": medical_supplies_cat, "is_disposable": True, "price_range": (1, 5)},
        {"name": "Gauze Pad", "category": medical_supplies_cat, "is_disposable": True, "price_range": (0.2, 0.8)},
        
        # Respiratory Equipment
        {"name": "Oxygen Mask Adult", "category": respiratory_cat, "is_disposable": True, "price_range": (2, 8)},
        {"name": "Oxygen Mask Pediatric", "category": respiratory_cat, "is_disposable": True, "price_range": (2, 8)},
        {"name": "Nasal Cannula", "category": respiratory_cat, "is_disposable": True, "price_range": (1, 5)},
        {"name": "Nebulizer Machine", "category": respiratory_cat, "is_disposable": False, "price_range": (50, 200)},
        {"name": "Nebulizer Kit", "category": respiratory_cat, "is_disposable": True, "price_range": (5, 15)},
        {"name": "Peak Flow Meter", "category": respiratory_cat, "is_disposable": False, "price_range": (20, 60)},
        {"name": "Spirometer", "category": respiratory_cat, "is_disposable": False, "price_range": (500, 2000)},
        {"name": "Oxygen Concentrator", "category": respiratory_cat, "is_disposable": False, "price_range": (700, 2500)},
        {"name": "Ambu Bag Adult", "category": respiratory_cat, "is_disposable": False, "price_range": (30, 100)},
        {"name": "Ambu Bag Pediatric", "category": respiratory_cat, "is_disposable": False, "price_range": (30, 100)},
        
        # First Aid Supplies
        {"name": "Adhesive Bandage", "category": first_aid_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Elastic Bandage", "category": first_aid_cat, "is_disposable": True, "price_range": (1, 5)},
        {"name": "First Aid Kit", "category": first_aid_cat, "is_disposable": False, "price_range": (20, 100)},
        {"name": "Cold Pack", "category": first_aid_cat, "is_disposable": False, "price_range": (2, 8)},
        {"name": "Hot Pack", "category": first_aid_cat, "is_disposable": False, "price_range": (2, 8)},
        {"name": "Triangular Bandage", "category": first_aid_cat, "is_disposable": True, "price_range": (1, 4)},
        {"name": "Emergency Blanket", "category": first_aid_cat, "is_disposable": True, "price_range": (2, 6)},
        {"name": "Burn Gel", "category": first_aid_cat, "is_disposable": True, "price_range": (5, 15)},
        {"name": "Antiseptic Wipes", "category": first_aid_cat, "is_disposable": True, "price_range": (0.2, 0.8)},
        {"name": "Tweezers", "category": first_aid_cat, "is_disposable": False, "price_range": (3, 10)},
        
        # PPE
        {"name": "Surgical Mask", "category": ppe_cat, "is_disposable": True, "price_range": (0.2, 1)},
        {"name": "N95 Respirator", "category": ppe_cat, "is_disposable": True, "price_range": (1, 5)},
        {"name": "Face Shield", "category": ppe_cat, "is_disposable": True, "price_range": (2, 8)},
        {"name": "Disposable Gown", "category": ppe_cat, "is_disposable": True, "price_range": (2, 10)},
        {"name": "Disposable Cap", "category": ppe_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Shoe Cover", "category": ppe_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Safety Goggles", "category": ppe_cat, "is_disposable": False, "price_range": (5, 20)},
        {"name": "Latex Gloves", "category": ppe_cat, "is_disposable": True, "price_range": (0.1, 0.5)},
        {"name": "Nitrile Gloves", "category": ppe_cat, "is_disposable": True, "price_range": (0.2, 0.8)},
        {"name": "Vinyl Gloves", "category": ppe_cat, "is_disposable": True, "price_range": (0.1, 0.4)}
    ]
    
    # Create inventory items
    created_count = 0
    for item_data in equipment_list:
        # Generate random prices based on price range
        min_price, max_price = item_data["price_range"]
        purchase_price = random_price(min_price, max_price)
        
        # For disposable items, stock more quantity
        if item_data["is_disposable"]:
            stock_qty = random.randint(100, 1000)
            reorder_level = max(20, int(stock_qty * 0.2))  # 20% of stock
        else:
            stock_qty = random.randint(5, 50)
            reorder_level = max(2, int(stock_qty * 0.3))  # 30% of stock
        
        try:
            # Create a unique item code
            item_code = f"{item_data['category'].type}-{created_count + 1:04d}"
            
            item, created = InventoryItem.objects.get_or_create(
                name=item_data["name"],
                item_code=item_code,
                defaults={
                    "description": f"{item_data['name']} for medical use",
                    "category": item_data["category"],
                    "supplier": get_random_supplier(suppliers),
                    "purchase_price": purchase_price,
                    "stock_quantity": stock_qty,
                    "reorder_level": reorder_level,
                    "is_disposable": item_data["is_disposable"],
                    "is_active": True
                }
            )
            
            # Add maintenance dates for non-disposable items if applicable
            if created and not item_data["is_disposable"] and random.choice([True, False]):
                item.last_maintenance = (datetime.now() - timedelta(days=random.randint(30, 180))).date()
                item.next_maintenance = (datetime.now() + timedelta(days=random.randint(30, 180))).date()
                item.warranty_expiry = (datetime.now() + timedelta(days=random.randint(365, 1095))).date()  # 1-3 years
                item.save()
            
            if created:
                created_count += 1
                if created_count % 20 == 0:
                    print(f"Created {created_count} equipment/supplies...")
        except Exception as e:
            print(f"Error creating equipment {item_data['name']}: {str(e)}")
    
    print(f"Total equipment and supplies created: {created_count}")

# Main function to execute the import
def main():
    categories = create_categories()
    suppliers = create_suppliers()
    
    create_medicines(categories, suppliers)
    create_equipment(categories, suppliers)
    
    # Count total items
    medicine_count = MedicineItem.objects.count()
    equipment_count = InventoryItem.objects.count()
    total_count = medicine_count + equipment_count
    
    print("\nImport Summary:")
    print(f"Total Categories: {Category.objects.count()}")
    print(f"Total Suppliers: {Supplier.objects.count()}")
    print(f"Total Medicines: {medicine_count}")
    print(f"Total Equipment & Supplies: {equipment_count}")
    print(f"Total Inventory Items: {total_count}")
    print("\nImport completed successfully!")

if __name__ == "__main__":
    main() 