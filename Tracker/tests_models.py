from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from Tracker.models import (
    TransactionType,
    TransactionSubType,
    JournalEntry,
    BankAccount,
    Transaction,
    UserProvidedSymbol,
    Budget,
)


class TransactionTypeTestCase(TestCase):
    """Test cases for TransactionType model"""

    def test_transaction_type_creation(self):
        """Test creating a transaction type"""
        transaction_type = TransactionType.objects.create(
            name="Income", description="Money received", expense_factor=1
        )

        self.assertEqual(transaction_type.name, "Income")
        self.assertEqual(transaction_type.description, "Money received")
        self.assertEqual(transaction_type.expense_factor, 1)
        self.assertEqual(str(transaction_type), "Income (+)")

    def test_transaction_type_expense_creation(self):
        """Test creating an expense transaction type"""
        transaction_type = TransactionType.objects.create(
            name="Expense", description="Money spent", expense_factor=-1
        )

        self.assertEqual(transaction_type.name, "Expense")
        self.assertEqual(transaction_type.expense_factor, -1)
        self.assertEqual(str(transaction_type), "Expense (-)")

    def test_transaction_type_unique_name(self):
        """Test that transaction type names must be unique"""
        TransactionType.objects.create(
            name="Income", description="Money received", expense_factor=1
        )

        with self.assertRaises(Exception):
            TransactionType.objects.create(
                name="Income", description="Duplicate", expense_factor=-1
            )


class TransactionSubTypeTestCase(TestCase):
    """Test cases for TransactionSubType model"""

    def setUp(self):
        self.income_type = TransactionType.objects.create(
            name="Income", description="Money received", expense_factor=1
        )
        self.expense_type = TransactionType.objects.create(
            name="Expense", description="Money spent", expense_factor=-1
        )

    def test_transaction_subtype_creation(self):
        """Test creating a transaction subtype"""
        subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Salary",
            description="Monthly salary payment",
        )

        self.assertEqual(subtype.transaction_type, self.income_type)
        self.assertEqual(subtype.name, "Salary")
        self.assertEqual(subtype.description, "Monthly salary payment")
        self.assertEqual(str(subtype), "Income - Salary")

    def test_transaction_subtype_get_expense_factor(self):
        """Test getting expense factor from parent transaction type"""
        income_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Salary",
            description="Monthly salary payment",
        )

        expense_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Food",
            description="Grocery expenses",
        )

        self.assertEqual(income_subtype.get_expense_factor(), 1)
        self.assertEqual(expense_subtype.get_expense_factor(), -1)

    def test_transaction_subtype_unique_together(self):
        """Test that subtype names must be unique within a transaction type"""
        TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Salary",
            description="Monthly salary payment",
        )

        with self.assertRaises(Exception):
            TransactionSubType.objects.create(
                transaction_type=self.income_type,
                name="Salary",
                description="Duplicate salary",
            )


class JournalEntryTestCase(TestCase):
    """Test cases for JournalEntry model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
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

        self.transaction_type = TransactionType.objects.create(
            name="Expense", description="Money spent", expense_factor=-1
        )

        self.transaction_subtype = TransactionSubType.objects.create(
            transaction_type=self.transaction_type,
            name="Food",
            description="Grocery expenses",
        )

    def test_journal_entry_creation(self):
        """Test creating a journal entry"""
        journal = JournalEntry.objects.create(
            description="Test transfer", user=self.user
        )

        self.assertEqual(journal.description, "Test transfer")
        self.assertEqual(journal.user, self.user)
        self.assertTrue(journal.created_at)
        self.assertEqual(str(journal), f"Test transfer ({journal.created_at.date()})")

    def test_journal_entry_is_balanced(self):
        """Test journal entry balance validation"""
        journal = JournalEntry.objects.create(
            description="Balanced entry", user=self.user
        )

        # Create balanced transactions (sum = 0)
        Transaction.objects.create(user=self.user, amount=100.00, journal_entry=journal)
        Transaction.objects.create(
            user=self.user, amount=-100.00, journal_entry=journal
        )

        self.assertTrue(journal.is_balanced())

    def test_journal_entry_not_balanced(self):
        """Test journal entry that is not balanced"""
        journal = JournalEntry.objects.create(
            description="Unbalanced entry", user=self.user
        )

        # Create unbalanced transactions (sum != 0)
        Transaction.objects.create(user=self.user, amount=100.00, journal_entry=journal)
        Transaction.objects.create(user=self.user, amount=-50.00, journal_entry=journal)

        self.assertFalse(journal.is_balanced())

    def test_journal_entry_clean_validation(self):
        """Test journal entry clean method validation"""
        journal = JournalEntry.objects.create(
            description="Unbalanced entry", user=self.user
        )

        # Create unbalanced transactions
        Transaction.objects.create(user=self.user, amount=100.00, journal_entry=journal)

        with self.assertRaises(ValidationError):
            journal.clean()


class BankAccountTestCase(TestCase):
    """Test cases for BankAccount model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.transaction_type = TransactionType.objects.create(
            name="Expense", description="Money spent", expense_factor=-1
        )

        self.transaction_subtype = TransactionSubType.objects.create(
            transaction_type=self.transaction_type,
            name="Food",
            description="Grocery expenses",
        )

    def test_bank_account_creation(self):
        """Test creating a bank account"""
        account = BankAccount.objects.create(
            user=self.user,
            name="Checking Account",
            iban="DE44500105170123456789",
            bic="COBADEFFXXX",
            bank_name="Test Bank",
            account_type="volksbank",
        )

        self.assertEqual(account.user, self.user)
        self.assertEqual(account.name, "Checking Account")
        self.assertEqual(account.iban, "DE44500105170123456789")
        self.assertEqual(account.bic, "COBADEFFXXX")
        self.assertEqual(account.bank_name, "Test Bank")
        self.assertEqual(account.account_type, "volksbank")
        self.assertEqual(str(account), f"{self.user} - Checking Account")

    def test_bank_account_with_balance(self):
        """Test bank account balance calculation"""
        account = BankAccount.objects.create(user=self.user, name="Savings Account")

        # Create some transactions
        Transaction.objects.create(user=self.user, bank_account=account, amount=100.00)
        Transaction.objects.create(user=self.user, bank_account=account, amount=-50.00)

        # Get account with balance annotation
        account_with_balance = BankAccount.objects.with_balance().get(id=account.id)
        self.assertEqual(account_with_balance.balance, 50.00)

    def test_bank_account_manager_get_balance(self):
        """Test BankAccountManager get_balance method"""
        account = BankAccount.objects.create(user=self.user, name="Test Account")

        # Create some transactions
        Transaction.objects.create(user=self.user, bank_account=account, amount=200.00)
        Transaction.objects.create(user=self.user, bank_account=account, amount=-75.00)

        balance = BankAccount.objects.get_balance(account.id)
        self.assertEqual(balance, 125.00)


class TransactionTestCase(TestCase):
    """Test cases for Transaction model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.account = BankAccount.objects.create(user=self.user, name="Test Account")
        self.transaction_type = TransactionType.objects.create(
            name="Expense", description="Money spent", expense_factor=-1
        )
        self.transaction_subtype = TransactionSubType.objects.create(
            transaction_type=self.transaction_type,
            name="Food",
            description="Grocery expenses",
        )

    def test_transaction_creation(self):
        """Test creating a transaction"""
        transaction = Transaction.objects.create(
            user=self.user,
            bank_account=self.account,
            transaction_subtype=self.transaction_subtype,
            amount=-50.00,
            note="Grocery shopping",
            isin="",
            quantity=None,
            fee=None,
            tax=None,
        )

        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.bank_account, self.account)
        self.assertEqual(transaction.transaction_subtype, self.transaction_subtype)
        self.assertEqual(transaction.amount, -50.00)
        self.assertEqual(transaction.note, "Grocery shopping")
        self.assertEqual(transaction.isin, "")
        self.assertIsNone(transaction.quantity)
        self.assertIsNone(transaction.fee)
        self.assertIsNone(transaction.tax)
        self.assertTrue(transaction.created_at)
        self.assertEqual(str(transaction), f"{self.user} - Expense - Food - -50.0")

    def test_transaction_save_without_bank_account(self):
        """Test transaction save assigns default bank account"""
        # Create transaction without bank_account
        transaction = Transaction(
            user=self.user, transaction_subtype=self.transaction_subtype, amount=-25.00
        )
        transaction.save()

        # Should automatically assign the first account for the user
        self.assertEqual(transaction.bank_account, self.account)

    def test_transaction_save_without_bank_account_no_accounts(self):
        """Test transaction save fails when user has no bank accounts"""
        # Create user without bank accounts
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        # Try to create transaction without bank account
        transaction = Transaction(
            user=user2, transaction_subtype=self.transaction_subtype, amount=-25.00
        )

        with self.assertRaises(ValidationError):
            transaction.save()

    def test_transaction_with_isin(self):
        """Test transaction with ISIN for stock transactions"""
        transaction = Transaction.objects.create(
            user=self.user,
            bank_account=self.account,
            transaction_subtype=self.transaction_subtype,
            amount=-100.00,
            isin="DE0007100000",
            quantity=10.0,
            fee=5.0,
            tax=2.0,
        )

        self.assertEqual(transaction.isin, "DE0007100000")
        self.assertEqual(transaction.quantity, 10.0)
        self.assertEqual(transaction.fee, 5.0)
        self.assertEqual(transaction.tax, 2.0)


class UserProvidedSymbolTestCase(TestCase):
    """Test cases for UserProvidedSymbol model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_user_provided_symbol_creation(self):
        """Test creating a user provided symbol"""
        symbol = UserProvidedSymbol.objects.create(
            user=self.user, isin="DE0007100000", symbol="AIRG", name="Airbus SE"
        )

        self.assertEqual(symbol.user, self.user)
        self.assertEqual(symbol.isin, "DE0007100000")
        self.assertEqual(symbol.symbol, "AIRG")
        self.assertEqual(symbol.name, "Airbus SE")
        self.assertTrue(symbol.created_at)
        self.assertEqual(str(symbol), f"{self.user} provided AIRG for DE0007100000")

    def test_user_provided_symbol_unique_together(self):
        """Test that ISIN must be unique per user"""
        UserProvidedSymbol.objects.create(
            user=self.user, isin="DE0007100000", symbol="AIRG", name="Airbus SE"
        )

        with self.assertRaises(Exception):
            UserProvidedSymbol.objects.create(
                user=self.user, isin="DE0007100000", symbol="AIRG2", name="Airbus SE 2"
            )


class BudgetTestCase(TestCase):
    """Test cases for Budget model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.account = BankAccount.objects.create(user=self.user, name="Test Account")
        self.transaction_type = TransactionType.objects.create(
            name="Expense", description="Money spent", expense_factor=-1
        )
        self.transaction_subtype = TransactionSubType.objects.create(
            transaction_type=self.transaction_type,
            name="Food",
            description="Grocery expenses",
        )

    def test_budget_creation(self):
        """Test creating a budget"""
        budget = Budget.objects.create(
            user=self.user, name="Food Budget", limit_amount=500.00, period="monthly"
        )

        self.assertEqual(budget.user, self.user)
        self.assertEqual(budget.name, "Food Budget")
        self.assertEqual(budget.limit_amount, 500.00)
        self.assertEqual(budget.period, "monthly")
        self.assertIsNone(budget.custom_period_days)
        self.assertTrue(budget.created_at)
        self.assertTrue(budget.updated_at)
        self.assertEqual(str(budget), f"Food Budget - {self.user.username}")

    def test_budget_get_period_timedelta(self):
        """Test getting period timedelta for different periods"""
        budget_daily = Budget.objects.create(
            user=self.user, name="Daily", limit_amount=100.00, period="daily"
        )
        budget_weekly = Budget.objects.create(
            user=self.user, name="Weekly", limit_amount=100.00, period="weekly"
        )
        budget_monthly = Budget.objects.create(
            user=self.user, name="Monthly", limit_amount=100.00, period="monthly"
        )
        budget_yearly = Budget.objects.create(
            user=self.user, name="Yearly", limit_amount=100.00, period="yearly"
        )
        budget_custom = Budget.objects.create(
            user=self.user,
            name="Custom",
            limit_amount=100.00,
            period="custom",
            custom_period_days=15,
        )

        self.assertEqual(budget_daily.get_period_timedelta(), timedelta(days=1))
        self.assertEqual(budget_weekly.get_period_timedelta(), timedelta(weeks=1))
        self.assertEqual(budget_monthly.get_period_timedelta(), timedelta(days=30))
        self.assertEqual(budget_yearly.get_period_timedelta(), timedelta(days=365))
        self.assertEqual(budget_custom.get_period_timedelta(), timedelta(days=15))

    def test_budget_get_current_period_start(self):
        """Test getting current period start date"""
        budget = Budget.objects.create(
            user=self.user, name="Test", limit_amount=100.00, period="monthly"
        )

        now = timezone.now()
        period_start = budget.get_current_period_start()

        # For monthly period, should start at beginning of month
        self.assertEqual(period_start.day, 1)
        self.assertEqual(period_start.hour, 0)
        self.assertEqual(period_start.minute, 0)
        self.assertEqual(period_start.second, 0)
        self.assertEqual(period_start.microsecond, 0)

    def test_budget_get_current_period_end(self):
        """Test getting current period end date"""
        budget = Budget.objects.create(
            user=self.user, name="Test", limit_amount=100.00, period="monthly"
        )

        period_start = budget.get_current_period_start()
        period_end = budget.get_current_period_end()

        # End should be start + period timedelta
        self.assertEqual(period_end, period_start + budget.get_period_timedelta())

    def test_budget_get_spent_amount(self):
        """Test calculating spent amount in current period"""
        budget = Budget.objects.create(
            user=self.user, name="Test", limit_amount=100.00, period="monthly"
        )

        # Create transactions in current period
        Transaction.objects.create(
            user=self.user, amount=-50.00, transaction_subtype=self.transaction_subtype
        )
        Transaction.objects.create(
            user=self.user, amount=-30.00, transaction_subtype=self.transaction_subtype
        )

        # Create transaction outside current period (last month)
        last_month = timezone.now() - timedelta(days=40)
        Transaction.objects.create(
            user=self.user,
            amount=-20.00,
            created_at=last_month,
            transaction_subtype=self.transaction_subtype,
        )

        spent = budget.get_spent_amount()
        self.assertEqual(spent, 80.00)  # Only current period transactions

    def test_budget_get_remaining_amount(self):
        """Test calculating remaining budget amount"""
        budget = Budget.objects.create(
            user=self.user, name="Test", limit_amount=100.00, period="monthly"
        )

        # Create transactions
        Transaction.objects.create(
            user=self.user, amount=-30.00, transaction_subtype=self.transaction_subtype
        )

        remaining = budget.get_remaining_amount()
        self.assertEqual(remaining, 70.00)

    def test_budget_get_spent_percentage(self):
        """Test calculating spent percentage"""
        budget = Budget.objects.create(
            user=self.user, name="Test", limit_amount=100.00, period="monthly"
        )

        # Create transactions
        Transaction.objects.create(
            user=self.user, amount=-50.00, transaction_subtype=self.transaction_subtype
        )

        percentage = budget.get_spent_percentage()
        self.assertEqual(percentage, 50.0)

        # Test with overspending (should cap at 100%)
        Transaction.objects.create(
            user=self.user, amount=-75.00, transaction_subtype=self.transaction_subtype
        )

        percentage = budget.get_spent_percentage()
        self.assertEqual(percentage, 100.0)
