from django.test import TestCase
from django.contrib.auth import get_user_model
from contracts.models import Contract, Unit
from datetime import date
from django.utils import timezone
from datetime import timedelta
from faker import Faker

fake = Faker()
User = get_user_model()  # Use Django's user model

class ContractTestCase(TestCase):
    
    def setUp(self):
        # Create staff user and staff profile
        user = get_user_model().objects.create_user(username="Dorothy", password="D0r0thy1234")
        
        self.unit = Unit.objects.create(name="HR Unit")
        # Create contract and associate it with the staff member
        self.staff_name = "Dorothy"  # Assuming you have a Unit model
        self.contract = Contract.objects.create(
            unit=self.unit,
            staff_name=self.staff_name, # Using the staff ForeignKey
            contract_type="regular",
            description="Contract for Dorothy",
            start_date=date(2025, 1, 9),
            end_date=date(2025, 6, 10),
            employee=user,
            renewal_count=0
        )
        # Create a contract for the staff member
        self.contract = Contract.objects.create(
            staff_name=self.staff_name,
            unit=self.unit,
            contract_type=fake.random_element(["Fixed-term", "Consultancy", "Regular contract"]),
            end_date=timezone.now().date() + timedelta(days=30),
        )

    def test_contract_is_associated_with_correct_staff(self):
        """Ensure the contract is linked to the right staff member"""
        contract = Contract.objects.get(id=self.contract.id)
        self.assertEqual(contract.staff_name, "Dorothy")

    def test_staff_belongs_to_correct_unit(self):
        """Check if staff member is in the right unit"""
        self.assertEqual(self.contract.unit.name, "HR Unit")
