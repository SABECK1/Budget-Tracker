from django.contrib.auth.models import Group, User
from Tracker import models
from rest_framework import serializers

# serializers.py


class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    bank_account = serializers.PrimaryKeyRelatedField(
        queryset=models.BankAccount.objects.all(), required=True
    )

    class Meta:
        fields = ["file", "bank_account"]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class TransactionTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.TransactionType
        fields = ["url", "id", "name", "description", "expense_factor"]


class TransactionSubtypeSerializer(serializers.ModelSerializer):
    transaction_type_name = serializers.CharField(
        source="transaction_type.name", read_only=True
    )

    class Meta:
        model = models.TransactionSubType
        fields = [
            "id",
            "transaction_type",
            "transaction_type_name",
            "name",
            "description",
        ]


class BankAccountSerializer(serializers.HyperlinkedModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = models.BankAccount
        fields = [
            "url",
            "id",
            "name",
            "iban",
            "bic",
            "bank_name",
            "account_type",
            "balance",
        ]

    def get_balance(self, obj):
        """Get the current balance for this bank account using BankAccountManager."""
        return obj.__class__.objects.get_balance(obj.id)


class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    transaction_subtype = serializers.PrimaryKeyRelatedField(
        queryset=models.TransactionSubType.objects.all()
    )
    bank_account = serializers.PrimaryKeyRelatedField(
        queryset=models.BankAccount.objects.all(), allow_null=True, required=True
    )
    bank_account_name = serializers.CharField(
        source="bank_account.name", read_only=True
    )

    class Meta:
        model = models.Transaction
        fields = [
            "id",
            "transaction_subtype",
            "bank_account",
            "bank_account_name",
            "amount",
            "created_at",
            "note",
            "isin",
            "quantity",
            "fee",
            "tax",
        ]
