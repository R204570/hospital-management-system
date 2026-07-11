#!/usr/bin/env python
# Ensure the project root is importable when this script is run from setup/.
import os as _hms_os, sys as _hms_sys
_hms_sys.path.insert(0, _hms_os.path.dirname(_hms_os.path.dirname(_hms_os.path.abspath(__file__))))

"""
Hospital Management System - Automatic Email Reply Checker
Schedule this script to run every 5-10 minutes to check for new email replies
"""
import os
import django
import logging
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.core.management import call_command

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_check.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

def main():
    """Main function to check for new email replies"""
    try:
        logging.info("🔍 Starting automatic email check...")
        
        # Run the check_email_replies command
        call_command('check_email_replies', limit=20, verbosity=1)
        
        logging.info("✅ Email check completed successfully")
        
    except Exception as e:
        logging.error(f"❌ Error during email check: {str(e)}")
        raise

if __name__ == "__main__":
    main() 