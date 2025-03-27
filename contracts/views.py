from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.utils.timezone import now
from datetime import date, timedelta
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_user_model
from contracts.models import Contract, Unit
from .serializers import ContractSerializer
from  contracts.forms import CustomUserCreationForm, ContractForm

logger = logging.getLogger(__name__)
User = get_user_model()

@login_required
def dashboard(request):
    """Dashboard displaying contract statistics for the logged-in user"""
    today = date.today()
    expiring_soon_threshold = today + timedelta(days=30)
    
    if not request.user.is_authenticated:
        return redirect("login")
    print(f"Logged-in user: {request.user}")
    
    user_contracts= Contract.objects.filter(employee=request.user)
    print(f"Contracts for {request.user}: {list(user_contracts)}")

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
def contract_list(request):
    """Display only contracts the user is allowed to see"""
    user = request.user
    today = now().date()

    if user.role == "Admin":
        contracts = Contract.objects.all()
    elif user.role == "Supervisor":
        # Supervisors see contracts of employees they supervise
        contracts = Contract.objects.filter(supervisor=user)
    else:  # Regular Users should only see their own contracts
        contracts = Contract.objects.filter(employee=user)

    # Optional: Filter by contract status
    status_filter = request.GET.get("status")
    if status_filter == "active":
        contracts = contracts.filter(end_date__gt=today)
    elif status_filter == "expiring":
        contracts = contracts.filter(end_date__range=[today, today + timedelta(days=30)])
    elif status_filter == "expired":
        contracts = contracts.filter(end_date__lt=today)

    return render(request, "contracts/contract_list.html", {"contracts": contracts, "status": status_filter})




def signup(request):
    """User registration view"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect("dashboard")  # Redirect to the dashboard after signup
        else:
            print("FORM ERRORS:", form.errors)
    else:
        form = CustomUserCreationForm()

    return render(request, "contracts/signup.html", {"form": form})


@login_required
def contract_detail(request, pk):
    """View contract details (restricted access)"""
    contract = get_object_or_404(Contract, id=pk)

    if request.user.role == "Admin" or contract.employee == request.user or contract.supervisor == request.user:
        return render(request, "contracts/contract_detail.html", {"contract": contract})
    else:
        raise PermissionDenied("You are not authorized to view this contract.")


class ContractViewSet(viewsets.ModelViewSet):
    """API ViewSet for managing contracts"""
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer

    def get_queryset(self):
        """Limit contracts visibility based on user role"""
        user = self.request.user

        if user.role == "Admin":
            return Contract.objects.all()
        elif user.role == "Supervisor":
            return Contract.objects.filter(supervisor=user)
        else:
            return Contract.objects.filter(employee=user)

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
    
    
    
@login_required
def contract_edit(request, pk):
    """Edit an existing contract"""
    contract = get_object_or_404(Contract, id=pk)

    # Check if the user has permission to edit
    if request.user.role not in ["Admin", "Supervisor"] and contract.employee != request.user:
        raise PermissionDenied("You are not authorized to edit this contract.")

    if request.method == "POST":
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, "Contract updated successfully!")
            return redirect("contract_detail", pk=pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContractForm(instance=contract)

    return render(request, "contracts/contract_edit.html", {"form": form, "contract": contract})


@login_required
def contract_create(request):
    """Create a new contract"""
    if request.method == "POST":
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.created_by = request.user  # Assign creator
            contract.save()
            return redirect("contract_list")  # Redirect to contracts list
    else:
        form = ContractForm()

    return render(request, "contracts/contract_form.html", {"form": form})




def user_list(request):
    """Display a list of users (Only Admins can see this)"""
    if request.user.role != "Admin":
        raise PermissionDenied("You are not authorized to view this page.")

    users = User.objects.all()
    return render(request, "contracts/user/user_list.html", {"users": users})


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


def delete_contract(request, contract_id):
    """Delete a contract by ID"""
    contract = get_object_or_404(Contract, id=contract_id)
    
    if request.method == "POST":
        contract.delete()
        return redirect("contract_list")  # Redirect to contract list after deletion

    return render(request, "contracts/contract_confirm_delete.html", {"contract": contract})

def logout_view(request):
    """User logout view"""
    logout(request)
    return redirect("login")


def about_view(request):
    """About page view"""
    return render(request, "contracts/about.html")
