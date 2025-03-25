from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.utils.timezone import now
import datetime
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from contracts.models import Contract, Unit
from .serializers import ContractSerializer
from .forms import CustomUserCreationForm, ContractForm
from datetime import date, timedelta

logger = logging.getLogger(__name__)
User = get_user_model()


@login_required
def dashboard(request):
    """Dashboard displaying contract statistics"""
    today = date.today()
    expiring_soon_threshold = today + timedelta(days=30)

    active_contracts = Contract.objects.filter(end_date__gte=today)
    expiring_soon_contracts = Contract.objects.filter(end_date__gte=today, end_date__lte=expiring_soon_threshold)
    expired_contracts = Contract.objects.filter(end_date__lt=today)

    context = {
        'active_contracts': active_contracts,
        'expiring_soon_contracts': expiring_soon_contracts,
        'expired_contracts': expired_contracts
    }
    return render(request, "contracts/dashboard.html", context)


@login_required
def user_list(request):
    """List all users"""
    users = User.objects.all()
    return render(request, "contracts/user/user_list.html", {"users": users})


@login_required
def contract_list(request):
    """Display contracts based on user role and filter status"""
    user = request.user
    today = now().date()

    if user.role == "Admin":
        contracts = Contract.objects.all()
    elif user.role == "User":
        contracts = Contract.objects.filter(unit=user.unit)
    elif user.role == "Supervisor":
        contracts = Contract.objects.filter(employee__supervisor=user)
    else:
        contracts = Contract.objects.none()

    status_filter = request.GET.get("status")
    
    if status_filter == "active":
        contracts = contracts.filter(end_date__gt=today)
    elif status_filter == "expiring":
        contracts = contracts.filter(end_date__range=[today, today + timedelta(days=30)])
    elif status_filter == "expired":
        contracts = contracts.filter(end_date__lt=today)

    return render(request, "contracts/contract_list.html", {"contracts": contracts, "status": status_filter})


@login_required
def contract_edit(request, pk):
    """Allow only Admins and Supervisors to edit contracts"""
    contract = get_object_or_404(Contract, pk=pk)

    if request.user.role not in ["Admin", "Supervisor"]:
        raise PermissionDenied

    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, "Contract updated successfully.")
            return redirect("contract_list")
        else:
            messages.error(request, "Error updating contract.")
    else:
        form = ContractForm(instance=contract)

    return render(request, "contracts/contract_edit.html", {"form": form})


@login_required
def contract_create(request):
    """Create a new contract"""
    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)

            if not contract.staff_name:
                messages.error(request, "You must select a staff name before creating a contract.")
                return render(request, "contracts/contract_form.html", {"form": form})

            contract.name = f"{contract.staff_name}, {contract.title}, {contract.contract_type}"
            contract.save()
            messages.success(request, "Contract created successfully.")
            return redirect("contract_list")
        else:
            messages.error(request, "Error creating contract.")
    else:
        form = ContractForm()

    return render(request, "contracts/contract_form.html", {"form": form})


@login_required
def contract_detail(request, pk):
    """View contract details"""
    contract = get_object_or_404(Contract, id=pk)
    return render(request, "contracts/contract_detail.html", {"contract": contract})


@login_required
def delete_contract(request, pk):
    """Allow only Admins and Supervisors to delete contracts"""
    contract = get_object_or_404(Contract, pk=pk)

    if request.user.role not in ["Admin", "Supervisor"]:
        raise PermissionDenied

    if request.method == "POST":
        contract.delete()
        messages.success(request, "Contract deleted successfully.")
        return redirect("contract_list")

    return render(request, "contracts/contract_confirm_delete.html", {"contract": contract})


def send_notification_email(subject, message, recipient_list):
    """Send email notifications"""
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    except Exception as e:
        logger.error(f"Error sending email: {e}")


def login_view(request):
    """User login view"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("dashboard")
            else:
                messages.error(request, "Your account is inactive. Contact the administrator.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "contracts/login.html")


def logout_view(request):
    """User logout view"""
    logout(request)
    return redirect("login")


def signup(request):
    """User signup view"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = CustomUserCreationForm()

    return render(request, "contracts/signup.html", {"form": form})


class ContractViewSet(viewsets.ModelViewSet):
    """API ViewSet for managing contracts"""
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer

    @action(detail=True, methods=["post"])
    def approve_by_supervisor(self, request, pk=None):
        """Supervisor approves a contract"""
        contract = get_object_or_404(Contract, pk=pk)

        if request.user != contract.supervisor:
            return Response({"error": "Only the supervisor can approve."}, status=status.HTTP_403_FORBIDDEN)

        contract.supervisor_approval = True
        contract.save()

        send_notification_email(
            "Contract Approved by Supervisor",
            f"Contract {contract.id} has been approved by Supervisor {request.user}.",
            [contract.employee.email]
        )

        return Response({"message": "Contract approved by Supervisor"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve_by_hr(self, request, pk=None):
        """HR approves a contract"""
        contract = get_object_or_404(Contract, pk=pk)

        if not contract.supervisor_approval:
            return Response({"error": "Supervisor approval required first."}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role != "Admin":
            return Response({"error": "Only HR/Admin can approve."}, status=status.HTTP_403_FORBIDDEN)

        contract.hr_approval = True
        contract.status = "Approved"
        contract.save()

        send_notification_email(
            "Contract Fully Approved",
            f"Contract {contract.id} has been fully approved by HR {request.user}.",
            [contract.employee.email, contract.supervisor.email]
        )

        return Response({"message": "Contract fully approved by HR"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def notify_expiring_contracts(self, request):
        """Send notifications for contracts expiring soon"""
        today = now().date()
        expiring_contracts = Contract.objects.filter(
            end_date__in=[today + timedelta(days=60), today + timedelta(days=30), today + timedelta(days=1)]
        )

        for contract in expiring_contracts:
            days_remaining = (contract.end_date - today).days

            send_notification_email(
                "Contract Expiration Reminder",
                f"Reminder: Contract {contract.id} is expiring in {days_remaining} days.",
                [contract.employee.email, contract.supervisor.email]
            )

        return Response({"message": "Expiration notifications sent."}, status=status.HTTP_200_OK)


def about_view(request):
    """About page view"""
    return render(request, "contracts/about.html")
