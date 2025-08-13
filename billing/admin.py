from django.contrib import admin
from .models import Service, BedType, Bill, BillItem, Payment


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(BedType)
class BedTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'daily_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1
    fields = ('item_type', 'description', 'quantity', 'unit_price', 'total_price', 'service', 'bed_type', 'days')
    raw_id_fields = ('service', 'bed_type')


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ('amount', 'payment_date', 'payment_method', 'reference_number', 'is_insurance_payment', 'receipt_number')
    readonly_fields = ('receipt_number',)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'patient', 'bill_date', 'total_amount', 'paid_amount', 'balance_due', 'status')
    list_filter = ('status', 'bill_date', 'insurance_claimed')
    search_fields = ('bill_number', 'patient__first_name', 'patient__last_name', 'patient__patient_id')
    readonly_fields = ('bill_number', 'created_at', 'last_updated', 'balance_due')
    raw_id_fields = ('patient', 'created_by')
    date_hierarchy = 'bill_date'
    inlines = [BillItemInline, PaymentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('bill_number', 'patient', 'bill_date', 'due_date')
        }),
        ('Financial Information', {
            'fields': ('total_amount', 'discount', 'paid_amount', 'status')
        }),
        ('Insurance Details', {
            'fields': ('insurance_claimed', 'insurance_coverage_amount', 'insurance_company', 'insurance_policy_number')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by', 'created_at', 'last_updated')
        }),
    )
    
    def balance_due(self, obj):
        return obj.balance_due
    balance_due.short_description = 'Balance Due'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'bill', 'amount', 'payment_date', 'payment_method', 'is_insurance_payment')
    list_filter = ('payment_method', 'is_insurance_payment', 'payment_date')
    search_fields = ('receipt_number', 'bill__bill_number', 'reference_number')
    readonly_fields = ('receipt_number', 'created_at')
    raw_id_fields = ('bill', 'recorded_by')
    date_hierarchy = 'payment_date' 