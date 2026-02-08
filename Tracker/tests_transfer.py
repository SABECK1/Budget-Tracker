from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.test import APITestCase
from rest_framework import status
from .models import (
    Transaction,
    TransactionType,
    TransactionSubType,
    BankAccount,
    JournalEntry,
)
from .services import LedgerService
import json


class TransferTransactionTestCase(APITestCase):
    """Test cases for Transfer transactions using LedgerService"""

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create bank accounts for testing
        self.account1 = BankAccount.objects.create(
            user=self.user,
            name="Checking Account",
            iban="DE44500105170123456789",
            bic="COBADEFFXXX",
            bank_name="Test Bank 1",
        )

        self.account2 = BankAccount.objects.create(
            user=self.user,
            name="Savings Account",
            iban="DE44500105170987654321",
            bic="COBADEFFXXX",
            bank_name="Test Bank 2",
        )

        # Create transaction types
        self.transfer_type, _ = TransactionType.objects.get_or_create(
            name="Transfer",
            defaults={
                "description": "Internal transfers between accounts",
                "expense_factor": 0,
            },
        )

        self.transfer_subtype, _ = TransactionSubType.objects.get_or_create(
            transaction_type=self.transfer_type,
            name="Account Transfer",
            defaults={"description": "Transfer between user accounts"},
        )

    def test_create_transfer_transaction_success(self):
        """Test successful creation of transfer transaction"""
        amount = 100.00
        note = "Monthly transfer"

        # Create transfer using LedgerService
        journal = LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=amount,
            note=note,
        )

        # Verify journal entry was created
        self.assertIsInstance(journal, JournalEntry)
        self.assertEqual(journal.user, self.user)
        self.assertEqual(
            journal.description,
            f"Transfer: {self.account1.name} -> {self.account2.name}",
        )

        # Verify two transactions were created
        transactions = Transaction.objects.filter(journal_entry=journal)
        self.assertEqual(transactions.count(), 2)

        # Verify debit transaction (negative amount)
        debit_transaction = transactions.filter(bank_account=self.account1).first()
        self.assertIsNotNone(debit_transaction)
        self.assertEqual(debit_transaction.amount, -amount)
        self.assertEqual(debit_transaction.transaction_subtype, self.transfer_subtype)
        self.assertEqual(debit_transaction.note, note)

        # Verify credit transaction (positive amount)
        credit_transaction = transactions.filter(bank_account=self.account2).first()
        self.assertIsNotNone(credit_transaction)
        self.assertEqual(credit_transaction.amount, amount)
        self.assertEqual(credit_transaction.transaction_subtype, self.transfer_subtype)
        self.assertEqual(credit_transaction.note, note)

    def test_create_transfer_transaction_zero_amount(self):
        """Test that zero amount raises ValueError"""
        with self.assertRaises(ValueError) as context:
            LedgerService.create_transfer_transaction(
                user=self.user,
                from_account=self.account1,
                to_account=self.account2,
                amount=0,
            )
        self.assertEqual(str(context.exception), "Transfer amount must be positive.")

    def test_create_transfer_transaction_negative_amount(self):
        """Test that negative amount raises ValueError"""
        with self.assertRaises(ValueError) as context:
            LedgerService.create_transfer_transaction(
                user=self.user,
                from_account=self.account1,
                to_account=self.account2,
                amount=-50.00,
            )
        self.assertEqual(str(context.exception), "Transfer amount must be positive.")

    def test_create_transfer_transaction_different_users(self):
        """Test that accounts from different users raises ValueError"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        other_account = BankAccount.objects.create(
            user=other_user,
            name="Other Account",
            iban="DE44500105171111111111",
            bic="COBADEFFXXX",
            bank_name="Other Bank",
        )

        with self.assertRaises(ValueError) as context:
            LedgerService.create_transfer_transaction(
                user=self.user,
                from_account=self.account1,
                to_account=other_account,
                amount=100.00,
            )
        self.assertEqual(
            str(context.exception), "Both accounts must belong to the same user."
        )

    def test_create_transfer_transaction_same_account(self):
        """Test that transfer to same account raises ValueError"""
        with self.assertRaises(ValueError) as context:
            LedgerService.create_transfer_transaction(
                user=self.user,
                from_account=self.account1,
                to_account=self.account1,
                amount=100.00,
            )
        self.assertEqual(
            str(context.exception),
            "Source and destination accounts cannot be the same.",
        )

    def test_create_transfer_transaction_rollback_on_error(self):
        """Test that transaction is rolled back if an error occurs"""
        # Create a transfer with valid data first
        amount = 50.00
        journal = LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=amount,
        )

        # Verify initial state
        initial_journal_count = JournalEntry.objects.count()
        initial_transaction_count = Transaction.objects.count()

        # Try to create a transfer with invalid data (should fail)
        try:
            LedgerService.create_transfer_transaction(
                user=self.user,
                from_account=self.account1,
                to_account=self.account2,
                amount=-100.00,  # Invalid negative amount
            )
        except ValueError:
            pass  # Expected to fail

        # Verify no new records were created due to rollback
        self.assertEqual(JournalEntry.objects.count(), initial_journal_count)
        self.assertEqual(Transaction.objects.count(), initial_transaction_count)

    def test_create_transfer_transaction_with_existing_types(self):
        """Test that existing transaction types are reused"""
        # Create transfer first time
        LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=100.00,
        )

        # Get counts after first creation
        type_count_after_first = TransactionType.objects.filter(name="Transfer").count()
        subtype_count_after_first = TransactionSubType.objects.filter(
            name="Account Transfer"
        ).count()

        # Create transfer second time
        LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account2,
            to_account=self.account1,
            amount=50.00,
        )

        # Verify types were not duplicated
        type_count_after_second = TransactionType.objects.filter(
            name="Transfer"
        ).count()
        subtype_count_after_second = TransactionSubType.objects.filter(
            name="Account Transfer"
        ).count()

        self.assertEqual(type_count_after_first, type_count_after_second)
        self.assertEqual(subtype_count_after_first, subtype_count_after_second)

    def test_transfer_transaction_balance(self):
        """Test that transfer transactions maintain double-entry balance"""
        amount = 250.00

        # Create transfer
        journal = LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=amount,
        )

        # Get all transactions for this journal
        transactions = Transaction.objects.filter(journal_entry=journal)

        # Calculate total amount (should be 0 in double-entry system)
        total_amount = sum(transaction.amount for transaction in transactions)
        self.assertEqual(total_amount, 0)

        # Verify individual transaction amounts
        amounts = [transaction.amount for transaction in transactions]
        self.assertIn(-amount, amounts)
        self.assertIn(amount, amounts)

    def test_multiple_transfers_same_accounts(self):
        """Test multiple transfers between same accounts"""
        amounts = [100.00, 50.00, 25.00]

        for amount in amounts:
            journal = LedgerService.create_transfer_transaction(
                user=self.user,
                from_account=self.account1,
                to_account=self.account2,
                amount=amount,
            )

            # Verify each transfer creates its own journal entry
            self.assertIsInstance(journal, JournalEntry)
            self.assertEqual(journal.user, self.user)

            # Verify each transfer has exactly 2 transactions
            transactions = Transaction.objects.filter(journal_entry=journal)
            self.assertEqual(transactions.count(), 2)

        # Verify total number of journal entries
        total_journals = JournalEntry.objects.filter(user=self.user).count()
        self.assertEqual(total_journals, len(amounts))

        # Verify total number of transactions
        total_transactions = Transaction.objects.filter(user=self.user).count()
        self.assertEqual(total_transactions, len(amounts) * 2)

    def test_transfer_transaction_with_custom_note(self):
        """Test transfer transaction with custom note"""
        amount = 75.00
        custom_note = "Rent payment to savings"

        journal = LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=amount,
            note=custom_note,
        )

        # Verify note is stored in both transactions
        transactions = Transaction.objects.filter(journal_entry=journal)
        for transaction in transactions:
            self.assertEqual(transaction.note, custom_note)

    def test_transfer_transaction_atomicity(self):
        """Test that transfer creation is atomic"""
        amount = 100.00

        # Count initial records
        initial_journals = JournalEntry.objects.count()
        initial_transactions = Transaction.objects.count()

        # Create transfer
        journal = LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=amount,
        )

        # Verify exactly one journal and two transactions were created
        self.assertEqual(JournalEntry.objects.count(), initial_journals + 1)
        self.assertEqual(Transaction.objects.count(), initial_transactions + 2)

        # Verify the journal and transactions are properly linked
        transactions = Transaction.objects.filter(journal_entry=journal)
        self.assertEqual(transactions.count(), 2)

    def test_transfer_transaction_user_isolation(self):
        """Test that transfers are isolated by user"""
        # Create second user and their accounts
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )
        account3 = BankAccount.objects.create(
            user=user2,
            name="User2 Account 1",
            iban="DE44500105172222222222",
            bic="COBADEFFXXX",
            bank_name="User2 Bank 1",
        )
        account4 = BankAccount.objects.create(
            user=user2,
            name="User2 Account 2",
            iban="DE44500105173333333333",
            bic="COBADEFFXXX",
            bank_name="User2 Bank 2",
        )

        # Create transfers for both users
        LedgerService.create_transfer_transaction(
            user=self.user,
            from_account=self.account1,
            to_account=self.account2,
            amount=100.00,
        )

        LedgerService.create_transfer_transaction(
            user=user2,
            from_account=account3,
            to_account=account4,
            amount=50.00,
        )

        # Verify each user only sees their own transfers
        user1_journals = JournalEntry.objects.filter(user=self.user)
        user2_journals = JournalEntry.objects.filter(user=user2)

        self.assertEqual(user1_journals.count(), 1)
        self.assertEqual(user2_journals.count(), 1)

        user1_transactions = Transaction.objects.filter(user=self.user)
        user2_transactions = Transaction.objects.filter(user=user2)

        self.assertEqual(user1_transactions.count(), 2)
        self.assertEqual(user2_transactions.count(), 2)
