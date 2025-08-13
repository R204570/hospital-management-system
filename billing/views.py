from django.shortcuts import render
from django.http import HttpResponse

def billing_home(request):
    return HttpResponse("Billing Home Page") 