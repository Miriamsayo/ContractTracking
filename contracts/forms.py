from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Contract, CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username',  'email', 'first_name', 'last_name' ]

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['staff_name', 'title', 'contract_type', 'start_date', 'end_date']
        
        