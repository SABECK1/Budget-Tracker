from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce
from django.db.models import Sum


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


class BankAccountQuerySet(models.QuerySet):
    def with_balance(self):
        """Annotates each account with its current balance."""
        return self.annotate(
            balance=Coalesce(
                Sum("ledger_entries__amount"), 0, output_field=models.DecimalField()
            )
        )


class BankAccountManager(models.Manager):
    def get_queryset(self):
        return BankAccountQuerySet(self.model, using=self._db)

    def get_balance(self, account_id):
        return self.get_queryset().with_balance().get(id=account_id).balance


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

    objects = BankAccountManager()

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
