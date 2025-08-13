from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator
from patient.models import Patient
import uuid


class Service(models.Model):
    """Model for hospital services that can be billed"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'services'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (${self.cost})"


class BedType(models.Model):
    """Model for different types of hospital beds with rates"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'bed_types'
        ordering = ['daily_rate']
    
    def __str__(self):
        return f"{self.name} (${self.daily_rate}/day)"


class Bill(models.Model):
    """Main billing model to track patient invoices"""
    # Payment Status
    PENDING = 'PENDING'
    PARTIALLY_PAID = 'PARTIALLY_PAID'
    PAID = 'PAID'
    CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PARTIALLY_PAID, 'Partially Paid'),
        (PAID, 'Paid'),
        (CANCELLED, 'Cancelled'),
    ]
    
    # Payment Methods
    CASH = 'CASH'
    CARD = 'CARD'
    BANK_TRANSFER = 'BANK_TRANSFER'
    INSURANCE = 'INSURANCE'
    MOBILE_PAYMENT = 'MOBILE_PAYMENT'
    
    PAYMENT_METHOD_CHOICES = [
        (CASH, 'Cash'),
        (CARD, 'Credit/Debit Card'),
        (BANK_TRANSFER, 'Bank Transfer'),
        (INSURANCE, 'Insurance'),
        (MOBILE_PAYMENT, 'Mobile Payment'),
    ]
    
    # Basic Information
    bill_number = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='bills')
    
    # Dates
    bill_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)
    
    # Financial Information
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Insurance Details
    insurance_claimed = models.BooleanField(default=False)
    insurance_coverage_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    insurance_company = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, help_text="Reference number for card/bank/mobile payments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    # Additional Information
    notes = models.TextField(blank=True)
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_bills')
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bills'
        ordering = ['-bill_date', '-created_at']
    
    def __str__(self):
        return f"Bill #{self.bill_number} - {self.patient.full_name} - ${self.total_amount}"
    
    def save(self, *args, **kwargs):
        # Generate a unique bill number if this is a new bill
        if not self.bill_number:
            year = timezone.now().year
            month = timezone.now().month
            # Get count of bills and add 1
            count = Bill.objects.count() + 1
            # Format: BL-YEAR-MONTH-COUNT (e.g., BL-2023-04-0001)
            self.bill_number = f"BL-{year}-{month:02d}-{count:04d}"
        
        # Set the status based on payments
        if self.paid_amount == 0:
            self.status = self.PENDING
        elif self.paid_amount < self.total_amount - self.discount - self.insurance_coverage_amount:
            self.status = self.PARTIALLY_PAID
        elif self.paid_amount >= self.total_amount - self.discount - self.insurance_coverage_amount:
            self.status = self.PAID
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('bill_detail', args=[str(self.id)])
    
    @property
    def balance_due(self):
        """Calculate remaining balance due"""
        return max(0, self.total_amount - self.discount - self.paid_amount - self.insurance_coverage_amount)
    
    @property
    def is_fully_paid(self):
        """Check if bill is fully paid"""
        return self.balance_due <= 0


class BillItem(models.Model):
    """Individual line items for a bill"""
    # Item Types
    CONSULTANCY = 'CONSULTANCY'
    SERVICE = 'SERVICE'
    MEDICINE = 'MEDICINE'
    ROOM_CHARGE = 'ROOM_CHARGE'
    EQUIPMENT = 'EQUIPMENT'
    LAB_TEST = 'LAB_TEST'
    OTHER = 'OTHER'
    
    ITEM_TYPE_CHOICES = [
        (CONSULTANCY, 'Doctor Consultancy'),
        (SERVICE, 'Medical Service'),
        (MEDICINE, 'Medication'),
        (ROOM_CHARGE, 'Room/Bed Charges'),
        (EQUIPMENT, 'Medical Equipment'),
        (LAB_TEST, 'Laboratory Test'),
        (OTHER, 'Other Charges'),
    ]
    
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    
    # Quantity and Pricing
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Reference to service if applicable
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    
    # For room charges
    days = models.PositiveIntegerField(default=1, help_text="Number of days for room charges")
    bed_type = models.ForeignKey(BedType, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking
    date_added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bill_items'
    
    def __str__(self):
        return f"{self.description} - {self.quantity} x ${self.unit_price}"
    
    def save(self, *args, **kwargs):
        # Calculate total price if not manually set
        if not self.total_price or self.total_price == 0:
            self.total_price = self.quantity * self.unit_price
        
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Model to track payments made against a bill"""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_date = models.DateTimeField(default=timezone.now)
    
    # Payment method details
    payment_method = models.CharField(max_length=20, choices=Bill.PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Reference number for card/bank/mobile payments")
    
    # Card payment details (if applicable)
    card_last_digits = models.CharField(max_length=4, blank=True)
    
    # Insurance payment details (if applicable)
    is_insurance_payment = models.BooleanField(default=False)
    insurance_company = models.CharField(max_length=100, blank=True)
    insurance_approval_code = models.CharField(max_length=50, blank=True)
    
    # Receipt
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Tracking
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment of ${self.amount} for Bill #{self.bill.bill_number}"
    
    def save(self, *args, **kwargs):
        # Generate unique receipt number
        if not self.receipt_number:
            year = timezone.now().year
            month = timezone.now().month
            # Get count of payments and add 1
            count = Payment.objects.count() + 1
            # Format: RCP-YEAR-MONTH-COUNT (e.g., RCP-2023-04-0001)
            self.receipt_number = f"RCP-{year}-{month:02d}-{count:04d}"
        
        # Update the bill's paid amount
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            if self.is_insurance_payment:
                self.bill.insurance_claimed = True
                self.bill.insurance_coverage_amount += self.amount
            else:
                self.bill.paid_amount += self.amount
            
            self.bill.save() 