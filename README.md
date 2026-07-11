# Hospital Management System (HMS) - SmartCare

A modular **Django 4.2** Hospital Management System for a multi-specialty
hospital. It manages patients, appointments, admissions & beds, an in-house
pharmacy (drug requests + retail sales), hospital inventory, staff with
role-based access, and a public website with a blog and inquiry system.

---

## Features

- **Role-based access** for 5 roles - Admin, Doctor, Nurse, Receptionist,
  Pharmacist - plus a **Head Nurse** privilege (a nurse who can manage the
  hospital inventory).
- **Patients & medical records** - registration, structured prescriptions,
  PDF reports.
- **Appointments** - booking, doctor availability, leave requests & approval.
- **Admissions** - 6-floor / department layout, rooms & beds, admission
  requests and discharge, emergency admissions.
- **In-house pharmacy**
  - **Nurse -> Pharmacy drug requests**: nurses request medicine, pharmacy
    approves/rejects and dispenses (internal stock movement).
  - **Retail sales & billing**: walk-in sales generate an invoice + printable
    receipt with cash/card/insurance/mobile payment.
- **Hospital inventory** (equipment / surgical / consumables) - managed by the
  Head Nurse, view-only for other nurses.
- **Admin analytics dashboard** - hospital-wide KPIs, bed occupancy by floor,
  revenue, low stock, and more.
- **Public website** - landing pages, doctor blogs, contact & appointment
  inquiries with email replies.

---

## Tech Stack

- **Backend:** Django 4.2 (Python)
- **Database:** SQLite
- **Frontend:** Django Templates, Bootstrap 5, crispy-forms
- **Auth:** Django auth with a custom `users.User` model + role middleware
- **PDF:** xhtml2pdf · **Email/OTP:** SMTP + IMAP (Gmail)

---

## Project Structure

```
hospital-management-system/
├── core/            # Shared constants, decorators, mixins, utils
├── users/           # Auth, roles, profiles, admin analytics
├── patient/         # Patients, records, rooms/beds, admissions
├── appointment/     # Appointments, availability, leave, dashboards
├── pharmacy/        # Medicines, sales, drug requests, hospital inventory
├── billing/         # Billing models (patient billing - light)
├── website/         # Public site, blog, inquiries
├── hms_project/     # Project config
│   └── settings/    # base.py / dev.py / prod.py (env-selected)
├── templates/       # Shared HTML templates
├── static/          # CSS, JS, fonts
├── setup/           # Data-seeding & maintenance scripts (see setup/README.md)
├── docs/            # Feature docs (e.g. DRUG_REQUESTS.md)
├── manage.py
└── requirements.txt
```

Each app is organized modularly: `views/` and `forms/` are **packages split by
feature**, with business logic in `services.py` and read queries in
`selectors.py`.

---

## Installation & Setup

### 1. Clone & create a virtual environment
```bash
git clone <repo-url>
cd hospital-management-system
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root (it is git-ignored):
```
# Email (Gmail address + app password) - required for OTP & inquiry emails
EMAIL_HOST=your.address@gmail.com
EMAIL_APP_PASSKEY=your-gmail-app-password

# Optional
SECRET_KEY=change-me-in-production
DJANGO_ENV=dev            # 'dev' (default) or 'prod'
```

### 4. Apply migrations
```bash
python manage.py migrate
```

### 5. (Optional) Seed demo data
Utility scripts live in `setup/` - run from the project root:
```bash
python setup/data_import.py
```
See **`setup/README.md`** for all available scripts.

### 6. Create an admin user
```bash
python manage.py createsuperuser
```
(Then set that user's role to Admin in the Django admin, or use the
`create_default_users` / `setup_hospital` management commands.)

### 7. Run the server
```bash
python manage.py runserver
```
Open http://127.0.0.1:8000/  ·  Admin panel: http://127.0.0.1:8000/admin/

---

## Environments

Settings are split into `hms_project/settings/{base,dev,prod}.py` and selected
by the `DJANGO_ENV` variable (`dev` by default). `dev` enables DEBUG and local
hosts; `prod` disables DEBUG, sets allowed hosts, and enables security cookies.

---

## Roles & Access

| Role | Can do |
|------|--------|
| **Admin** | Full access to everything, incl. the analytics dashboard |
| **Doctor** | Appointments, patients, medical records, admissions, leave, blogs |
| **Nurse** | Assigned patients, admissions, drug requests, view inventory & medicines |
| **Head Nurse** | Everything a nurse can, **plus** manage the hospital inventory |
| **Receptionist** | Register patients, book appointments, handle inquiries |
| **Pharmacist** | Medicines, purchases, sales/billing, dispense drug requests |

Access is enforced by `users.middleware.RoleBasedAccessMiddleware` plus
per-view role decorators in `core.decorators`.

---

## Key Workflows

- **Nurse <-> Pharmacy drug requests** - a nurse requests medicine for a
  patient; the pharmacy approves/rejects and dispenses, which deducts pharmacy
  stock. Full docs in `docs/DRUG_REQUESTS.md`.
- **Pharmacy retail sale** - `Pharmacy -> Sales -> Add Sale` creates a `Sale`
  (invoice), deducts stock, and produces a printable receipt.
- **Hospital inventory** - `Hospital Inventory` in the nurse menu; the Head
  Nurse sees Add/Edit, other nurses get view + search only.
- **Admin analytics** - the Admin dashboard shows live hospital-wide metrics.

---

## Management Commands

- `python manage.py create_default_users` - create default staff accounts
- `python manage.py setup_hospital` - set up floors, rooms and beds
- `python manage.py setup_nurse_assignments` - assign nurses to floors
- `python manage.py setup_test_data` - populate test data
- `python manage.py check_email_replies` - poll inbound email replies

---

## Setup / Maintenance Scripts

Standalone data-seeding and maintenance utilities live in **`setup/`**
(run from the project root, e.g. `python setup/data_import.py`). See
`setup/README.md` for the full list.

---

## License

Intended for **educational and learning purposes**.

## Author

**Raj Patel** - https://github.com/R204570
