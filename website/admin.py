from django.contrib import admin
from .models import ContactInquiry, AppointmentInquiry, Blog, BlogSubscription, BlogComment, EmailReply

# Register your models here.

@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'subject', 'message')
        }),
        ('Management', {
            'fields': ('status', 'assigned_to', 'admin_notes', 'reply_message')
        }),
        ('Notifications', {
            'fields': ('is_notification_sent', 'notification_seen'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'replied_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AppointmentInquiry)
class AppointmentInquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'department', 'preferred_doctor', 'status', 'created_at']
    list_filter = ['department', 'status', 'created_at', 'preferred_doctor']
    search_fields = ['name', 'email', 'department']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('name', 'email', 'phone', 'department', 'preferred_doctor', 'message', 'preferred_date')
        }),
        ('Documents', {
            'fields': ('health_records',)
        }),
        ('Management', {
            'fields': ('status', 'assigned_to', 'notes', 'reply_message')
        }),
        ('Notifications', {
            'fields': ('is_notification_sent', 'notification_seen'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'replied_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_featured', 'views_count', 'created_at']
    list_filter = ['status', 'category', 'is_featured', 'created_at', 'author']
    search_fields = ['title', 'content', 'tags', 'author__first_name', 'author__last_name']
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['views_count', 'created_at', 'updated_at', 'published_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'category')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image')
        }),
        ('Publishing', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('SEO & Meta', {
            'fields': ('tags', 'meta_description', 'read_time'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'likes_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(BlogSubscription)
class BlogSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'doctor', 'notification_frequency', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'notification_frequency', 'subscribed_at', 'doctor']
    search_fields = ['email', 'name', 'doctor__first_name', 'doctor__last_name']
    readonly_fields = ['subscribed_at', 'last_notification_sent']
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': ('email', 'name', 'doctor')
        }),
        ('Subscription Settings', {
            'fields': ('is_active', 'notification_frequency')
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'last_notification_sent'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'blog_post', 'is_approved', 'is_spam', 'created_at']
    list_filter = ['is_approved', 'is_spam', 'created_at', 'blog_post__author']
    search_fields = ['name', 'email', 'comment', 'blog_post__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('blog_post', 'name', 'email', 'website', 'comment')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_spam')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_comments', 'mark_as_spam', 'mark_as_not_spam']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True, is_spam=False)
        self.message_user(request, f'{queryset.count()} comments approved successfully.')
    approve_comments.short_description = "Approve selected comments"
    
    def mark_as_spam(self, request, queryset):
        queryset.update(is_spam=True, is_approved=False)
        self.message_user(request, f'{queryset.count()} comments marked as spam.')
    mark_as_spam.short_description = "Mark selected comments as spam"
    
    def mark_as_not_spam(self, request, queryset):
        queryset.update(is_spam=False)
        self.message_user(request, f'{queryset.count()} comments unmarked as spam.')
    mark_as_not_spam.short_description = "Unmark selected comments as spam"


@admin.register(EmailReply)
class EmailReplyAdmin(admin.ModelAdmin):
    list_display = ['sender_email', 'sender_name', 'subject', 'get_inquiry_type', 'is_seen_by_staff', 'email_received_at']
    list_filter = ['is_seen_by_staff', 'is_processed', 'email_received_at']
    search_fields = ['sender_email', 'sender_name', 'subject', 'message_body']
    readonly_fields = ['email_received_at', 'processed_at', 'message_id']
    
    fieldsets = (
        ('Email Information', {
            'fields': ('sender_email', 'sender_name', 'subject', 'message_body', 'message_id')
        }),
        ('Related Inquiries', {
            'fields': ('related_contact_inquiry', 'related_appointment_inquiry')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'is_seen_by_staff', 'staff_notes')
        }),
        ('Raw Data', {
            'fields': ('raw_email_headers',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('email_received_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_seen', 'mark_as_processed']
    
    def mark_as_seen(self, request, queryset):
        queryset.update(is_seen_by_staff=True)
        self.message_user(request, f'{queryset.count()} email replies marked as seen.')
    mark_as_seen.short_description = "Mark selected email replies as seen"
    
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
        self.message_user(request, f'{queryset.count()} email replies marked as processed.')
    mark_as_processed.short_description = "Mark selected email replies as processed"
