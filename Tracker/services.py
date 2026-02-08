from django.db import transaction
from .models import JournalEntry, Transaction


class LedgerService:
    @staticmethod
    @transaction.atomic
    def transfer_funds(user, from_account, to_account, amount, note=""):
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        # 1. Create the Journal Entry (The "Why")
        journal = JournalEntry.objects.create(
            user=user, description=f"Transfer: {from_account.name} -> {to_account.name}"
        )

        # 2. Debit the source account (The "From")
        Transaction.objects.create(
            journal_entry=journal, bank_account=from_account, amount=-amount, note=note
        )

        # 3. Credit the destination account (The "To")
        Transaction.objects.create(
            journal_entry=journal, bank_account=to_account, amount=amount, note=note
        )

        return journal
