"""
Business logic for the users app.

Keeps side-effecting operations (file handling, profile mutations) out of the
views so they stay thin and the logic is reusable/testable.
"""
import base64
import binascii
import os
import uuid

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


def apply_cropped_profile_picture(request):
    """Decode a base64 ``cropped_data`` POST field (if present) and inject it
    into ``request.FILES['profile_picture']``.

    Returns an error message string on failure, or ``None`` on success/no-op.
    """
    cropped_data = request.POST.get('cropped_data')
    if not (cropped_data and cropped_data.startswith('data:image')):
        return None

    try:
        fmt, imgstr = cropped_data.split(';base64,')
        ext = fmt.split('/')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        temp_file_path = os.path.join(settings.MEDIA_ROOT, 'temp', filename)
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

        with open(temp_file_path, 'wb') as f:
            f.write(base64.b64decode(imgstr))
        with open(temp_file_path, 'rb') as f:
            request.FILES['profile_picture'] = SimpleUploadedFile(
                name=filename,
                content=f.read(),
                content_type=fmt.split(':')[1],
            )
        os.remove(temp_file_path)
        return None
    except (binascii.Error, IOError, OSError) as e:
        return f"Error processing cropped image: {str(e)}"


def clear_profile_picture(user):
    """Delete the user's profile-picture file and clear the field.

    Returns ``True`` if a picture file was actually removed.
    """
    if not user.profile_picture:
        return False
    if hasattr(user.profile_picture, 'path') and os.path.exists(user.profile_picture.path):
        old_path = user.profile_picture.path
        user.profile_picture = None
        user.save()
        os.remove(old_path)
        return True
    return False
