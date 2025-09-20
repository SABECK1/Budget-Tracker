from django.db import models
from django.contrib.auth.models import User

class TransactionType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Income", "Expense"
    description = models.TextField(blank=True)
    expense_factor = models.SmallIntegerField(choices=[(1, "Income"), (-1, "Expense")], default=-1)

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


# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     phone_number = models.CharField(max_length=20, blank=True)
#     pin = models.CharField(max_length=10, blank=True)

#     def __str__(self):
#         return f"{self.user.username}'s profile"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    transaction_subtype = models.ForeignKey(
        TransactionSubType, on_delete=models.PROTECT, related_name="transactions", default=1
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    isin = models.CharField(max_length=12, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.transaction_subtype} - {self.amount}"


class UserProvidedSymbol(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="provided_symbols")
    isin = models.CharField(max_length=12)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "isin")

    def __str__(self):
        return f"{self.user} provided {self.symbol} for {self.isin}"
