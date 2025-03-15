from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Contract, CustomUser
from django.contrib.auth import get_user_model

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["unit",
            "staff_name",
            "title",
            "contract_type",
            "description",
            "start_date",
            "end_date",
            "file",
            "supervisor",  
            "status", 
            "supervisor_approval",
            "hr_approval",
        ]
        
User = get_user_model()   


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password"]      

            
        
