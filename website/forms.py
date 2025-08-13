from django import forms
from django.contrib.auth import get_user_model
from .models import Blog, ContactInquiry, AppointmentInquiry, BlogSubscription, BlogComment
from users.models import User

User = get_user_model()

class BlogForm(forms.ModelForm):
    """Form for creating and editing blog posts"""
    
    class Meta:
        model = Blog
        fields = [
            'title', 'content', 'excerpt', 'featured_image', 
            'category', 'tags', 'status', 'is_featured', 
            'meta_description', 'read_time'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter blog title...',
                'maxlength': '200'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Write your blog content here...'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of your blog post...',
                'maxlength': '300'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'health, medicine, wellness (comma-separated)',
                'maxlength': '200'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'meta_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SEO description for search engines...',
                'maxlength': '160'
            }),
            'read_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60',
                'placeholder': '5'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set field requirements and help texts
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['excerpt'].required = False  # Make optional for now
        self.fields['category'].required = True
        
        # Set default values
        if not self.instance.pk:  # Only for new instances
            self.fields['read_time'].initial = 5
            self.fields['status'].initial = 'DRAFT'
        
        # Make some fields optional
        self.fields['read_time'].required = False
        self.fields['meta_description'].required = False
        self.fields['tags'].required = False
        self.fields['featured_image'].required = False
        
        # Help texts
        self.fields['tags'].help_text = "Enter comma-separated tags (e.g., health, medicine, wellness)"
        self.fields['read_time'].help_text = "Estimated reading time in minutes"
        self.fields['meta_description'].help_text = "Brief description for search engines (160 chars max)"
        self.fields['is_featured'].help_text = "Check to feature this post on the homepage"
    
    def save(self, commit=True):
        blog = super().save(commit=False)
        if self.user:
            blog.author = self.user
        
        # Set published_at when status changes to PUBLISHED
        if blog.status == 'PUBLISHED' and not blog.published_at:
            from django.utils import timezone
            blog.published_at = timezone.now()
        
        if commit:
            blog.save()
        return blog

class ContactInquiryForm(forms.ModelForm):
    """Form for contact inquiries"""
    
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Phone'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your Message'
            }),
        }

class AppointmentInquiryForm(forms.ModelForm):
    """Form for appointment inquiries"""
    
    class Meta:
        model = AppointmentInquiry
        fields = [
            'name', 'email', 'phone', 'department', 
            'preferred_doctor', 'message', 'preferred_date', 'health_records'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Phone'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'preferred_doctor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your Message'
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'health_records': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter doctors only
        self.fields['preferred_doctor'].queryset = User.objects.filter(role='DOCTOR').order_by('first_name', 'last_name')
        self.fields['preferred_doctor'].empty_label = "Any Available Doctor"

class BlogSubscriptionForm(forms.ModelForm):
    class Meta:
        model = BlogSubscription
        fields = ['name', 'email', 'notification_frequency']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name (Optional)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email Address'
            }),
            'notification_frequency': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = False

class BlogCommentForm(forms.ModelForm):
    class Meta:
        model = BlogComment
        fields = ['name', 'email', 'website', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Website (Optional)'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your comment here...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['website'].required = False

class BlogSearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search blogs...'
        })
    )
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Blog.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    author = forms.ModelChoiceField(
        queryset=User.objects.filter(role='DOCTOR').order_by('first_name', 'last_name'),
        required=False,
        empty_label="All Doctors",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    ) 