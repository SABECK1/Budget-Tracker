from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class TransactionType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Income", "Expense"
    description = models.TextField(blank=True)
    expense_factor = models.SmallIntegerField(
        choices=[(1, "Income"), (-1, "Expense")], default=-1
    )

    def __str__(self):
        return f"{self.name} ({'+' if self.expense_factor == 1 else '-'})"


class TransactionSubType(models.Model):
    transaction_type = models.ForeignKey(
        TransactionType, on_delete=models.CASCADE, related_name="subtypes"
    )
    name = models.CharField(max_length=50)  # e.g., "Food", "Salary", "Rent"
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("transaction_type", "name")

    def __str__(self):
        return f"{self.transaction_type.name} - {self.name}"

    def get_expense_factor(self):
        """Return the parent TransactionType instance of this subtype."""
        return self.transaction_type.expense_factor


class JournalEntry(models.Model):
    """Groups multiple transactions together (e.g., a transfer or a split)."""

    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def is_balanced(self):
        """The sum of all lines must be 0 in a double-entry system."""
        # Sum of all lines should satisfy: \sum_{i=1}^{n} amount_i = 0
        total = sum(line.amount for line in self.lines.all())
        return total == 0

    def clean(self):
        if not self.is_balanced():
            raise ValidationError("The ledger entries do not balance to zero.")

    def __str__(self):
        return f"{self.description} ({self.created_at.date()})"


# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     phone_number = models.CharField(max_length=20, blank=True)
#     pin = models.CharField(max_length=10, blank=True)

#     def __str__(self):
#         return f"{self.user.username}'s profile"


class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ("trade_republic", "Trade Republic"),
        ("volksbank", "Volksbank"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    name = models.CharField(
        max_length=100, help_text="Name of the account (e.g., Checking, Savings)"
    )
    iban = models.CharField(
        max_length=34, blank=True, help_text="International Bank Account Number"
    )
    bic = models.CharField(max_length=11, blank=True, help_text="Bank Identifier Code")
    bank_name = models.CharField(
        max_length=100, blank=True, help_text="Name of the bank"
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        blank=True,
        help_text="Type of bank account for CSV processing",
    )

    def __str__(self):
        return f"{self.user} - {self.name}"


class Transaction(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_subtype = models.ForeignKey(
        TransactionSubType,
        on_delete=models.PROTECT,
        related_name="transactions",
        default=1,
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=False,
        blank=False,
        related_name="outgoing_transactions",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)
    isin = models.CharField(max_length=12, blank=True)
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    journal_entry = models.ForeignKey(
        JournalEntry, related_name="lines", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.user} - {self.transaction_subtype} - {self.amount}"


class UserProvidedSymbol(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="provided_symbols"
    )
    isin = models.CharField(max_length=12)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "isin")

    def __str__(self):
        return f"{self.user} provided {self.symbol} for {self.isin}"


class TransferService:
    @staticmethod
    def execute_transfer(user, from_account, to_account, amount, note=""):
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        # Ensure the whole block succeeds or fails together
        with transaction.atomic():
            # 1. Create the parent record
            journal = JournalEntry.objects.create(
                user=user,
                description=f"Transfer from {from_account.name} to {to_account.name}",
            )

            # 2. The Outbound Line (Negative)
            Transaction.objects.create(
                journal_entry=journal,
                bank_account=from_account,
                amount=-amount,
                note=note,
            )

            # 3. The Inbound Line (Positive)
            Transaction.objects.create(
                journal_entry=journal, bank_account=to_account, amount=amount, note=note
            )

            # Optional: Add a fee here if needed in the future

        return journal
