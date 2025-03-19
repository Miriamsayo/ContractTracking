from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Contract, CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            "unit",
            "staff_name",
            "title",
            "contract_type",
            "description",
            "start_date",
            "end_date",
            "file",
            "supervisor",   
            "supervisor_approval",
            "hr_approval",
            'status'
        ]

    def clean_staff_name(self):
        staff_name = self.cleaned_data.get("staff_name", "").strip()
        if not staff_name:
            raise forms.ValidationError("A staff name must be selected to create a contract.")
        return staff_name

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if not title:
            raise forms.ValidationError("A job title must be provided.")
        return title


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "role", "unit", "supervisor"]

    def clean_email(self):
        email = self.cleaned_data.get("email").strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
