from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    
    # Medicine management
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.add_medicine, name='add_medicine'),
    path('medicines/<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('medicines/<int:pk>/edit/', views.edit_medicine, name='edit_medicine'),
    path('medicines/search/', views.medicine_search_api, name='medicine_search_api'),
    
    # Supplier management
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/<int:pk>/edit/', views.edit_supplier, name='edit_supplier'),
    
    # Purchase management
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.add_purchase, name='add_purchase'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/receive/', views.receive_purchase, name='receive_purchase'),
    path('purchases/<int:pk>/cancel/', views.cancel_purchase, name='cancel_purchase'),
    
    # Sales management
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/add/', views.add_sale, name='add_sale'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    
    # Prescription management
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    
    # Inventory management
    path('low-stock/', views.low_stock_list, name='low_stock_list'),
    path('expired-medicines/', views.expired_medicines, name='expired_medicines'),

    # Hospital inventory (equipment/surgical/consumables) - Head Nurse managed
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_add, name='inventory_add'),
    path('inventory/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),

    # Drug request workflow (Nurse <-> Pharmacy)
    path('drug-requests/', views.drug_request_queue, name='drug_request_queue'),
    path('drug-requests/new/', views.drug_request_create, name='drug_request_create'),
    path('drug-requests/new/<int:patient_id>/', views.drug_request_create, name='drug_request_create_for_patient'),
    path('drug-requests/mine/', views.nurse_drug_request_list, name='nurse_drug_request_list'),
    path('drug-requests/notifications/', views.drug_request_notifications, name='drug_request_notifications'),
    path('drug-requests/<int:pk>/', views.drug_request_detail, name='drug_request_detail'),
    path('drug-requests/<int:pk>/respond/', views.drug_request_respond, name='drug_request_respond'),
    path('drug-requests/<int:pk>/dispense/', views.drug_request_dispense, name='drug_request_dispense'),
    path('drug-requests/<int:pk>/cancel/', views.drug_request_cancel, name='drug_request_cancel'),
] 