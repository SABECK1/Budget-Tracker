import os
import sys
import django
from datetime import datetime
from django.utils import timezone
import csv

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Budget_Tracker.settings')
django.setup()

from django.core.management.base import BaseCommand, CommandError
from Tracker.models import Transaction, TransactionSubType
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Import example transactions from example_transactions.csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            required=True,
            help='Email of the user to import transactions for',
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise CommandError(f"User with email '{user_email}' does not exist")

        # Delete existing transactions for this user to avoid duplicates
        deleted_count = Transaction.objects.filter(user=user).delete()
        self.stdout.write(f"Deleted {deleted_count[0]} existing transactions for user {user_email}")

        # Import new transactions
        csv_path = 'example_transactions.csv'
        if not os.path.exists(csv_path):
            raise CommandError("example_transactions.csv not found")

        with open(csv_path, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader, None)  # Skip header row

            imported_count = 0
            for row in reader:
                if not row:  # skip empty lines
                    continue

                try:
                    # Parse row data, strip whitespace
                    row = [cell.strip() for cell in row]
                    datetime_from_iso = datetime.fromisoformat(row[0])
                    creation_datetime = timezone.make_aware(datetime_from_iso)

                    isin = row[4] if len(row) > 4 and row[4] else ""
                    is_stock = bool(isin)
                    amount = float(row[2]) if row[2] else 0.0
                    note = row[3] if len(row) > 3 and row[3] else ""

                    # Get subtype
                    transaction_subtype = self.get_transaction_subtype(is_stock, amount)

                    # Helper function to safely convert to float
                    def safe_float(value):
                        try:
                            return float(value) if value else 0.0
                        except (ValueError, TypeError):
                            return 0.0

                    # Create transaction
                    Transaction.objects.create(
                        user=user,
                        created_at=creation_datetime,
                        transaction_subtype=transaction_subtype,
                        amount=amount,
                        note=note,
                        isin=isin,
                        quantity=safe_float(row[5] if len(row) > 5 else None),
                        fee=safe_float(row[6] if len(row) > 6 else None),
                        tax=safe_float(row[7] if len(row) > 7 else None),
                    )
                    imported_count += 1
                except Exception as e:
                    self.stdout.write(f"Error importing row {row}: {e}")
                    continue

            self.stdout.write(f"Successfully imported {imported_count} transactions")

    def get_transaction_subtype(self, is_stock, amount):
        try:
            if not is_stock:  # Regular transaction
                if amount < 0:
                    return TransactionSubType.objects.get(name="Outflow")
                else:
                    return TransactionSubType.objects.get(name="Inflow")
            else:  # Stock transaction
                if amount < 0:
                    return TransactionSubType.objects.get(name="Stock/ETF/Bond Purchase")
                else:
                    return TransactionSubType.objects.get(name="Investment Returns")
        except TransactionSubType.DoesNotExist:
            # Fallback
            return TransactionSubType.objects.get(name="Not assigned")
