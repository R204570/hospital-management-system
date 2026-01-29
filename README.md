# 🏥 Hospital Management System (HMS)

A **Django-based Hospital Management System** that manages core hospital operations such as **patients, appointments, billing, pharmacy, users, and website pages**.  
The project also includes **utility scripts to populate and normalize database data**, making initial setup and testing easier.

This repository demonstrates a **real-world modular Django project structure** with setup helpers and data seeding support.

---

## 🚀 Features

- 🔐 User authentication and role-based access
- 🧑‍⚕️ Patient management
- 📅 Appointment scheduling
- 💳 Billing and invoice records
- 💊 Pharmacy and medicine inventory
- 🌐 Website pages (landing, login, dashboard)
- 📦 Database population & normalization scripts
- 🎨 Static assets and reusable templates

---

## 🛠️ Tech Stack

- **Backend:** Django (Python)
- **Database:** SQLite (default)
- **Frontend:** HTML, CSS, JavaScript, Django Templates
- **Authentication:** Django Auth System

---

## 📁 Project Structure

```
hospital-management-system/
│
├── appointment/              # Appointment management
├── billing/                  # Billing and invoices
├── patient/                  # Patient records
├── pharmacy/                 # Pharmacy & medicines
├── users/                    # Authentication & roles
├── website/                  # Public website pages
│
├── scripts/                  # Database setup & utility scripts
│   ├── populate_medicines.py
│   ├── normalize_medicines.py
│   └── data_setup_helpers.py
│
├── static/                   # CSS, JS, images
├── templates/                # Shared HTML templates
│
├── manage.py
├── requirements.txt
└── db.sqlite3
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip

---

### 1️⃣ Clone the Repository

```
git clone https://github.com/R204570/hospital-management-system.git
cd hospital-management-system
```

---

### 2️⃣ Create & Activate Virtual Environment

```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS
```

---

### 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

### 4️⃣ Apply Migrations

```
python manage.py makemigrations
python manage.py migrate
```

---

### 5️⃣ Populate Initial Database Data (IMPORTANT)

The project includes scripts to **populate and normalize pharmacy and system data**.

Run them **after migrations**:

```
python manage.py shell
```

Inside shell:
```python
exec(open("scripts/populate_medicines.py").read())
exec(open("scripts/normalize_medicines.py").read())
```

These scripts:
- Insert initial medicine data
- Standardize medicine naming & dosages
- Prepare pharmacy inventory for use

---

### 6️⃣ Create Superuser

```
python manage.py createsuperuser
```

---

### 7️⃣ Run Development Server

```
python manage.py runserver
```

Open:
```
http://127.0.0.1:8000/
```

---

## 🔑 Admin Panel

Access Django admin panel:
```
http://127.0.0.1:8000/admin/
```

Admin can:
- Manage users & roles
- Control patients, appointments, billing
- Edit pharmacy inventory

---

## 🧠 System Workflow Overview

- Patients are registered and managed
- Appointments are created and tracked
- Billing is associated with patient visits
- Pharmacy inventory is preloaded using scripts
- Admin has full control over all modules

---

## 🧪 Utility Scripts Overview

| Script | Purpose |
|------|--------|
| populate_medicines.py | Inserts initial medicine records |
| normalize_medicines.py | Cleans & standardizes medicine data |
| data_setup_helpers.py | Common setup utilities |

These scripts are intended to **speed up development and testing**.

---

## 🚧 Future Enhancements

- REST API support
- Doctor scheduling module
- Email & OTP notifications
- Payment gateway integration
- Analytics dashboard
- PostgreSQL / MySQL support

---

## 🤝 Contributing

1. Fork the repository  
2. Create a feature branch  
3. Commit your changes  
4. Push to your fork  
5. Open a Pull Request  

---

## 📄 License

This project is intended for **educational and learning purposes**.

---

## 👨‍💻 Author

**Raj Patel**  
GitHub: https://github.com/R204570
