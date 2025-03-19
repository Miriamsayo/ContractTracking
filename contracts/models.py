from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.timezone import now
from django.core.mail import send_mail


class UserRoles(models.TextChoices):
    ADMIN = "Admin", "Admin"
    DEVELOPER = "Developer", "Developer"
    USER = "User", "User"
    SUPERVISOR = "Supervisor", "Supervisor"


class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=20, choices=UserRoles.choices, default=UserRoles.USER
    )
    unit = models.ForeignKey(
        "contracts.Unit", on_delete=models.SET_NULL, null=True, blank=True
    )
    supervisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
    )

    groups = models.ManyToManyField(
        "auth.Group", related_name="customuser_groups", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="customuser_permissions", blank=True
    )

    def is_admin_or_supervisor(self):
        """Check if the user is an Admin or Supervisor."""
        return self.role in {UserRoles.ADMIN, UserRoles.SUPERVISOR}

    def __str__(self):
        return f"{self.username} - {self.role}"


class Unit(models.Model):
    name = models.CharField(max_length=100, default="Unknown")

    def __str__(self):
        return self.name


class ContractType(models.TextChoices):
    REGULAR = "Regular Contract", "Regular Contract"
    SHORT_TERM = "Short-term Contract", "Short-term Contract"
    FIXED_TERM = "Fixed-term Contract", "Fixed-term Contract"
    CONSULTANCY = "Consultancy", "Consultancy"


class Contract(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    staff_name = models.CharField(max_length=255, default="Unknown")
    title = models.CharField(max_length=200)
    contract_type = models.CharField(
        max_length=50, choices=ContractType.choices, default=ContractType.REGULAR
    )
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    file = models.FileField(upload_to="contracts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    renewal_count = models.PositiveIntegerField(default=0)

    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_contracts",
    )

    supervisor_approval = models.BooleanField(default=False)
    hr_approval = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Expired", "Expired"),
        ("Pending Renewal", "Pending Renewal"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")

    contract_name = models.CharField(
        max_length=255, blank=True
    )

    def  get_status(self):
        today = now().date()
        
        if self.end_date < today:
            return "Expired"
        elif (self.end_date - today).days <= 30:
            return "Pending Renewal"
        return "Active"
    def can_edit(self, user):
        """Only Admin, Supervisor, or the contract's supervisor can edit."""
        return user.is_superuser or user.role in ["Admin", "Supervisor"] or user == self.supervisor
    
    def save(self, *args, **kwargs):
        """Auto-update contract_name and status before saving."""
        self.status = self.get_status()  
        self.contract_name = f"{self.staff_name} - {self.title} ({self.contract_type})"
        super().save(*args, **kwargs)

    def can_delete(self, user):
        """Only Admin or Supervisor can delete the contract."""
        return user.is_superuser or user.role in ["Admin", "Supervisor"]

    def __str__(self):
        return f"{self.staff_name} - {self.title} ({self.contract_type})"


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    contract = models.ForeignKey(
        Contract, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    sent_at = models.DateTimeField(default=now)
    recipient_email = models.EmailField()
    created_at = models.DateTimeField(default=now)

    def send_email_notification(self):
        """Send an email notification to the recipient."""
        if self.recipient and self.recipient.email:
            send_mail(
                subject="Contract Notification",
                message=self.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.recipient.email],
                fail_silently=True,
            )

    def save(self, *args, **kwargs):
        """Auto-send email when notification is created."""
        super().save(*args, **kwargs)
        self.send_email_notification()

    def __str__(self):
        return f"Notification for {self.recipient.username if self.recipient else 'Unknown'} - {self.contract}"
