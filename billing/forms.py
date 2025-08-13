from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Bill, BillItem, Payment, Service, BedType


class BillSearchForm(forms.Form):
    """Form for searching bills"""
    query = forms.CharField(
        label="Search by bill number or patient",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bill number or patient name'})
    )
    status = forms.ChoiceField(
        label="Status",
        required=False,
        choices=[('', 'All')] + list(Bill.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        label="Date From",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label="Date To",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class BillForm(forms.ModelForm):
    """Form for creating/updating bills"""
    
    class Meta:
        model = Bill
        fields = ['patient', 'bill_date', 'due_date', 'discount', 'insurance_claimed', 
                 'insurance_company', 'insurance_policy_number', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'bill_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'insurance_company': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


class BillItemForm(forms.ModelForm):
    """Form for adding items to a bill"""
    
    class Meta:
        model = BillItem
        fields = ['item_type', 'description', 'quantity', 'unit_price', 'service', 'bed_type', 'days']
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'bed_type': forms.Select(attrs={'class': 'form-select'}),
            'days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active services and bed types
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        self.fields['bed_type'].queryset = BedType.objects.filter(is_active=True)
        
        # Make fields conditionally required based on item type
        self.fields['service'].required = False
        self.fields['bed_type'].required = False
        self.fields['days'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        item_type = cleaned_data.get('item_type')
        service = cleaned_data.get('service')
        bed_type = cleaned_data.get('bed_type')
        
        # Validate based on item type
        if item_type == BillItem.SERVICE and not service:
            self.add_error('service', 'Service must be selected for service items')
        
        if item_type == BillItem.ROOM_CHARGE and not bed_type:
            self.add_error('bed_type', 'Bed type must be selected for room charge items')
        
        return cleaned_data


class PaymentForm(forms.ModelForm):
    """Form for recording payments"""
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'reference_number', 'card_last_digits',
                 'is_insurance_payment', 'insurance_company', 'insurance_approval_code', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'card_last_digits': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4'}),
            'insurance_company': forms.TextInput(attrs={'class': 'form-control'}),
            'insurance_approval_code': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop('bill', None)
        super().__init__(*args, **kwargs)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.bill and amount > self.bill.balance_due:
            raise ValidationError(f"Payment amount cannot exceed the balance due ({self.bill.balance_due})")
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        is_insurance_payment = cleaned_data.get('is_insurance_payment')
        reference_number = cleaned_data.get('reference_number')
        card_last_digits = cleaned_data.get('card_last_digits')
        
        # Validate payment method specific fields
        if payment_method == Bill.CARD and not card_last_digits:
            self.add_error('card_last_digits', 'Last 4 digits are required for card payments')
        
        if payment_method in [Bill.CARD, Bill.BANK_TRANSFER, Bill.MOBILE_PAYMENT] and not reference_number:
            self.add_error('reference_number', f'Reference number is required for {dict(Bill.PAYMENT_METHOD_CHOICES)[payment_method]} payments')
        
        if is_insurance_payment:
            insurance_company = cleaned_data.get('insurance_company')
            insurance_approval_code = cleaned_data.get('insurance_approval_code')
            
            if not insurance_company:
                self.add_error('insurance_company', 'Insurance company is required for insurance payments')
            
            if not insurance_approval_code:
                self.add_error('insurance_approval_code', 'Approval code is required for insurance payments')
        
        return cleaned_data


class ServiceForm(forms.ModelForm):
    """Form for managing services"""
    
    class Meta:
        model = Service
        fields = ['name', 'description', 'cost', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BedTypeForm(forms.ModelForm):
    """Form for managing bed types"""
    
    class Meta:
        model = BedType
        fields = ['name', 'description', 'daily_rate', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 