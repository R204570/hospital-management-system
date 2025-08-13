"""
Debug script for profile update issues.
Run this script with: python manage.py shell < debug_profile.py
"""

from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
import os

User = get_user_model()

def check_media_permissions():
    """Check if media directory exists and has correct permissions"""
    media_root = settings.MEDIA_ROOT
    
    # Check if media directory exists
    if not os.path.exists(media_root):
        print(f"[ERROR] Media directory {media_root} does not exist")
        try:
            os.makedirs(media_root, exist_ok=True)
            print(f"[FIXED] Created media directory at {media_root}")
        except Exception as e:
            print(f"[ERROR] Failed to create media directory: {str(e)}")
    else:
        print(f"[OK] Media directory exists at {media_root}")
    
    # Check permissions
    try:
        # Try to create a test file
        test_file_path = os.path.join(media_root, 'test_write_permission.txt')
        with open(test_file_path, 'w') as f:
            f.write('Test write permission')
        
        # Clean up test file
        os.remove(test_file_path)
        print("[OK] Media directory is writable")
    except Exception as e:
        print(f"[ERROR] Media directory is not writable: {str(e)}")

def check_profile_picture_field():
    """Check if profile_picture field is correctly defined"""
    try:
        field = User._meta.get_field('profile_picture')
        print(f"[OK] Profile picture field exists: {field}")
        print(f"    Upload to: {field.upload_to}")
        print(f"    Storage: {field.storage}")
    except Exception as e:
        print(f"[ERROR] Issue with profile_picture field: {str(e)}")

def check_form_issues():
    """Check common form issues"""
    from users.forms import UserUpdateForm
    
    # Create a sample instance
    try:
        users = User.objects.all()
        if users.exists():
            user = users.first()
            form = UserUpdateForm(instance=user)
            print(f"[OK] UserUpdateForm can be instantiated for user: {user.username}")
            
            # Check form fields
            if 'profile_picture' in form.fields:
                print("[OK] Form has profile_picture field")
            else:
                print("[ERROR] Form is missing profile_picture field")
                
            # Check for required fields that might cause validation issues
            required_fields = [name for name, field in form.fields.items() if field.required]
            print(f"[INFO] Required fields in form: {', '.join(required_fields)}")
    except Exception as e:
        print(f"[ERROR] Issue with UserUpdateForm: {str(e)}")

if __name__ == '__main__':
    print("=== PROFILE UPDATE DIAGNOSTICS ===")
    print("\n=== Media Directory Check ===")
    check_media_permissions()
    
    print("\n=== Profile Picture Field Check ===")
    check_profile_picture_field()
    
    print("\n=== Form Check ===")
    check_form_issues()
    
    print("\n=== Troubleshooting Tips ===")
    print("1. Make sure the form has enctype='multipart/form-data' attribute")
    print("2. Check that UserUpdateForm.Meta includes 'profile_picture' in its fields")
    print("3. Ensure the template loads the form correctly")
    print("4. Verify the view saves the form properly")
    print("5. Check for JavaScript errors that might prevent form submission") 