# Hospital Management System (HMS)

A comprehensive Hospital Management System built with Django and MongoDB using Server-Side Rendering (SSR).

## Features

- **Role-Based Access Control**: Different interfaces for Doctors, Nurses, Receptionists, Pharmacy staff, and Administrators
- **Patient Management**: Register, update, and track patient information
- **Appointment System**: Book, reschedule, and manage patient appointments 
- **Medical Records**: Create and maintain digital medical records
- **Billing & Payments**: Generate invoices, track payments, and handle insurance claims
- **Pharmacy & Inventory**: Manage medications and medical supplies
- **Bed Management**: Track and assign hospital beds
- **Reporting**: Generate PDF reports and analytics

## Technology Stack

- **Backend Framework**: Django 4.2.9
- **Database**: MongoDB (via djongo)
- **Frontend**: Server-Side Rendering with Django Templates
- **Real-time Chat**: Django Channels with WebSockets
- **PDF Generation**: xhtml2pdf
- **Styling**: Bootstrap 5

## Installation

### Prerequisites

- Python 3.8+
- MongoDB 5.0+
- Git

### Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/hms.git
   cd hms
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start MongoDB:
   ```
   # Make sure MongoDB is running on your system
   # Default connection is localhost:27017
   ```

5. Run migrations to initialize the database:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```
   python manage.py runserver
   ```

8. Access the application:
   - Admin Panel: http://127.0.0.1:8000/admin/
   - Main Application: http://127.0.0.1:8000/

## Project Structure

- **hms_project/** - Project settings and configurations
- **users/** - User authentication and role-based access
- **patient/** - Patient registration and medical records
- **appointment/** - Appointment scheduling and management
- **billing/** - Invoicing, payments, and financial records
- **pharmacy/** - Medication inventory and dispensing
- **nursing/** - Nursing station and bed management
- **chat/** - Real-time communication between staff

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django community
- MongoDB and Djongo documentation
- Bootstrap team for the UI components 