from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

# Create your models here.

class ContactInquiry(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('READ', 'Read'),
        ('REPLIED', 'Replied'),
        ('CLOSED', 'Closed'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contact_inquiries')
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for staff")
    reply_message = models.TextField(blank=True, null=True, help_text="Reply message sent to customer")
    
    # Notification tracking
    is_notification_sent = models.BooleanField(default=False)
    notification_seen = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Contact Inquiries"
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.status})"
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status_classes = {
            'PENDING': 'bg-warning',
            'READ': 'bg-info',
            'REPLIED': 'bg-success',
            'CLOSED': 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-primary')


class AppointmentInquiry(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONTACTED', 'Contacted'),
        ('SCHEDULED', 'Scheduled'),
        ('CLOSED', 'Closed'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('general_medicine', 'General Medicine MD'),
        ('cardiology', 'Cardiologist'),
        ('orthopedics', 'Orthopedic'),
        ('neurology', 'Neurologist'),
        ('oncology', 'Cancer'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    preferred_doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointment_inquiries', limit_choices_to={'role': 'DOCTOR'})
    message = models.TextField()
    preferred_date = models.DateField()
    
    # File Upload
    health_records = models.FileField(upload_to='health_records/', blank=True, null=True)
    
    # Status and Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_inquiries')
    notes = models.TextField(blank=True, null=True, help_text="Internal notes for receptionist")
    reply_message = models.TextField(blank=True, null=True, help_text="Reply message sent to customer")
    
    # Notification tracking
    is_notification_sent = models.BooleanField(default=False)
    notification_seen = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Appointment Inquiries"
    
    def __str__(self):
        return f"{self.name} - {self.get_department_display()} ({self.status})"
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status_classes = {
            'PENDING': 'bg-warning',
            'CONTACTED': 'bg-info',
            'SCHEDULED': 'bg-success',
            'CLOSED': 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-primary')


class EmailReply(models.Model):
    """Model to track incoming email replies from customers"""
    
    # Email content
    sender_email = models.EmailField()
    sender_name = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=300)
    message_body = models.TextField()
    message_id = models.CharField(max_length=200, unique=True, help_text="Email Message-ID to prevent duplicates")
    
    # Link to original inquiry (if found)
    related_contact_inquiry = models.ForeignKey(ContactInquiry, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_replies')
    related_appointment_inquiry = models.ForeignKey(AppointmentInquiry, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_replies')
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    is_seen_by_staff = models.BooleanField(default=False)
    staff_notes = models.TextField(blank=True, null=True, help_text="Internal staff notes about this reply")
    
    # Raw email data
    raw_email_headers = models.JSONField(blank=True, null=True, help_text="Raw email headers for debugging")
    
    # Timestamps
    email_received_at = models.DateTimeField(help_text="When the email was actually received")
    processed_at = models.DateTimeField(auto_now_add=True, help_text="When we processed the email")
    
    class Meta:
        ordering = ['-email_received_at']
        verbose_name_plural = "Email Replies"
    
    def __str__(self):
        return f"Reply from {self.sender_email} - {self.subject[:50]}"
    
    def get_related_inquiry(self):
        """Get the related inquiry (contact or appointment)"""
        if self.related_contact_inquiry:
            return self.related_contact_inquiry
        elif self.related_appointment_inquiry:
            return self.related_appointment_inquiry
        return None
    
    def get_inquiry_type(self):
        """Get the type of related inquiry"""
        if self.related_contact_inquiry:
            return 'contact'
        elif self.related_appointment_inquiry:
            return 'appointment'
        return 'unmatched'
    
    @classmethod
    def conversation_limit_reached(cls, contact_inquiry=None, appointment_inquiry=None):
        """Check if conversation has reached the 20 reply limit"""
        CONVERSATION_LIMIT = 20
        
        if contact_inquiry:
            count = cls.objects.filter(related_contact_inquiry=contact_inquiry).count()
            return count >= CONVERSATION_LIMIT
        elif appointment_inquiry:
            count = cls.objects.filter(related_appointment_inquiry=appointment_inquiry).count()
            return count >= CONVERSATION_LIMIT
        
        return False
    
    def get_conversation_reply_count(self):
        """Get total number of replies in this conversation"""
        if self.related_contact_inquiry:
            return EmailReply.objects.filter(related_contact_inquiry=self.related_contact_inquiry).count()
        elif self.related_appointment_inquiry:
            return EmailReply.objects.filter(related_appointment_inquiry=self.related_appointment_inquiry).count()
        return 0


class Blog(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('HEALTH_TIPS', 'Health Tips'),
        ('MEDICAL_NEWS', 'Medical News'),
        ('TREATMENT_UPDATES', 'Treatment Updates'),
        ('RESEARCH', 'Medical Research'),
        ('WELLNESS', 'Wellness & Prevention'),
        ('TECHNOLOGY', 'Medical Technology'),
        ('PATIENT_CARE', 'Patient Care'),
        ('GENERAL', 'General'),
    ]
    
    # Basic Info
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'DOCTOR'}, related_name='blog_posts')
    content = models.TextField()
    excerpt = models.TextField(max_length=300, help_text="Brief description of the blog post")
    
    # Media
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    
    # Categorization
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    
    # Status and Publishing
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    is_featured = models.BooleanField(default=False, help_text="Feature this post on the homepage")
    
    # SEO and Metadata
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    read_time = models.PositiveIntegerField(default=5, help_text="Estimated read time in minutes")
    
    # Statistics
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Blog Posts"
    
    def __str__(self):
        return f"{self.title} by {self.author.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure unique slug
            counter = 1
            original_slug = self.slug
            while Blog.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('website:blog_detail', kwargs={'slug': self.slug})
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status_classes = {
            'DRAFT': 'bg-warning',
            'PUBLISHED': 'bg-success',
            'ARCHIVED': 'bg-secondary',
        }
        return status_classes.get(self.status, 'bg-primary')
    
    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class BlogSubscription(models.Model):
    """Model for users to subscribe to specific doctors' blogs"""
    
    # Subscriber info
    email = models.EmailField()
    name = models.CharField(max_length=100, blank=True)
    
    # Doctor to follow
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'DOCTOR'},
        related_name='blog_subscribers'
    )
    
    # Subscription settings
    is_active = models.BooleanField(default=True)
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('IMMEDIATE', 'Immediate'),
            ('DAILY', 'Daily Digest'),
            ('WEEKLY', 'Weekly Digest'),
        ],
        default='IMMEDIATE'
    )
    
    # Timestamps
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_notification_sent = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['email', 'doctor']
        ordering = ['-subscribed_at']
        verbose_name_plural = "Blog Subscriptions"
    
    def __str__(self):
        return f"{self.email} subscribed to Dr. {self.doctor.get_full_name()}"


class BlogComment(models.Model):
    """Model for blog comments"""
    
    blog_post = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    
    # Commenter info
    name = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Comment content
    comment = models.TextField()
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Blog Comments"
    
    def __str__(self):
        return f"Comment by {self.name} on {self.blog_post.title}"
