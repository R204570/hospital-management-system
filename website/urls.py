from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Blog URLs
    path('blog/', views.blog, name='blog'),
    path('blog/create/', views.create_blog, name='create_blog'),
    path('blog/my-blogs/', views.my_blogs, name='my_blogs'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/<slug:slug>/edit/', views.edit_blog, name='edit_blog'),
    path('blog/<slug:slug>/delete/', views.delete_blog, name='delete_blog'),
    path('blog/<slug:slug>/view/', views.track_blog_view, name='track_blog_view'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    path('doctors/', views.doctors, name='doctors'),
    path('service/', views.service, name='service'),
    path('login/', views.login_view, name='login'),
    path('appointment/', views.appointment, name='appointment'),
    path('appointment-inquiry/', views.appointment_inquiry, name='appointment_inquiry'),
] 