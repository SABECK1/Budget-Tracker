#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Budget_Tracker.settings')
django.setup()

from Tracker.models import Transaction, TransactionType, TransactionSubType

def main():
    print("Starting database setup...")

    # Delete all transactions
    print("Deleting all transactions...")
    deleted_count = Transaction.objects.all().delete()
    print(f"Deleted {deleted_count[0]} transactions")

    # Define transaction types and their subtypes
    transaction_data = {
        "Income": {
            "factor": 1,  # Income
            "description": "Money coming in",
            "subtypes": [
                "Salary",
                "Freelance",
                "Business Income",
                "Investment Returns",
                "Rental Income",
                "Other Income"
            ]
        },
        "Expense": {
            "factor": -1,  # Expense
            "description": "Money going out",
            "subtypes": [
                "Food & Dining",
                "Transportation",
                "Housing",
                "Utilities",
                "Healthcare",
                "Entertainment",
                "Shopping",
                "Education",
                "Travel",
                "Insurance",
                "Personal Care",
                "Other Expenses"
            ]
        },
        "Investment": {
            "factor": -1,  # Can be both, but default to expense for tracking
            "description": "Investment related transactions",
            "subtypes": [
                "Stock/ETF/Bond Purchase",
                "Real Estate",
                "Retirement Accounts",
                "Other Investments"
            ]
        },
        "Transfer": {
            "factor": 0,  # Neutral
            "description": "Money transfers between accounts",
            "subtypes": [
                "Bank Transfer",
                "Credit Card Payment",
                "Account Transfer",
                "Wire Transfer"
            ]
        },
        "Not assigned": {
            "factor": -1,
            "description": "Default category for unassigned transactions",
            "subtypes": [
                "Not assigned"
            ]
        }
    }

    # Create transaction types and subtypes
    for type_name, type_data in transaction_data.items():
        print(f"\nCreating TransactionType: {type_name}")

        # Create TransactionType
        transaction_type, created = TransactionType.objects.get_or_create(
            name=type_name,
            defaults={
                'description': type_data["description"],
                'expense_factor': type_data["factor"]
            }
        )

        if created:
            print(f"✓ Created TransactionType: {transaction_type}")
        else:
            print(f"⚠ TransactionType '{type_name}' already exists")

        # Create subtypes
        for subtype_name in type_data["subtypes"]:
            subtype, created = TransactionSubType.objects.get_or_create(
                transaction_type=transaction_type,
                name=subtype_name,
                defaults={
                    'description': f'{subtype_name} under {type_name}'
                }
            )

            if created:
                print(f"  ✓ Created subtype: {subtype}")
            else:
                print(f"  ⚠ Subtype '{subtype_name}' already exists")

    print("\n" + "="*50)
    print("Database setup completed successfully!")
    print("="*50)

    # Show summary
    total_types = TransactionType.objects.count()
    total_subtypes = TransactionSubType.objects.count()
    total_transactions = Transaction.objects.count()

    print(f"\nSummary:")
    print(f"- Transaction Types: {total_types}")
    print(f"- Transaction Subtypes: {total_subtypes}")
    print(f"- Transactions: {total_transactions}")

if __name__ == '__main__':
    main()
