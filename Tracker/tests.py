from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Transaction, TransactionType, TransactionSubType
import io
import csv

class CSVUploadTestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create transaction types
        self.income_type = TransactionType.objects.create(
            name="Income",
            expense_factor=1
        )
        self.expense_type = TransactionType.objects.create(
            name="Expense",
            expense_factor=-1
        )

        # Create transaction subtypes
        self.inflow_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Inflow"
        )
        self.outflow_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Outflow"
        )
        self.buy_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Buy"
        )
        self.sell_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Sell"
        )
        self.not_assigned_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Not assigned"
        )

    def create_csv_content(self, rows):
        """Helper method to create CSV content from rows"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        for row in rows:
            writer.writerow(row)
        return output.getvalue()

    def test_csv_upload_requires_authentication(self):
        """Test that CSV upload requires authentication"""
        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'Test Transaction', '-100.00', 'Test Note', '', '', '0.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_csv_upload_successful(self):
        """Test successful CSV upload with valid data"""
        self.client.login(username='testuser', password='testpass123')

        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'Test Transaction', '-100.00', 'Test Note', '', '', '0.00', '0.00'],
            ['2023-01-02', 'Income Transaction', '200.00', 'Income Note', '', '', '0.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Imported 2 rows', response.data['status'])

        # Check that transactions were created
        transactions = Transaction.objects.filter(user=self.user)
        self.assertEqual(transactions.count(), 2)

        # Check first transaction (expense)
        expense_transaction = transactions.filter(amount=-100.00).first()
        self.assertEqual(expense_transaction.transaction_subtype, self.outflow_subtype)
        self.assertEqual(expense_transaction.note, 'Test Note')

        # Check second transaction (income)
        income_transaction = transactions.filter(amount=200.00).first()
        self.assertEqual(income_transaction.transaction_subtype, self.inflow_subtype)
        self.assertEqual(income_transaction.note, 'Income Note')

    def test_csv_upload_with_stock_transaction(self):
        """Test CSV upload with stock transactions"""
        self.client.login(username='testuser', password='testpass123')

        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'Stock Buy', '-150.00', 'AAPL Purchase', 'US0378331005', '10', '5.00', '0.00'],
            ['2023-01-02', 'Stock Sell', '160.00', 'AAPL Sale', 'US0378331005', '-10', '5.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        transactions = Transaction.objects.filter(user=self.user)
        self.assertEqual(transactions.count(), 2)

        # Check buy transaction
        buy_transaction = transactions.filter(amount=-150.00).first()
        self.assertEqual(buy_transaction.transaction_subtype, self.buy_subtype)
        self.assertEqual(buy_transaction.isin, 'US0378331005')
        self.assertEqual(buy_transaction.quantity, 10)

        # Check sell transaction
        sell_transaction = transactions.filter(amount=160.00).first()
        self.assertEqual(sell_transaction.transaction_subtype, self.sell_subtype)
        self.assertEqual(sell_transaction.isin, 'US0378331005')
        self.assertEqual(sell_transaction.quantity, -10)

    def test_csv_upload_automatic_subtype_assignment_by_note(self):
        """Test that new transactions get subtype from existing transactions with same note"""
        self.client.login(username='testuser', password='testpass123')

        # Create an existing transaction with a specific subtype
        custom_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Custom Expense"
        )
        existing_transaction = Transaction.objects.create(
            user=self.user,
            amount=-50.00,
            note="Recurring Payment",
            transaction_subtype=custom_subtype
        )

        # Upload CSV with transaction having same note
        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'New Transaction', '-75.00', 'Recurring Payment', '', '', '0.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that new transaction got the same subtype as existing one
        new_transaction = Transaction.objects.filter(user=self.user, amount=-75.00).first()
        self.assertEqual(new_transaction.transaction_subtype, custom_subtype)

    def test_csv_upload_default_subtype_when_no_matching_note(self):
        """Test that transactions get default subtype when no matching note exists"""
        self.client.login(username='testuser', password='testpass123')

        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'New Transaction', '-100.00', 'Unique Note', '', '', '0.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that transaction got default subtype (Outflow for negative amount)
        new_transaction = Transaction.objects.filter(user=self.user, amount=-100.00).first()
        self.assertEqual(new_transaction.transaction_subtype, self.outflow_subtype)

    def test_csv_upload_handles_empty_rows(self):
        """Test that CSV upload handles empty rows gracefully"""
        self.client.login(username='testuser', password='testpass123')

        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'Valid Transaction', '-100.00', 'Test Note', '', '', '0.00', '0.00'],
            [],  # Empty row
            ['2023-01-02', 'Another Transaction', '50.00', 'Another Note', '', '', '0.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Imported 2 rows', response.data['status'])

        transactions = Transaction.objects.filter(user=self.user)
        self.assertEqual(transactions.count(), 2)

    def test_csv_upload_with_missing_columns(self):
        """Test CSV upload with rows having fewer columns"""
        self.client.login(username='testuser', password='testpass123')

        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note'],  # Missing ISIN, Quantity, Fee, Tax
            ['2023-01-01', 'Test Transaction', '-100.00', 'Test Note']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        transaction = Transaction.objects.filter(user=self.user).first()
        self.assertEqual(transaction.amount, -100.00)
        self.assertEqual(transaction.note, 'Test Note')
        self.assertEqual(transaction.isin, '')  # Should be empty
        self.assertEqual(transaction.quantity, 0.0)  # Should be 0.0
        self.assertEqual(transaction.fee, 0.0)  # Should be 0.0
        self.assertEqual(transaction.tax, 0.0)  # Should be 0.0

    def test_csv_upload_invalid_file(self):
        """Test CSV upload with invalid file"""
        self.client.login(username='testuser', password='testpass123')

        # Try to upload without file
        response = self.client.post('/api/upload-csv/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
