from django.urls import path
from . import views

urlpatterns = [
    # Add billing views here
    path('', views.billing_home, name='billing_home'),
] 