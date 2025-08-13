import imaplib
import email
import re
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from website.models import EmailReply, ContactInquiry, AppointmentInquiry


class Command(BaseCommand):
    help = 'Check Gmail inbox for email replies and link them to inquiries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Limit number of emails to process (default: 10)',
        )
        parser.add_argument(
            '--mark-seen',
            action='store_true',
            help='Mark processed emails as seen in Gmail',
        )

    def handle(self, *args, **options):
        import time
        start_time = time.time()
        self.stdout.write(self.style.SUCCESS('🔍 Checking Gmail inbox for new replies...'))
        
        limit = options['limit']
        mark_seen = options['mark_seen']
        
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
            mail.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
            
            # Select inbox
            mail.select('inbox')
            
            # Search for unread emails (or recent emails)
            if mark_seen:
                # Only unseen emails
                status, email_ids = mail.search(None, 'UNSEEN')
            else:
                # Recent emails (last 3 days only) to improve performance
                from datetime import datetime, timedelta
                three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%d-%b-%Y')
                status, email_ids = mail.search(None, f'SINCE "{three_days_ago}"')
            
            if status != 'OK':
                self.stdout.write(self.style.ERROR('❌ Failed to search emails'))
                return
                
            email_ids = email_ids[0].split()
            
            if not email_ids:
                self.stdout.write(self.style.WARNING('📭 No new emails found'))
                return
                
            self.stdout.write(f'📧 Found {len(email_ids)} emails to process (limit: {limit})')
            
            processed_count = 0
            new_replies_count = 0
            
            # Process emails (limit to avoid overloading)
            for email_id in email_ids[-limit:]:  # Get most recent emails
                try:
                    # Fetch email
                    status, email_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                        
                    # Parse email
                    raw_email = email_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Extract email details
                    subject = self.decode_header_value(email_message.get('Subject', ''))
                    sender = self.decode_header_value(email_message.get('From', ''))
                    message_id = email_message.get('Message-ID', '')
                    date_received = email_message.get('Date', '')
                    
                    # Parse sender email address
                    sender_email = self.extract_email_address(sender)
                    sender_name = self.extract_sender_name(sender)
                    
                    # Parse date
                    try:
                        email_received_at = parsedate_to_datetime(date_received)
                        if email_received_at.tzinfo is None:
                            email_received_at = timezone.make_aware(email_received_at)
                    except:
                        email_received_at = timezone.now()
                    
                    # Check if we already processed this email
                    if EmailReply.objects.filter(message_id=message_id).exists():
                        continue
                    
                    # Skip very old emails (older than 7 days) to improve performance
                    if (timezone.now() - email_received_at).days > 7:
                        continue
                    
                    # Extract email body
                    body = self.extract_email_body(email_message)
                    
                    # Skip if this looks like an automated email or from our own system
                    if self.is_automated_email(sender_email, subject, body):
                        continue
                    
                    # Quick hospital relevance check (before heavy processing)
                    if not self.is_hospital_related_email(sender_email, subject, body):
                        continue
                    
                    # Try to match with existing inquiries
                    related_contact = self.find_matching_contact_inquiry(sender_email, subject, body)
                    related_appointment = self.find_matching_appointment_inquiry(sender_email, subject, body)
                    
                    # Check if existing conversation has reached 20 replies limit
                    if related_contact:
                        existing_replies_count = EmailReply.objects.filter(
                            related_contact_inquiry=related_contact
                        ).count()
                        if existing_replies_count >= 20:
                            self.stdout.write(f'  🔄 Contact conversation limit reached (20 replies), starting new thread')
                            related_contact = None  # Start new conversation
                    
                    if related_appointment:
                        existing_replies_count = EmailReply.objects.filter(
                            related_appointment_inquiry=related_appointment
                        ).count()
                        if existing_replies_count >= 20:
                            self.stdout.write(f'  🔄 Appointment conversation limit reached (20 replies), starting new thread')
                            related_appointment = None  # Start new conversation
                    
                    # Create EmailReply record
                    with transaction.atomic():
                        email_reply = EmailReply.objects.create(
                            sender_email=sender_email,
                            sender_name=sender_name,
                            subject=subject,
                            message_body=body,
                            message_id=message_id,
                            related_contact_inquiry=related_contact,
                            related_appointment_inquiry=related_appointment,
                            email_received_at=email_received_at,
                            raw_email_headers={
                                'from': sender,
                                'to': email_message.get('To', ''),
                                'cc': email_message.get('Cc', ''),
                                'reply_to': email_message.get('Reply-To', ''),
                            },
                        )
                        
                        # Update related inquiry status if matched
                        if related_contact:
                            related_contact.status = 'REPLIED'
                            related_contact.save()
                            self.stdout.write(f'  📎 Linked to contact inquiry: {related_contact.name}')
                        elif related_appointment:
                            related_appointment.status = 'CONTACTED'
                            related_appointment.save()
                            self.stdout.write(f'  📎 Linked to appointment inquiry: {related_appointment.name}')
                        else:
                            self.stdout.write(f'  ❓ Unmatched email from: {sender_email}')
                    
                    self.stdout.write(f'  ✅ Processed: {subject[:50]}...')
                    processed_count += 1
                    new_replies_count += 1
                    
                    # Mark as seen in Gmail if requested
                    if mark_seen:
                        mail.store(email_id, '+FLAGS', '\\Seen')
                        
                except Exception as e:
                    self.stdout.write(f'  ❌ Error processing email {email_id}: {str(e)}')
                    continue
            
            # Close connection
            mail.close()
            mail.logout()
            
            total_time = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Completed! Processed {processed_count} emails, found {new_replies_count} new replies in {total_time:.2f}s'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ IMAP connection error: {str(e)}'))
            self.stdout.write('💡 Make sure Gmail IMAP is enabled and app password is correct')

    def decode_header_value(self, value):
        """Decode email header value"""
        if not value:
            return ''
        
        decoded_parts = decode_header(value)
        decoded_value = ''
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_value += part.decode(encoding)
                    except:
                        decoded_value += part.decode('utf-8', errors='ignore')
                else:
                    decoded_value += part.decode('utf-8', errors='ignore')
            else:
                decoded_value += part
                
        return decoded_value

    def extract_email_address(self, sender):
        """Extract email address from sender field"""
        if not sender:
            return ''
        
        # Use regex to extract email from "Name <email@domain.com>" format
        email_match = re.search(r'<([^>]+)>', sender)
        if email_match:
            return email_match.group(1).strip()
        
        # If no angle brackets, assume the whole thing is an email
        if '@' in sender:
            return sender.strip()
            
        return ''

    def extract_sender_name(self, sender):
        """Extract sender name from sender field"""
        if not sender:
            return ''
        
        # Extract name from "Name <email@domain.com>" format
        if '<' in sender:
            name = sender.split('<')[0].strip()
            # Remove quotes if present
            name = name.strip('"').strip("'")
            return name
        
        return ''

    def extract_email_body(self, email_message):
        """Extract text content from email"""
        body = ''
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                
                if content_type == 'text/plain':
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break
                    except:
                        continue
                        
                elif content_type == 'text/html' and not body:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        # Simple HTML to text conversion
                        body = re.sub(r'<[^>]+>', '', html_body)
                        body = re.sub(r'\s+', ' ', body).strip()
                    except:
                        continue
        else:
            try:
                charset = email_message.get_content_charset() or 'utf-8'
                body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
            except:
                body = str(email_message.get_payload())
        
        # Clean up the body
        body = body.strip()
        
        # Remove email signatures and quoted text (basic cleanup)
        lines = body.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Stop at common reply indicators
            if any(indicator in line.lower() for indicator in [
                '--- original message ---',
                'on ', 'wrote:',
                '-----original message-----',
                'from:', 'sent:', 'to:', 'subject:'
            ]):
                break
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()

    def is_automated_email(self, sender_email, subject, body):
        """Check if this looks like an automated email or non-hospital related email"""
        # Skip emails from our own system
        if sender_email == settings.EMAIL_HOST_USER:
            return True
        
        # Skip common automated email patterns
        automated_indicators = [
            'noreply', 'no-reply', 'donotreply', 'mailer-daemon',
            'postmaster', 'delivery-status', 'bounce'
        ]
        
        for indicator in automated_indicators:
            if indicator in sender_email.lower():
                return True
        
        # Skip auto-reply subjects
        auto_reply_subjects = [
            'out of office', 'vacation', 'automatic reply',
            'delivery failure', 'undelivered', 'bounce'
        ]
        
        for indicator in auto_reply_subjects:
            if indicator in subject.lower():
                return True
        
        # Skip non-hospital related domains and services
        non_hospital_domains = [
            'cursor.so', 'github.com', 'linkedin.com', 'facebook.com', 
            'twitter.com', 'instagram.com', 'youtube.com', 'google.com',
            'microsoft.com', 'apple.com', 'amazon.com', 'netflix.com',
            'dropbox.com', 'slack.com', 'discord.com', 'zoom.us'
        ]
        
        for domain in non_hospital_domains:
            if domain in sender_email.lower():
                return True
        
        # Skip non-hospital related subjects
        non_hospital_subjects = [
            'cursor', 'github', 'linkedin', 'facebook', 'social media',
            'newsletter', 'promotion', 'offer', 'sale', 'discount',
            'software update', 'app notification', 'subscription'
        ]
        
        subject_lower = subject.lower()
        for keyword in non_hospital_subjects:
            if keyword in subject_lower:
                return True
        
        # Check if this email is hospital-related
        hospital_keywords = [
            'appointment', 'smartcare', 'hospital', 'medical', 'doctor', 
            'patient', 'inquiry', 'health', 'clinic', 'medicine', 'treatment'
        ]
        
        # Check if sender has existing inquiries (known patient/customer)
        has_existing_inquiry = False
        try:
            from website.models import ContactInquiry, AppointmentInquiry
            has_existing_inquiry = (
                ContactInquiry.objects.filter(email=sender_email).exists() or
                AppointmentInquiry.objects.filter(email=sender_email).exists()
            )
        except:
            pass
        
        # If sender has existing inquiries, always process the email
        if has_existing_inquiry:
            return False
        
        # For new senders, only process if it contains hospital keywords
        contains_hospital_keywords = any(
            keyword in subject_lower or keyword in body.lower() 
            for keyword in hospital_keywords
        )
        
        if not contains_hospital_keywords:
            return True  # Skip non-hospital related emails
                
        return False
    
    def is_hospital_related_email(self, sender_email, subject, body):
        """Quick check if email is potentially hospital-related (used for early filtering)"""
        # This is a lightweight version of the hospital check in is_automated_email
        # Check if sender has existing inquiries (known patient/customer)
        try:
            from website.models import ContactInquiry, AppointmentInquiry
            has_existing_inquiry = (
                ContactInquiry.objects.filter(email=sender_email).exists() or
                AppointmentInquiry.objects.filter(email=sender_email).exists()
            )
            if has_existing_inquiry:
                return True
        except:
            pass
        
        # Look for hospital keywords in subject (quick check)
        hospital_keywords = ['appointment', 'doctor', 'hospital', 'medical', 'smartcare']
        return any(keyword in subject.lower() for keyword in hospital_keywords)
    
    def find_matching_contact_inquiry(self, sender_email, subject, body):
        """Try to find matching contact inquiry"""
        # First, try exact email match
        inquiries = ContactInquiry.objects.filter(
            email__iexact=sender_email
        ).order_by('-created_at')
        
        if inquiries.exists():
            # If subject contains "Re:" and matches inquiry subject
            for inquiry in inquiries[:5]:  # Check last 5 inquiries
                if f"re: {inquiry.subject.lower()}" in subject.lower():
                    return inquiry
            
            # Return most recent inquiry from this email
            return inquiries.first()
        
        return None

    def find_matching_appointment_inquiry(self, sender_email, subject, body):
        """Try to find matching appointment inquiry"""
        # First, try exact email match
        inquiries = AppointmentInquiry.objects.filter(
            email__iexact=sender_email
        ).order_by('-created_at')
        
        if inquiries.exists():
            # If subject contains "Re:" and mentions appointment or department
            for inquiry in inquiries[:5]:  # Check last 5 inquiries
                department_name = inquiry.get_department_display().lower()
                if any(keyword in subject.lower() for keyword in [
                    f"re: your appointment inquiry - {department_name}",
                    "appointment", department_name
                ]):
                    return inquiry
            
            # Return most recent inquiry from this email
            return inquiries.first()
        
        return None 