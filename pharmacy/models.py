from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.translation import gettext_lazy as _
from users.models import User
from patient.models import Patient

class Category(models.Model):
    """Category model for classifying inventory items"""
    MEDICINE = 'MED'
    EQUIPMENT = 'EQP'
    SURGICAL = 'SUR'
    CONSUMABLE = 'CON'
    CATEGORY_CHOICES = [
        (MEDICINE, 'Medicine'),
        (EQUIPMENT, 'Equipment'),
        (SURGICAL, 'Surgical Instrument'),
        (CONSUMABLE, 'Consumable'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=3, choices=CATEGORY_CHOICES, default=MEDICINE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    """Supplier model for inventory items"""
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    representative = models.CharField(max_length=100, blank=True, null=True, help_text="Company representative through which the medicine is supplied")
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
    
    def __str__(self):
        if self.country:
            return f"{self.name} ({self.country})"
        return self.name

class MedicineItem(models.Model):
    """Medicine inventory item model"""
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='medicines')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='medicines')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    dosage_form = models.CharField(max_length=50, blank=True, null=True)  # e.g., tablet, capsule, liquid
    strength = models.CharField(max_length=50, blank=True, null=True)  # e.g., 500mg, 50ml
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    requires_prescription = models.BooleanField(default=False)
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level
    
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date <= timezone.now().date()
        return False

class InventoryItem(models.Model):
    """Non-medicine inventory item model (equipment, surgical instruments, consumables)"""
    name = models.CharField(max_length=200)
    item_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='inventory_items')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='inventory_items')
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    last_maintenance = models.DateField(blank=True, null=True)
    next_maintenance = models.DateField(blank=True, null=True)
    warranty_expiry = models.DateField(blank=True, null=True)
    is_disposable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_level
    
    def needs_maintenance(self):
        if self.next_maintenance:
            return self.next_maintenance <= timezone.now().date()
        return False

class Purchase(models.Model):
    """Purchase model for tracking inventory purchases"""
    PENDING = 'PENDING'
    RECEIVED = 'RECEIVED'
    CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (RECEIVED, 'Received'),
        (CANCELLED, 'Cancelled'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    purchase_date = models.DateField()
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, default='Unpaid')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchases')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-purchase_date"]
    
    def __str__(self):
        return f"PO-{self.id} - {self.supplier.name} - {self.purchase_date}"
    
    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)
            self.invoice_number = f"PO-{self.id:06d}"
            return self.save()
        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        total = self.items.aggregate(
            total=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
        )['total'] or 0
        return total

class PurchaseItem(models.Model):
    """Items included in a purchase"""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(MedicineItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    received_quantity = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["id"]
    
    def __str__(self):
        if self.medicine:
            return f"{self.medicine.name} - {self.quantity}"
        elif self.inventory_item:
            return f"{self.inventory_item.name} - {self.quantity}"
        return f"Item #{self.id}"
    
    def total_price(self):
        return self.quantity * self.unit_price
    
    def clean(self):
        if not self.medicine and not self.inventory_item:
            raise ValueError("Either medicine or inventory item must be selected")
        if self.medicine and self.inventory_item:
            raise ValueError("Only one of medicine or inventory item should be selected")

class Sale(models.Model):
    """Sale model for tracking pharmacy sales"""
    CASH = 'CASH'
    CARD = 'CARD'
    INSURANCE = 'INSURANCE'
    MOBILE_PAYMENT = 'MOBILE'
    PAYMENT_CHOICES = [
        (CASH, 'Cash'),
        (CARD, 'Card'),
        (INSURANCE, 'Insurance'),
        (MOBILE_PAYMENT, 'Mobile Payment'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    sale_date = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default=CASH)
    payment_status = models.CharField(max_length=20, default='Paid')
    points_earned = models.PositiveIntegerField(default=0)
    points_redeemed = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-sale_date"]
    
    def __str__(self):
        return f"INV-{self.invoice_number} - {self.sale_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        if not self.id:
            super().save(*args, **kwargs)
            self.invoice_number = f"INV-{self.id:06d}"
        
        # Calculate totals
        self.subtotal = self.calculate_subtotal()
        self.total = self.subtotal - self.discount + self.tax
        
        # Calculate loyalty points (1 point per 10 currency units spent)
        if self.patient and not self.points_earned:
            self.points_earned = int(self.total / 10)
        
        super().save(*args, **kwargs)
    
    def calculate_subtotal(self):
        return self.items.aggregate(
            subtotal=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
        )['subtotal'] or 0

class SaleItem(models.Model):
    """Items included in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(MedicineItem, on_delete=models.CASCADE, related_name='sale_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ["id"]
    
    def __str__(self):
        return f"{self.medicine.name} - {self.quantity}"
    
    def total_price(self):
        return (self.unit_price * self.quantity) - self.discount
    
    def save(self, *args, **kwargs):
        # Update stock quantity when a sale is made
        if not self.id:  # Only for new sale items
            self.medicine.stock_quantity = F('stock_quantity') - self.quantity
            self.medicine.save()
        super().save(*args, **kwargs)

class LoyaltyProgram(models.Model):
    """Loyalty program settings"""
    name = models.CharField(max_length=100)
    points_per_currency = models.DecimalField(max_digits=5, decimal_places=2, default=0.1)  # 0.1 means 1 point per 10 currency units
    redemption_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.01)  # 0.01 means 1 currency unit per 100 points
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Loyalty Programs"
    
    def __str__(self):
        return self.name

class PatientLoyalty(models.Model):
    """Patient loyalty points tracking"""
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='loyalty')
    points_balance = models.PositiveIntegerField(default=0)
    total_points_earned = models.PositiveIntegerField(default=0)
    total_points_redeemed = models.PositiveIntegerField(default=0)
    loyalty_tier = models.CharField(max_length=20, default='Standard')
    joined_date = models.DateField(auto_now_add=True)
    last_transaction = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Patient Loyalty"
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.points_balance} points"
    
    def add_points(self, points):
        self.points_balance += points
        self.total_points_earned += points
        self.last_transaction = timezone.now()
        self.update_tier()
        self.save()
    
    def redeem_points(self, points):
        if points <= self.points_balance:
            self.points_balance -= points
            self.total_points_redeemed += points
            self.last_transaction = timezone.now()
            self.update_tier()
            self.save()
            return True
        return False
    
    def update_tier(self):
        if self.total_points_earned >= 5000:
            self.loyalty_tier = 'Platinum'
        elif self.total_points_earned >= 2000:
            self.loyalty_tier = 'Gold'
        elif self.total_points_earned >= 500:
            self.loyalty_tier = 'Silver'
        else:
            self.loyalty_tier = 'Standard' 