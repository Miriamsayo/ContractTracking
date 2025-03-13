from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings
from django.core.mail import send_mail

# User Roles
class UserRoles(models.TextChoices):
    ADMIN = 'Admin', 'Admin'
    DEVELOPER = 'Developer', 'Developer'
    USER = 'User', 'User'
    SUPERVISOR = 'Supervisor', 'Supervisor'

# Custom User Model
class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRoles.choices,
        default=UserRoles.USER
    )
    unit = models.ForeignKey(
        'contracts.Unit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name="customuser_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True
    )
    
    def is_supervisor(self):
        """Check if the user is assigned the Supervisor role."""
        return self.role == UserRoles.SUPERVISOR
    
    def __str__(self):
        return f"{self.username} - {self.role}"

# Unit Model
class Unit(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, default="Unknown")

    def __str__(self):
        return self.name

# Contract Types
class ContractType(models.TextChoices):
    REGULAR = 'Regular Contract', 'Regular Contract'
    SHORT_TERM = 'Short-term Contract', 'Short-term Contract'
    FIXED_TERM = 'Fixed-term Contract', 'Fixed-term Contract'
    CONSULTANCY = 'Consultancy', 'Consultancy'

# Contract Model
class Contract(models.Model):
    unit = models.ForeignKey('Unit', on_delete=models.CASCADE)
    staff_name = models.CharField(max_length=255, blank=True, null=True, default="Unknown")
    title = models.CharField(max_length=200)
    contract_type = models.CharField(
        max_length=50,
        choices=ContractType.choices,
        default=ContractType.REGULAR
    )
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    file = models.FileField(upload_to='contracts/')
    created_at = models.DateTimeField(auto_now_add=True)
    contract_name = models.CharField(max_length=255, default="Unnamed Staff - No Title - Contract Type Unknown")
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    renewal_count = models.PositiveIntegerField(default=0)
    
    supervisor_approval = models.BooleanField(default=False)
    hr_approval = models.BooleanField(default=False)
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Expired', 'Expired'),
        ('Pending Renewal', 'Pending Renewal'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active'
    )

    def __str__(self):
        return f"{self.staff_name} - {self.title} ({self.contract_type})"

    def renew_contract(self, new_end_date):
        """Renews the contract if the new end date is valid."""
        if new_end_date > self.end_date:
            self.end_date = new_end_date
            self.renewal_count += 1
            self.save()
        else:
            raise ValueError("New end date must be later than the current end date.")

    def get_expiry_status(self):
        """Determines contract expiry status and updates it accordingly."""
        today = now().date()
        days_to_expiry = (self.end_date - today).days

        if days_to_expiry <= 0:
            self.status = "Expired"
        elif days_to_expiry < 60:
            self.status = "Pending Renewal"
        else:
            self.status = "Active"

        self.save()
        return self.status  

# Notification Model
class Notification(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="notifications")
    recipient_email = models.EmailField()
    recipient_phone = models.CharField(max_length=15, blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField() 
    notification_type = models.CharField(max_length=100)

    def __str__(self):
        return f"Notification for {self.contract.title} sent on {self.sent_at}"

    def send_email_notification(self):
        """Sends an email notification for contract expiry alerts."""
        if self.recipient_email:
            send_mail(
                subject=f"Contract Expiry Alert: {self.contract.staff_name} - {self.contract.title}",
                message=self.message,
                from_email="noreply@AU.com",
                recipient_list=[self.recipient_email],
                fail_silently=False,
            )
