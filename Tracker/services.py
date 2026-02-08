from django.db import transaction
from .models import JournalEntry, Transaction, TransactionType, TransactionSubType


class LedgerService:
    @staticmethod
    @transaction.atomic
    def create_transfer_transaction(
        user,
        from_account,
        to_account,
        amount,
        note="",
        isin="",
        quantity=None,
        fee=None,
        tax=None,
    ):
        """
        Create a transfer transaction using double-entry bookkeeping.
        This creates two transactions: one negative (debit) and one positive (credit).

        Args:
            user: The user creating the transaction
            from_account: Source bank account (will be debited)
            to_account: Destination bank account (will be credited)
            amount: Positive amount to transfer
            note: Optional note for the transaction
            isin: Optional ISIN for the transfer
            quantity: Optional quantity for the transfer
            fee: Optional fee for the transfer
            tax: Optional tax for the transfer

        Returns:
            JournalEntry: The created journal entry containing both transactions
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        if from_account.user != user or to_account.user != user:
            raise ValueError("Both accounts must belong to the same user.")

        if from_account == to_account:
            raise ValueError("Source and destination accounts cannot be the same.")

        # Get or create Transfer transaction type and subtype
        transfer_type, _ = TransactionType.objects.get_or_create(
            name="Transfer",
            defaults={
                "description": "Internal transfers between accounts",
                "expense_factor": 0,
            },
        )

        transfer_subtype, _ = TransactionSubType.objects.get_or_create(
            transaction_type=transfer_type,
            name="Account Transfer",
            defaults={"description": "Transfer between user accounts"},
        )

        # Create the Journal Entry (The "Why")
        journal = JournalEntry.objects.create(
            user=user,
            description=f"Transfer: {from_account.name} -> {to_account.name}",
        )

        # 2. Debit the source account (The "From") - Negative amount
        Transaction.objects.create(
            user=user,
            journal_entry=journal,
            bank_account=from_account,
            amount=-amount,
            note=note,
            isin=isin,
            quantity=quantity,
            fee=fee,
            tax=tax,
            transaction_subtype=transfer_subtype,
        )

        # 3. Credit the destination account (The "To") - Positive amount
        Transaction.objects.create(
            user=user,
            journal_entry=journal,
            bank_account=to_account,
            amount=amount,
            note=note,
            isin=isin,
            quantity=quantity,
            fee=fee,
            tax=tax,
            transaction_subtype=transfer_subtype,
        )

        return journal
