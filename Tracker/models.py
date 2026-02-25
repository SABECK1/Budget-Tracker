from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.db.models import Value, DecimalField
from datetime import timedelta


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
                Sum("outgoing_transactions__amount"),
                Value(0, output_field=DecimalField()),
                output_field=models.DecimalField(),
            )
        )


class BankAccountManager(models.Manager):
    def get_queryset(self):
        return BankAccountQuerySet(self.model, using=self._db)

    def get_balance(self, account_id):
        account = self.get_queryset().with_balance().filter(id=account_id).first()
        return account.balance if account else 0


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

    objects = BankAccountManager.from_queryset(BankAccountQuerySet)()

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
        on_delete=models.PROTECT,
        null=True,
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
        JournalEntry,
        related_name="lines",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.bank_account:
            # Find the first account belonging to THIS user
            default_account = BankAccount.objects.filter(user=self.user).first()
            if default_account:
                self.bank_account = default_account
            else:
                raise ValidationError(f"User {self.user} has no bank accounts defined.")

        super().save(*args, **kwargs)

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


class Budget(models.Model):
    PERIOD_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
        ("custom", "Custom"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    name = models.CharField(max_length=100)
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default="monthly")
    custom_period_days = models.PositiveIntegerField(null=True, blank=True)
    transaction_types = models.ManyToManyField(TransactionType, blank=True)
    transaction_subtypes = models.ManyToManyField(TransactionSubType, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    def get_period_timedelta(self):
        """Return the timedelta for the budget period."""
        if self.period == "daily":
            return timedelta(days=1)
        elif self.period == "weekly":
            return timedelta(weeks=1)
        elif self.period == "monthly":
            return timedelta(days=30)  # Approximate
        elif self.period == "yearly":
            return timedelta(days=365)  # Approximate
        elif self.period == "custom":
            return timedelta(days=self.custom_period_days or 1)
        return timedelta(days=30)

    def get_current_period_start(self):
        """Get the start date of the current budget period."""
        now = timezone.now()
        if self.period == "daily":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == "weekly":
            # Start of week (Monday)
            start_of_week = now - timedelta(days=now.weekday())
            return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == "monthly":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.period == "yearly":
            return now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif self.period == "custom":
            # For custom periods, we need to calculate based on the creation date
            period_start = self.created_at.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            days_since_start = (now.date() - period_start.date()).days
            periods_passed = days_since_start // (self.custom_period_days or 1)
            return period_start + timedelta(
                days=periods_passed * (self.custom_period_days or 1)
            )
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def get_current_period_end(self):
        """Get the end date of the current budget period."""
        return self.get_current_period_start() + self.get_period_timedelta()

    def get_spent_amount(self):
        """Calculate the total amount spent in the current period."""
        period_start = self.get_current_period_start()
        period_end = self.get_current_period_end()

        # Get transactions for this budget in the current period
        transactions = Transaction.objects.filter(
            user=self.user, created_at__gte=period_start, created_at__lt=period_end
        )

        # Filter by transaction types and subtypes if specified
        if self.transaction_types.exists():
            transactions = transactions.filter(
                transaction_subtype__transaction_type__in=self.transaction_types.all()
            )

        if self.transaction_subtypes.exists():
            transactions = transactions.filter(
                transaction_subtype__in=self.transaction_subtypes.all()
            )

        # Calculate total spent (only expenses, not income)
        total_spent = (
            transactions.filter(
                transaction_subtype__transaction_type__expense_factor=-1
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        return abs(total_spent)  # Return positive value for spent amount

    def get_remaining_amount(self):
        """Calculate the remaining budget amount."""
        return float(self.limit_amount) - float(self.get_spent_amount())

    def get_spent_percentage(self):
        """Calculate the percentage of budget spent."""
        if self.limit_amount == 0:
            return 0
        return min(
            100, (float(self.get_spent_amount()) / float(self.limit_amount)) * 100
        )
