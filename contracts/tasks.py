from celery import shared_task
from datetime import datetime, timedelta
from django.utils.timezone import now
from .models import Contract
from django.core.mail import send_mail

@shared_task
def update_contract_statuses():
    """
    This task automatically updates contract statuses based on expiration dates.
    It runs periodically and updates contracts that are about to expire.
    """
    today = now().date()
    contracts = Contract.objects.all()

    for contract in contracts:
        contract.update_status()
        contract.save()

    return f"Updated {contracts.count()} contracts."

@shared_task
def check_contract_expiry():
    """Check contracts nearing expiration and send notifications."""
    today = datetime.today().date()
    reminder_dates = [today + timedelta(days=60), today + timedelta(days=30), today + timedelta(days=1)]

    expiring_contracts = Contract.objects.filter(expiration_date__in=reminder_dates)

    for contract in expiring_contracts:
        send_mail(
            subject=f"Contract Expiry Reminder: {contract.staff_name} - {contract.contract_type}",
            message=f"Reminder: The contract for {contract.staff_name} ({contract.contract_type}) is expiring on {contract.expiration_date}.",
            from_email="noreply@yourcompany.com",
            recipient_list=[contract.supervisor.email],  # Adjust as necessary
        )

    return f"Checked {len(expiring_contracts)} contracts for expiration."
