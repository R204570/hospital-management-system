"""Views package for the pharmacy app (split by feature).

Every view is re-exported so ``from . import views`` and
``pharmacy.views.<name>`` keep working unchanged.
"""
from .dashboard import (
    pharmacy_dashboard,
)
from .medicines import (
    medicine_list,
    medicine_detail,
    add_medicine,
    edit_medicine,
    medicine_search_api,
    low_stock_list,
    expired_medicines,
)
from .suppliers import (
    supplier_list,
    add_supplier,
    edit_supplier,
)
from .purchases import (
    purchase_list,
    add_purchase,
    purchase_detail,
    receive_purchase,
    cancel_purchase,
)
from .sales import (
    sale_list,
    add_sale,
    sale_detail,
)
from .prescriptions import (
    prescription_list,
)
from .inventory import (
    inventory_list,
    inventory_add,
    inventory_edit,
)
from .drug_requests import (
    drug_request_create,
    nurse_drug_request_list,
    drug_request_cancel,
    drug_request_queue,
    drug_request_detail,
    drug_request_respond,
    drug_request_dispense,
    drug_request_notifications,
)

__all__ = [
    "pharmacy_dashboard",
    "medicine_list",
    "medicine_detail",
    "add_medicine",
    "edit_medicine",
    "medicine_search_api",
    "low_stock_list",
    "expired_medicines",
    "supplier_list",
    "add_supplier",
    "edit_supplier",
    "purchase_list",
    "add_purchase",
    "purchase_detail",
    "receive_purchase",
    "cancel_purchase",
    "sale_list",
    "add_sale",
    "sale_detail",
    "prescription_list",
    "drug_request_create",
    "nurse_drug_request_list",
    "drug_request_cancel",
    "drug_request_queue",
    "drug_request_detail",
    "drug_request_respond",
    "drug_request_dispense",
    "drug_request_notifications",
    "inventory_list",
    "inventory_add",
    "inventory_edit",
]
