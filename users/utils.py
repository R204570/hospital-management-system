import random
import string
import os
import traceback
import base64
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import timedelta
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import os.path

def generate_otp(length=6):
    """Generate a random numeric OTP of specified length"""
    digits = string.digits
    return ''.join(random.choice(digits) for _ in range(length))

def send_otp_email(user, otp):
    """Send OTP via email to the user with HTML formatting and logo"""
    subject = 'OTP for changing password'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    
    # Ensure otp is a string 
    otp_str = str(otp)
    
    # Use the hosted image URL from ImageKit
    logo_url = "https://ik.imagekit.io/smartcarelogo/smartcare-logo.png?updatedAt=1750880603700"
    
    # HTML email content with hosted image URL
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OTP for Password Reset</title>
        <style>
            @media screen and (max-width: 480px) {{
                .container {{
                    width: 100% !important;
                    padding: 10px !important;
                }}
                .header {{
                    padding: 15px !important;
                }}
                .content {{
                    padding: 20px !important;
                }}
                .logo {{
                    width: 90% !important;
                    max-width: 250px !important;
                }}
                .otp-box {{
                    font-size: 20px !important;
                    padding: 15px !important;
                }}
            }}
            
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0;
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 20px;
                width: 100%;
                box-sizing: border-box;
            }}
            .header {{ 
                text-align: center; 
                margin-bottom: 30px; 
                background-color: #0037ff; 
                padding: 20px;
                border-radius: 8px 8px 0 0;
            }}
            .content {{ 
                background-color: #f9f9f9; 
                padding: 30px; 
                border-radius: 0 0 8px 8px;
            }}
            .otp-box {{ 
                background-color: #f2f2f2; 
                padding: 20px; 
                text-align: center; 
                font-size: 24px; 
                letter-spacing: 4px;
                font-weight: bold;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            h2 {{ color: #333; text-align: center; }}
            p {{ color: #555; line-height: 1.5; }}
            .logo {{ 
                max-width: 280px; 
                width: auto;
                margin: 0 auto; 
                display: block; 
                background-color: white;
                border-radius: 4px;
                padding: 12px;
                border: 3px solid #0037ff;
                box-sizing: border-box;
            }}
            img.logo-img {{
                max-width: 260px;
                width: auto;
                height: auto;
                display: block;
                margin: 0 auto;
            }}
            .additional-message {{
                margin-top: 30px;
                padding: 15px;
                background-color: #e6f7ff;
                border-left: 4px solid #0037ff;
                font-style: italic;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">
                    <img src="{logo_url}" alt="Smart Care Logo" class="logo-img">
                </div>
            </div>
            
            <div class="content">
                <h2>OTP for changing password</h2>
                <p>Use this OTP to change your password:</p>
                
                <div class="otp-box">
                    {otp_str}
                </div>
                
                <p>This OTP is valid for 2 minutes.</p>
                
                <div class="additional-message">
                    <p>Thank you for using Smart Care Hospital Management System. We are committed to providing you with secure and reliable healthcare services.</p>
                    <p>For security reasons, please do not share this OTP with anyone.</p>
                </div>
            </div>
            
            <div class="footer">
                <p>If you didn't request this password change, please ignore this email.</p>
                <p>&copy; {timezone.now().year} Smart Care - Hospital Management System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version of the email
    plain_text = f"""
    SMART CARE - Hospital Management System

    OTP for changing password
    
    Use this OTP to change your password: {otp}
    
    This OTP is valid for 2 minutes.
    
    Thank you for using Smart Care Hospital Management System. We are committed to providing you with secure and reliable healthcare services.
    
    For security reasons, please do not share this OTP with anyone.
    
    If you didn't request this password change, please ignore this email.
    """
    
    try:
        # Create email message with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject,
            plain_text,
            from_email,
            recipient_list
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        email.send(fail_silently=False)
        print(f"OTP email sent successfully to {user.email}")
        return True
    except Exception as e:
        error_tb = traceback.format_exc()
        print(f"Error sending email: {str(e)}")
        print(f"Error traceback: {error_tb}")
        return False

def is_otp_valid(otp, stored_otp, created_time):
    """
    Check if OTP is valid:
    1. OTP matches
    2. OTP is not expired (2 minutes)
    """
    if not otp or not stored_otp or not created_time:
        return False
    
    # Check if OTP matches
    if otp != stored_otp:
        return False
    
    # Check if OTP is expired (2 minutes)
    expiry_time = created_time + timedelta(minutes=2)
    if timezone.now() > expiry_time:
        return False
    
    return True 