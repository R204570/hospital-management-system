# Nurse ↔ Pharmacy Drug Requests

In-house drug-request workflow that lets ward **nurses** request medicine from the
**pharmacy**, and lets the pharmacy approve/reject and dispense. Because the pharmacy
is an in-house store (not a separate entity), **dispensing is an internal stock
movement** — the medicine is issued out of pharmacy inventory to the ward/patient.
There is intentionally **no separate pharmacy bill/receipt** for these requests.

## Roles & access
- **Nurse** — create a request, view their own requests, cancel while pending.
- **Pharmacist** — see the request queue, approve/reject, dispense (deducts stock).
- **Admin** — full access to both sides.

Access is enforced by `users.middleware.RoleBasedAccessMiddleware` (nurse request
URLs are whitelisted) plus the `@nurse_required` / `@pharmacist_required` decorators.

## Workflow / statuses
```
PENDING ──approve──► APPROVED ──dispense──► DISPENSED
   │                    
   ├──reject──► REJECTED
   └──cancel (nurse)──► CANCELLED
```
- **Dispense** runs atomically: it checks stock, decrements
  `MedicineItem.stock_quantity` by the approved quantity, and stamps `dispensed_at`.
- Insufficient stock blocks dispensing with an error message.

## Model — `pharmacy.DrugRequest`
Key fields: `requesting_nurse`, `patient`, `medicine`, `quantity`, `urgency`
(ROUTINE/URGENT/EMERGENCY), `status`, `approved_quantity`, `responded_by`,
`response_notes`, timestamps (`created_at`, `responded_at`, `dispensed_at`).

Migrations: `pharmacy/0003_drugrequest.py`.

## Code layout
- `pharmacy/models.py` — `DrugRequest`.
- `pharmacy/services.py` — `create_drug_request`, `respond_to_drug_request`,
  `dispense_drug_request`, `cancel_drug_request` (business logic).
- `pharmacy/selectors.py` — `pharmacy_queue`, `drug_requests_for_nurse`,
  `pending_request_count` (read queries).
- `pharmacy/views/drug_requests.py` — request/queue/detail/respond/dispense views
  plus the `drug_request_notifications` polling endpoint.
- Templates: `templates/pharmacy/drug_request_form.html`,
  `nurse_drug_request_list.html`, `drug_request_queue.html`,
  `drug_request_detail.html`.

## URLs (under `/pharmacy/`)
| URL | Name | Who |
|-----|------|-----|
| `drug-requests/new/` | `drug_request_create` | Nurse |
| `drug-requests/mine/` | `nurse_drug_request_list` | Nurse |
| `drug-requests/<id>/cancel/` | `drug_request_cancel` | Nurse |
| `drug-requests/` | `drug_request_queue` | Pharmacy |
| `drug-requests/<id>/` | `drug_request_detail` | Nurse (own) / Pharmacy |
| `drug-requests/<id>/respond/` | `drug_request_respond` | Pharmacy |
| `drug-requests/<id>/dispense/` | `drug_request_dispense` | Pharmacy |
| `drug-requests/notifications/` | `drug_request_notifications` | Nurse / Pharmacy (JSON, polled) |

## Notifications
`drug_request_notifications` returns JSON — pending count + recent items — polled by
the pharmacy queue page every 15s to keep the "pending" badge current (same polling
approach used elsewhere in the app).
