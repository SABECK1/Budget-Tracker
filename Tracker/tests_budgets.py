from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
from unittest.mock import patch

from Tracker.models import (
    Transaction,
    TransactionType,
    TransactionSubType,
    BankAccount,
    Budget,
)
from Tracker.serializers import BudgetSerializer


class BudgetModelTestCase(TestCase):
    """Test cases for the Budget model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create transaction types
        self.expense_type = TransactionType.objects.create(
            name="Expense", expense_factor=-1
        )
        self.income_type = TransactionType.objects.create(
            name="Income", expense_factor=1
        )

        # Create transaction subtypes
        self.food_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type, name="Food"
        )
        self.salary_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type, name="Salary"
        )

        # Create bank account
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            name="Test Account",
            iban="DE44500105170123456789",
            bic="COBADEFFXXX",
            bank_name="Test Bank",
            account_type="trade_republic",
        )

    def test_budget_creation(self):
        """Test basic budget creation"""
        budget = Budget.objects.create(
            user=self.user,
            name="Food Budget",
            limit_amount=500.00,
            period="monthly",
        )
        self.assertEqual(budget.name, "Food Budget")
        self.assertEqual(budget.limit_amount, 500.00)
        self.assertEqual(budget.period, "monthly")
        self.assertEqual(budget.user, self.user)

    def test_budget_with_transaction_types(self):
        """Test budget with transaction types"""
        budget = Budget.objects.create(
            user=self.user,
            name="Expense Budget",
            limit_amount=1000.00,
            period="weekly",
        )
        budget.transaction_types.add(self.expense_type)

        self.assertEqual(budget.transaction_types.count(), 1)
        self.assertIn(self.expense_type, budget.transaction_types.all())

    def test_budget_with_transaction_subtypes(self):
        """Test budget with transaction subtypes"""
        budget = Budget.objects.create(
            user=self.user,
            name="Food Budget",
            limit_amount=300.00,
            period="daily",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        self.assertEqual(budget.transaction_subtypes.count(), 1)
        self.assertIn(self.food_subtype, budget.transaction_subtypes.all())

    def test_budget_custom_period(self):
        """Test budget with custom period"""
        budget = Budget.objects.create(
            user=self.user,
            name="Custom Budget",
            limit_amount=200.00,
            period="custom",
            custom_period_days=15,
        )
        self.assertEqual(budget.period, "custom")
        self.assertEqual(budget.custom_period_days, 15)

    def test_get_period_timedelta(self):
        """Test period timedelta calculation"""
        budget = Budget.objects.create(
            user=self.user,
            name="Test Budget",
            limit_amount=100.00,
            period="daily",
        )

        self.assertEqual(budget.get_period_timedelta().days, 1)

        budget.period = "weekly"
        self.assertEqual(budget.get_period_timedelta().days, 7)

        budget.period = "monthly"
        self.assertEqual(budget.get_period_timedelta().days, 30)

        budget.period = "yearly"
        self.assertEqual(budget.get_period_timedelta().days, 365)

        budget.period = "custom"
        budget.custom_period_days = 45
        self.assertEqual(budget.get_period_timedelta().days, 45)

    def test_get_current_period_start_daily(self):
        """Test daily period start calculation"""
        budget = Budget.objects.create(
            user=self.user,
            name="Daily Budget",
            limit_amount=100.00,
            period="daily",
        )

        now = timezone.now()
        period_start = budget.get_current_period_start()

        self.assertEqual(period_start.year, now.year)
        self.assertEqual(period_start.month, now.month)
        self.assertEqual(period_start.day, now.day)
        self.assertEqual(period_start.hour, 0)
        self.assertEqual(period_start.minute, 0)
        self.assertEqual(period_start.second, 0)
        self.assertEqual(period_start.microsecond, 0)

    def test_get_current_period_start_weekly(self):
        """Test weekly period start calculation"""
        budget = Budget.objects.create(
            user=self.user,
            name="Weekly Budget",
            limit_amount=500.00,
            period="weekly",
        )

        now = timezone.now()
        period_start = budget.get_current_period_start()

        # Should be Monday (weekday 0)
        self.assertEqual(period_start.weekday(), 0)
        self.assertEqual(period_start.hour, 0)
        self.assertEqual(period_start.minute, 0)
        self.assertEqual(period_start.second, 0)
        self.assertEqual(period_start.microsecond, 0)

    def test_get_current_period_start_monthly(self):
        """Test monthly period start calculation"""
        budget = Budget.objects.create(
            user=self.user,
            name="Monthly Budget",
            limit_amount=1000.00,
            period="monthly",
        )

        now = timezone.now()
        period_start = budget.get_current_period_start()

        self.assertEqual(period_start.year, now.year)
        self.assertEqual(period_start.month, now.month)
        self.assertEqual(period_start.day, 1)
        self.assertEqual(period_start.hour, 0)
        self.assertEqual(period_start.minute, 0)
        self.assertEqual(period_start.second, 0)
        self.assertEqual(period_start.microsecond, 0)

    def test_get_current_period_start_yearly(self):
        """Test yearly period start calculation"""
        budget = Budget.objects.create(
            user=self.user,
            name="Yearly Budget",
            limit_amount=5000.00,
            period="yearly",
        )

        now = timezone.now()
        period_start = budget.get_current_period_start()

        self.assertEqual(period_start.year, now.year)
        self.assertEqual(period_start.month, 1)
        self.assertEqual(period_start.day, 1)
        self.assertEqual(period_start.hour, 0)
        self.assertEqual(period_start.minute, 0)
        self.assertEqual(period_start.second, 0)
        self.assertEqual(period_start.microsecond, 0)

    def test_get_current_period_start_custom(self):
        """Test custom period start calculation"""
        budget = Budget.objects.create(
            user=self.user,
            name="Custom Budget",
            limit_amount=200.00,
            period="custom",
            custom_period_days=10,
        )

        # Set creation time to a specific date
        budget.created_at = timezone.make_aware(datetime(2023, 1, 1, 12, 0, 0))
        budget.save()

        # Test with a date that should be in the same period
        test_time = timezone.make_aware(datetime(2023, 1, 5, 10, 0, 0))

        # Mock timezone.now() to return our test time
        with patch("django.utils.timezone.now", return_value=test_time):
            period_start = budget.get_current_period_start()

        self.assertEqual(period_start.year, 2023)
        self.assertEqual(period_start.month, 1)
        self.assertEqual(period_start.day, 1)
        self.assertEqual(period_start.hour, 0)
        self.assertEqual(period_start.minute, 0)
        self.assertEqual(period_start.second, 0)
        self.assertEqual(period_start.microsecond, 0)


class BudgetCalculationTestCase(TestCase):
    """Test cases for budget spending calculations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create transaction types
        self.expense_type = TransactionType.objects.create(
            name="Expense", expense_factor=-1
        )
        self.income_type = TransactionType.objects.create(
            name="Income", expense_factor=1
        )

        # Create transaction subtypes
        self.food_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type, name="Food"
        )
        self.salary_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type, name="Salary"
        )

        # Create bank account
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            name="Test Account",
            iban="DE44500105170123456789",
            bic="COBADEFFXXX",
            bank_name="Test Bank",
            account_type="trade_republic",
        )

        # Create budget
        self.budget = Budget.objects.create(
            user=self.user,
            name="Food Budget",
            limit_amount=100.00,
            period="monthly",
        )
        self.budget.transaction_subtypes.add(self.food_subtype)

    def create_transaction(self, amount, subtype, days_ago=0):
        """Helper method to create a transaction"""
        return Transaction.objects.create(
            user=self.user,
            amount=amount,
            quantity=1,
            isin="",
            transaction_subtype=subtype,
            bank_account=self.bank_account,
            created_at=timezone.now() - timedelta(days=days_ago),
        )

    def test_get_spent_amount_no_transactions(self):
        """Test spent amount with no transactions"""
        spent = self.budget.get_spent_amount()
        self.assertEqual(spent, 0)

    def test_get_spent_amount_with_expense_transactions(self):
        """Test spent amount with expense transactions"""
        # Create expense transactions
        self.create_transaction(-20.00, self.food_subtype, days_ago=1)
        self.create_transaction(-30.00, self.food_subtype, days_ago=2)
        self.create_transaction(-15.00, self.food_subtype, days_ago=3)

        spent = self.budget.get_spent_amount()
        self.assertEqual(spent, 65.00)  # 20 + 30 + 15

    def test_get_spent_amount_ignores_income_transactions(self):
        """Test that income transactions are ignored in spent calculation"""
        # Create expense and income transactions
        self.create_transaction(-20.00, self.food_subtype, days_ago=1)
        self.create_transaction(100.00, self.salary_subtype, days_ago=2)  # Income

        spent = self.budget.get_spent_amount()
        self.assertEqual(spent, 20.00)  # Only expense counted

    def test_get_spent_amount_respects_transaction_subtype_filter(self):
        """Test that only transactions with matching subtypes are counted"""
        other_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type, name="Other"
        )

        # Create transactions with different subtypes
        self.create_transaction(-20.00, self.food_subtype, days_ago=1)
        self.create_transaction(-30.00, other_subtype, days_ago=2)  # Different subtype

        spent = self.budget.get_spent_amount()
        self.assertEqual(spent, 20.00)  # Only food subtype counted

    def test_get_spent_amount_respects_transaction_type_filter(self):
        """Test that only transactions with matching types are counted"""
        budget_with_type = Budget.objects.create(
            user=self.user,
            name="Expense Budget",
            limit_amount=100.00,
            period="monthly",
        )
        budget_with_type.transaction_types.add(self.expense_type)

        # Create transactions with different types
        self.create_transaction(-20.00, self.food_subtype, days_ago=1)
        self.create_transaction(100.00, self.salary_subtype, days_ago=2)  # Income type

        spent = budget_with_type.get_spent_amount()
        self.assertEqual(spent, 20.00)  # Only expense type counted

    def test_get_spent_amount_respects_both_type_and_subtype(self):
        """Test that transactions must match both type and subtype"""
        other_type = TransactionType.objects.create(name="Other", expense_factor=-1)
        other_subtype = TransactionSubType.objects.create(
            transaction_type=other_type, name="Other"
        )

        budget_with_both = Budget.objects.create(
            user=self.user,
            name="Specific Budget",
            limit_amount=100.00,
            period="monthly",
        )
        budget_with_both.transaction_types.add(self.expense_type)
        budget_with_both.transaction_subtypes.add(self.food_subtype)

        # Create transactions
        self.create_transaction(-20.00, self.food_subtype, days_ago=1)  # Should count
        self.create_transaction(-30.00, other_subtype, days_ago=2)  # Wrong type
        self.create_transaction(-15.00, self.salary_subtype, days_ago=3)  # Wrong type

        spent = budget_with_both.get_spent_amount()
        self.assertEqual(spent, 20.00)  # Only matching type and subtype

    def test_get_remaining_amount(self):
        """Test remaining amount calculation"""
        # Create expense transactions
        self.create_transaction(-30.00, self.food_subtype, days_ago=1)
        self.create_transaction(-20.00, self.food_subtype, days_ago=2)

        remaining = self.budget.get_remaining_amount()
        self.assertEqual(remaining, 50.00)  # 100 - 50

    def test_get_spent_percentage(self):
        """Test spent percentage calculation"""
        # Create expense transactions
        self.create_transaction(-50.00, self.food_subtype, days_ago=1)
        self.create_transaction(-25.00, self.food_subtype, days_ago=2)

        percentage = self.budget.get_spent_percentage()
        self.assertEqual(percentage, 75.0)  # (75 / 100) * 100

    def test_get_spent_percentage_capped_at_100(self):
        """Test that spent percentage is capped at 100%"""
        # Create expense transactions exceeding limit
        self.create_transaction(-100.00, self.food_subtype, days_ago=1)
        self.create_transaction(-50.00, self.food_subtype, days_ago=2)

        percentage = self.budget.get_spent_percentage()
        self.assertEqual(percentage, 100.0)  # Capped at 100%

    def test_get_spent_percentage_zero_for_zero_limit(self):
        """Test spent percentage when limit is zero"""
        zero_budget = Budget.objects.create(
            user=self.user,
            name="Zero Budget",
            limit_amount=0.00,
            period="monthly",
        )
        zero_budget.transaction_subtypes.add(self.food_subtype)

        percentage = zero_budget.get_spent_percentage()
        self.assertEqual(percentage, 0.0)


class BudgetAPITestCase(APITestCase):
    """Test cases for Budget API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = APIClient()

        # Create transaction types
        self.expense_type = TransactionType.objects.create(
            name="Expense", expense_factor=-1
        )
        self.income_type = TransactionType.objects.create(
            name="Income", expense_factor=1
        )

        # Create transaction subtypes
        self.food_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type, name="Food"
        )
        self.salary_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type, name="Salary"
        )

    def test_budget_list_requires_authentication(self):
        """Test that budget list requires authentication"""
        response = self.client.get("/api/budgets/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_budget_list_authenticated(self):
        """Test budget list for authenticated user"""
        self.client.login(username="testuser", password="testpass123")

        # Create a budget
        Budget.objects.create(
            user=self.user,
            name="Test Budget",
            limit_amount=100.00,
            period="monthly",
        )

        response = self.client.get("/api/budgets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test Budget")

    def test_budget_create(self):
        """Test budget creation"""
        self.client.login(username="testuser", password="testpass123")

        data = {
            "name": "New Budget",
            "limit_amount": 200.00,
            "period": "weekly",
            "transaction_types": [self.expense_type.id],
            "transaction_subtypes": [self.food_subtype.id],
        }

        response = self.client.post("/api/budgets/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Budget")
        self.assertEqual(response.data["limit_amount"], "200.00")
        self.assertEqual(response.data["period"], "weekly")

        # Check that budget was created
        budget = Budget.objects.get(id=response.data["id"])
        self.assertEqual(budget.user, self.user)
        self.assertIn(self.expense_type, budget.transaction_types.all())
        self.assertIn(self.food_subtype, budget.transaction_subtypes.all())

    def test_budget_create_with_custom_period(self):
        """Test budget creation with custom period"""
        self.client.login(username="testuser", password="testpass123")

        data = {
            "name": "Custom Budget",
            "limit_amount": 150.00,
            "period": "custom",
            "custom_period_days": 14,
            "transaction_types": [self.expense_type.id],
        }

        response = self.client.post("/api/budgets/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["period"], "custom")
        self.assertEqual(response.data["custom_period_days"], 14)

    def test_budget_update(self):
        """Test budget update"""
        self.client.login(username="testuser", password="testpass123")

        # Create a budget
        budget = Budget.objects.create(
            user=self.user,
            name="Original Budget",
            limit_amount=100.00,
            period="monthly",
        )

        data = {
            "name": "Updated Budget",
            "limit_amount": 250.00,
            "period": "weekly",
        }

        response = self.client.patch(f"/api/budgets/{budget.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Budget")
        self.assertEqual(response.data["limit_amount"], "250.00")
        self.assertEqual(response.data["period"], "weekly")

    def test_budget_delete(self):
        """Test budget deletion"""
        self.client.login(username="testuser", password="testpass123")

        # Create a budget
        budget = Budget.objects.create(
            user=self.user,
            name="Budget to Delete",
            limit_amount=100.00,
            period="monthly",
        )

        response = self.client.delete(f"/api/budgets/{budget.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that budget was deleted
        self.assertFalse(Budget.objects.filter(id=budget.id).exists())

    def test_budget_user_isolation(self):
        """Test that users can only see their own budgets"""
        # Create second user
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        # Create budgets for both users
        Budget.objects.create(
            user=self.user,
            name="User1 Budget",
            limit_amount=100.00,
            period="monthly",
        )
        Budget.objects.create(
            user=user2,
            name="User2 Budget",
            limit_amount=200.00,
            period="weekly",
        )

        # Login as user1
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/api/budgets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "User1 Budget")

        # Login as user2
        self.client.logout()
        self.client.login(username="user2", password="testpass123")
        response = self.client.get("/api/budgets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "User2 Budget")

    def test_budget_serializer_calculations(self):
        """Test that budget serializer includes calculated fields"""
        self.client.login(username="testuser", password="testpass123")

        # Create a budget with transactions
        budget = Budget.objects.create(
            user=self.user,
            name="Test Budget",
            limit_amount=100.00,
            period="monthly",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        # Create bank account for transactions
        bank_account = BankAccount.objects.create(
            user=self.user,
            name="Test Account",
            iban="DE44500105170123456789",
            bic="COBADEFFXXX",
            bank_name="Test Bank",
            account_type="trade_republic",
        )

        # Create transactions
        Transaction.objects.create(
            user=self.user,
            amount=-30.00,
            quantity=1,
            isin="",
            transaction_subtype=self.food_subtype,
            bank_account=bank_account,
            created_at=timezone.now(),
        )
        Transaction.objects.create(
            user=self.user,
            amount=-20.00,
            quantity=1,
            isin="",
            transaction_subtype=self.food_subtype,
            bank_account=bank_account,
            created_at=timezone.now(),
        )

        response = self.client.get(f"/api/budgets/{budget.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check calculated fields
        self.assertEqual(response.data["spent_amount"], 50.0)
        self.assertEqual(response.data["remaining_amount"], 50.0)
        self.assertEqual(response.data["spent_percentage"], 50.0)
        self.assertIn("period_start", response.data)
        self.assertIn("period_end", response.data)


class BudgetPeriodLogicTestCase(TestCase):
    """Test cases for budget period logic and reset functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create transaction types and subtypes
        self.expense_type = TransactionType.objects.create(
            name="Expense", expense_factor=-1
        )
        self.food_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type, name="Food"
        )

        # Create bank account
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            name="Test Account",
            iban="DE44500105170123456789",
            bic="COBADEFFXXX",
            bank_name="Test Bank",
            account_type="trade_republic",
        )

    def create_transaction(self, amount, days_ago=0):
        """Helper method to create a transaction"""
        return Transaction.objects.create(
            user=self.user,
            amount=amount,
            quantity=1,
            isin="",
            transaction_subtype=self.food_subtype,
            bank_account=self.bank_account,
            created_at=timezone.now() - timedelta(days=days_ago),
        )

    def test_daily_budget_period_reset(self):
        """Test that daily budget periods reset correctly"""
        budget = Budget.objects.create(
            user=self.user,
            name="Daily Budget",
            limit_amount=50.00,
            period="daily",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        # Create transactions from yesterday
        self.create_transaction(-20.00, days_ago=1)
        self.create_transaction(-15.00, days_ago=1)

        # Create transactions from today
        self.create_transaction(-10.00, days_ago=0)

        spent = budget.get_spent_amount()
        self.assertEqual(spent, 10.00)  # Only today's transactions

    def test_weekly_budget_period_reset(self):
        """Test that weekly budget periods reset correctly"""
        budget = Budget.objects.create(
            user=self.user,
            name="Weekly Budget",
            limit_amount=200.00,
            period="weekly",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        # Create transactions from last week
        last_week = timezone.now() - timedelta(days=8)
        with timezone.override(timezone.get_current_timezone()):
            # Create transaction in last week
            Transaction.objects.create(
                user=self.user,
                amount=-50.00,
                quantity=1,
                isin="",
                transaction_subtype=self.food_subtype,
                bank_account=self.bank_account,
                created_at=last_week,
            )

        # Create transactions from this week
        self.create_transaction(-30.00, days_ago=2)
        self.create_transaction(-20.00, days_ago=1)

        spent = budget.get_spent_amount()
        self.assertEqual(spent, 50.00)  # Only this week's transactions

    def test_monthly_budget_period_reset(self):
        """Test that monthly budget periods reset correctly"""
        budget = Budget.objects.create(
            user=self.user,
            name="Monthly Budget",
            limit_amount=1000.00,
            period="monthly",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        # Create transactions from last month
        last_month = timezone.now() - timedelta(days=45)
        with timezone.override(timezone.get_current_timezone()):
            Transaction.objects.create(
                user=self.user,
                amount=-200.00,
                quantity=1,
                isin="",
                transaction_subtype=self.food_subtype,
                bank_account=self.bank_account,
                created_at=last_month,
            )

        # Create transactions from this month
        self.create_transaction(-100.00, days_ago=10)
        self.create_transaction(-50.00, days_ago=5)

        spent = budget.get_spent_amount()
        self.assertEqual(spent, 150.00)  # Only this month's transactions

    def test_yearly_budget_period_reset(self):
        """Test that yearly budget periods reset correctly"""
        budget = Budget.objects.create(
            user=self.user,
            name="Yearly Budget",
            limit_amount=5000.00,
            period="yearly",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        # Create transactions from last year
        last_year = timezone.now() - timedelta(days=400)
        with timezone.override(timezone.get_current_timezone()):
            Transaction.objects.create(
                user=self.user,
                amount=-1000.00,
                quantity=1,
                isin="",
                transaction_subtype=self.food_subtype,
                bank_account=self.bank_account,
                created_at=last_year,
            )

        # Create transactions from this year
        self.create_transaction(-500.00)
        self.create_transaction(-300.00)

        spent = budget.get_spent_amount()
        # Only this year's transactions should count
        self.assertEqual(spent, 800.00)

    def test_custom_budget_period_reset(self):
        """Test that custom budget periods reset correctly"""
        budget = Budget.objects.create(
            user=self.user,
            name="Custom Budget",
            limit_amount=300.00,
            period="custom",
            custom_period_days=10,
        )
        budget.transaction_subtypes.add(self.food_subtype)

        # Set creation time to a specific date
        budget.created_at = timezone.make_aware(datetime(2023, 1, 1, 12, 0, 0))
        budget.save()

        # Create transactions from previous period
        old_period = timezone.make_aware(datetime(2023, 1, 5, 10, 0, 0))
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,
            quantity=1,
            isin="",
            transaction_subtype=self.food_subtype,
            bank_account=self.bank_account,
            created_at=old_period,
        )

        # Create transactions from current period
        current_period = timezone.make_aware(datetime(2023, 1, 15, 10, 0, 0))
        Transaction.objects.create(
            user=self.user,
            amount=-50.00,
            quantity=1,
            isin="",
            transaction_subtype=self.food_subtype,
            bank_account=self.bank_account,
            created_at=current_period,
        )

        # Mock timezone.now() to return the current period time for testing
        with patch("django.utils.timezone.now", return_value=current_period):
            spent = budget.get_spent_amount()
            self.assertEqual(spent, 50.00)  # Only current period transactions


class BudgetSerializerTestCase(TestCase):
    """Test cases for BudgetSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create transaction types and subtypes
        self.expense_type = TransactionType.objects.create(
            name="Expense", expense_factor=-1
        )
        self.food_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type, name="Food"
        )

    def test_budget_serializer_fields(self):
        """Test that budget serializer includes all required fields"""
        budget = Budget.objects.create(
            user=self.user,
            name="Test Budget",
            limit_amount=100.00,
            period="monthly",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        serializer = BudgetSerializer(budget)
        data = serializer.data

        # Check all required fields are present
        required_fields = [
            "id",
            "name",
            "limit_amount",
            "period",
            "custom_period_days",
            "transaction_types",
            "transaction_subtypes",
            "spent_amount",
            "remaining_amount",
            "spent_percentage",
            "period_start",
            "period_end",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            self.assertIn(field, data)

        # Check calculated fields
        self.assertEqual(data["spent_amount"], 0.0)
        self.assertEqual(data["remaining_amount"], 100.0)
        self.assertEqual(data["spent_percentage"], 0.0)

    def test_budget_serializer_with_transactions(self):
        """Test budget serializer with actual transactions"""
        from Tracker.models import BankAccount

        # Create bank account
        bank_account = BankAccount.objects.create(
            user=self.user,
            name="Test Account",
            iban="DE44500105170123456789",
            bic="COBADEFFXXX",
            bank_name="Test Bank",
            account_type="trade_republic",
        )

        budget = Budget.objects.create(
            user=self.user,
            name="Test Budget",
            limit_amount=100.00,
            period="monthly",
        )
        budget.transaction_subtypes.add(self.food_subtype)

        # Create transactions
        Transaction.objects.create(
            user=self.user,
            amount=-30.00,
            quantity=1,
            isin="",
            transaction_subtype=self.food_subtype,
            bank_account=bank_account,
            created_at=timezone.now(),
        )
        Transaction.objects.create(
            user=self.user,
            amount=-20.00,
            quantity=1,
            isin="",
            transaction_subtype=self.food_subtype,
            bank_account=bank_account,
            created_at=timezone.now(),
        )

        serializer = BudgetSerializer(budget)
        data = serializer.data

        self.assertEqual(data["spent_amount"], 50.0)
        self.assertEqual(data["remaining_amount"], 50.0)
        self.assertEqual(data["spent_percentage"], 50.0)
        self.assertIn("period_start", data)
        self.assertIn("period_end", data)
