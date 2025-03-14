from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse
from django.utils.timezone import now
import datetime
from django.contrib.auth import get_user_model
from django.conf import settings
from contracts.models import Contract, Unit
from .serializers import ContractSerializer
import logging
from .forms import CustomUserCreationForm, ContractForm
from django.contrib.auth import logout
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


def dashboard(request):
    return render(request, "contracts/dashboard.html")


def user_list(request):
    User = get_user_model()
    users = User.objects.all()
    return render(request, "contracts/user/user_list.html", {"users": users})


def settings_view(request):
    return render(request, "contracts/settings.html")


def contract_list(request):
    user = request.user

    if hasattr(user, "role"):
        if user.role == "Admin":
            contracts = Contract.objects.all()
        elif user.role == "User":
            contracts = Contract.objects.filter(unit=user.unit)
        else:  # Supervisor sees all their subordinates' contracts
            contracts = Contract.objects.filter(employee__supervisor=user)
    else:
        contracts = Contract.objects.none()
    return render(request, "contracts/contract_list.html", {"contracts": contracts})


# Edit contract (Fix: Ensure updating the existing contract)
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)

    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, "Contract updated successfully.")
            return redirect("contract_list")
        else:
            messages.error(request, "There was an error updating the contract.")
    else:
        form = ContractForm(instance=contract)

    return render(request, "contracts/contract_edit.html", {"form": form})


def add_contract(request):
    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("contracts")
    else:
        form = ContractForm()

    return render(request, "contracts/contract_form.html", {"form": form})


def contract_create(request):
    if request.method == "GET":
        form = ContractForm()
        
    elif request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contract_list')
    return render(request, 'contracts/contract_form.html', {'form': form})    
def update_contract(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    if request.method == "POST":
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            return redirect("contract_list")
    else:
        form = ContractForm(instance=contract)
    return render(request, "contracts/update_contract.html", {"form": form})


def delete_contract(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        contract.delete()
        return redirect("contract_list")
    return render(
        request,
        "contracts/contract_details.html",
        {"contract": contract, "delete_mode": True},
    )


def contract_detail(request, id):
    contract = get_object_or_404(Contract, id=id)
    return render(request, "contracts/contract_detail.html", {"contract": contract})



def send_notification_email(subject, message, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")


# Login view (Fix: Redirect instead of JSON response)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "contracts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# Signup view
def signup(request):
    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the new user
            user = authenticate(
                request, username=user.username, password=request.POST["password1"]
            )  # Authenticate the user
            if user is not None:
                login(request, user)  # Log the user in
                return redirect(
                    "dashboard"
                )  # Redirect to home or another page after successful signup

    return render(request, "signup.html", {"form": form})


# Contract API ViewSet
class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer

    @action(detail=True, methods=["post"])
    def approve_by_supervisor(self, request, pk=None):
        contract = get_object_or_404(Contract, pk=pk)
        if request.employee != contract.supervisor:
            return Response(
                {"error": "Only the supervisor can approve."},
                status=status.HTTP_403_FORBIDDEN,
            )

        contract.supervisor_approval = True
        contract.save()

        send_notification_email(
            subject="Contract Approved by Supervisor",
            message=f"Contract {contract.id} has been approved by Supervisor {request.user}.",
            recipient_list=[contract.employee.email],
        )
        messages.success(request, f"Contract {contract.id} approved successfully.")
        logger.info(f"Contract {contract.id} approved by Supervisor {request.user}")
        return Response(
            {"message": "Contract approved by Supervisor"}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def approve_by_hr(self, request, pk=None):
        contract = get_object_or_404(Contract, pk=pk)

        if not contract.supervisor_approval:
            return Response(
                {"error": "Supervisor approval required first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.is_superuser:
            return Response(
                {"error": "Only HR/Admin can approve."},
                status=status.HTTP_403_FORBIDDEN,
            )

        contract.hr_approval = True
        contract.status = "Approved"
        contract.save()

        send_notification_email(
            subject="Contract Fully Approved",
            message=f"Contract {contract.id} has been fully approved by HR {request.user}.",
            recipient_list=[
                contract.employee.email,
                contract.employee.supervisor.email,
            ],
        )
        messages.success(request, f"Contract {contract.id} fully approved by HR.")
        logger.info(f"Contract {contract.id} fully approved by HR {request.user}")
        return Response(
            {"message": "Contract fully approved by HR"}, status=status.HTTP_200_OK
        )
        
        
    @action(detail=False, methods=["get"])
    def notify_expiring_contracts(self, request):
        today = now().date()
        upcoming_expirations = Contract.objects.filter(
            end_date__in=[
                today + datetime.timedelta(days=60),
                today + datetime.timedelta(days=30),
                today + datetime.timedelta(days=1),
            ]
        )
        if not upcoming_expirations.exists():
            return Response(
                {"message": "No upcoming contract expiration."},
                status=status.HTTP_200_OK,
            )

        for contract in upcoming_expirations:
            days_remaining = (contract.end_date - today).days

            send_notification_email(
                subject="Contract Expiration Reminder",
                message=f"Reminder: Contract {contract.id} is expiring in {days_remaining} days.",
                recipient_list=[
                    contract.employee.email,
                    contract.employee.supervisor.email,
                ],
            )

            logger.info(f"Expiration reminder sent for Contract {contract.id}")
        return Response(
            {"message": "Expiration notifications sent."}, status=status.HTTP_200_OK
        )

def about_view(request):
    return render(request, "contracts/about.html")