from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta
from .models import Contract


def send_contract_expiry_notification():

    upcoming_expiry_date = now() + timedelta(days=30)
    expiring_contracts = Contract.objects.filter(expiry_date_lte=upcoming_expiry_date)

    for contract in expiring_contracts:
        subject = "Contract Expiry Notification"
        message = (
            f"Dear {contract.party_name}, \n\n"
            f"Your contract {contract.contract_name} will expire on {contract.expiry_date}. \n"
            f"Please take necessary action. \n\nBest Regards,\nContract Management Team"
        )
        send_mail(
            subject,
            message,
            "admin@AUBAR.com",
            [contract.party_email],
            fail_silently=False,
        )
        return f"Sent {expiring_contracts.count()} notifications."
