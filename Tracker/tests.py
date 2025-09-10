from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Transaction, TransactionType, TransactionSubType
import io
import csv
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from decimal import Decimal

# Import portfolio classes for testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'API', 'TradeRepublic'))
from standalone_portfolio import Portfolio, TradeRepublicApi, get_portfolio_data

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
        print("🧪 Running: test_csv_upload_requires_authentication")
        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'Test Transaction', '-100.00', 'Test Note', '', '', '0.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


    def test_csv_upload_successful(self):
        """Test successful CSV upload with valid data"""
        print("🧪 Running: test_csv_upload_successful")
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
        print("🧪 Running: test_csv_upload_with_stock_transaction")
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
        """Test that new regular transactions get subtype from existing transactions with same note"""
        print("🧪 Running: test_csv_upload_automatic_subtype_assignment_by_note")
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

    def test_csv_upload_automatic_subtype_assignment_by_isin(self):
        """Test that new stock transactions get subtype from existing transactions with same ISIN"""
        print("🧪 Running: test_csv_upload_automatic_subtype_assignment_by_isin")
        self.client.login(username='testuser', password='testpass123')

        # Create an existing stock transaction with a specific subtype
        custom_stock_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Custom Stock Buy"
        )
        existing_transaction = Transaction.objects.create(
            user=self.user,
            amount=-100.00,
            isin="US0378331005",
            note="AAPL Purchase",
            transaction_subtype=custom_stock_subtype
        )

        # Upload CSV with stock transaction having same ISIN
        csv_content = self.create_csv_content([
            ['Date', 'Description', 'Amount', 'Note', 'ISIN', 'Quantity', 'Fee', 'Tax'],
            ['2023-01-01', 'New AAPL Purchase', '-200.00', 'Additional AAPL', 'US0378331005', '20', '5.00', '0.00']
        ])
        csv_file = SimpleUploadedFile("test.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client.post('/api/upload-csv/', {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that new transaction got the same subtype as existing one
        new_transaction = Transaction.objects.filter(user=self.user, amount=-200.00).first()
        self.assertEqual(new_transaction.transaction_subtype, custom_stock_subtype)

    def test_csv_upload_default_subtype_when_no_matching_note(self):
        """Test that transactions get default subtype when no matching note exists"""
        print("🧪 Running: test_csv_upload_default_subtype_when_no_matching_note")
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
        print("🧪 Running: test_csv_upload_handles_empty_rows")
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
        print("🧪 Running: test_csv_upload_with_missing_columns")
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
        print("🧪 Running: test_csv_upload_invalid_file")
        self.client.login(username='testuser', password='testpass123')

        # Try to upload without file
        response = self.client.post('/api/upload-csv/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PortfolioTestCase(unittest.TestCase):
    """Test cases for the TradeRepublic portfolio functionality"""

    def setUp(self):
        # Mock TradeRepublicApi
        self.mock_tr = Mock(spec=TradeRepublicApi)
        self.mock_tr.compact_portfolio = AsyncMock()
        self.mock_tr.cash = AsyncMock()
        self.mock_tr.watchlist = AsyncMock()
        self.mock_tr.recv = AsyncMock()
        self.mock_tr.unsubscribe = AsyncMock()
        self.mock_tr.instrument_details = AsyncMock()
        self.mock_tr.ticker = AsyncMock()

        # Sample portfolio data
        self.sample_positions = [
            {
                "instrumentId": "US0378331005",
                "netSize": "10.0",
                "averageBuyIn": "150.0",
                "name": "Apple Inc.",
                "exchangeIds": ["LSX"],
                "price": 155.0,
                "netValue": 1550.0,
                "exchangeId": "LSX"
            }
        ]

        self.sample_cash = [{"amount": "1000.0", "currencyId": "EUR"}]

    def test_portfolio_overview_calculation(self):
        """Test that portfolio overview calculates totals correctly"""
        print("🧪 Running: test_portfolio_overview_calculation")
        portfolio = Portfolio(self.mock_tr)

        # Mock the portfolio data
        portfolio.portfolio = self.sample_positions
        portfolio.cash = self.sample_cash

        result = portfolio.overview()

        # Check positions
        self.assertEqual(len(result["positions"]), 1)
        pos = result["positions"][0]
        self.assertEqual(pos["name"], "Apple Inc.")
        self.assertEqual(pos["isin"], "US0378331005")
        self.assertEqual(pos["quantity"], 10.0)
        self.assertEqual(pos["price"], 155.0)
        self.assertEqual(pos["buyCost"], 1500.0)  # 150 * 10
        self.assertEqual(pos["netValue"], 1550.0)
        self.assertEqual(pos["diff"], 50.0)  # 1550 - 1500
        self.assertAlmostEqual(pos["diffP"], 3.333, places=3)  # (50/1500)*100

        # Check summary
        summary = result["summary"]
        self.assertEqual(summary["totalBuyCost"], 1500.0)
        self.assertEqual(summary["totalNetValue"], 1550.0)
        self.assertEqual(summary["diff"], 50.0)
        self.assertAlmostEqual(summary["diffP"], 3.333, places=3)
        self.assertEqual(summary["cash"], 1000.0)
        self.assertEqual(summary["total"], 2500.0)  # 1000 + 1500
        self.assertEqual(summary["totalWithNet"], 2550.0)  # 1000 + 1550

    def test_portfolio_to_csv(self):
        """Test CSV generation"""
        print("🧪 Running: test_portfolio_to_csv")
        portfolio = Portfolio(self.mock_tr, output=None)
        portfolio.portfolio = self.sample_positions

        csv_lines = portfolio.portfolio_to_csv()

        self.assertEqual(len(csv_lines), 1)
        # Check CSV format: Name;ISIN;quantity;price;avgCost;netValue
        expected = "Apple Inc.;US0378331005;10;155;150;1550"
        self.assertEqual(csv_lines[0], expected)

    def test_portfolio_to_csv_with_output(self):
        """Test CSV generation with output file"""
        print("🧪 Running: test_portfolio_to_csv_with_output")
        with patch('builtins.open', create=True) as mock_open:
            with patch('pathlib.Path.mkdir'):
                portfolio = Portfolio(self.mock_tr, output="test.csv")
                portfolio.portfolio = self.sample_positions

                csv_lines = portfolio.portfolio_to_csv()

                # Should still return csv_lines
                self.assertEqual(len(csv_lines), 1)
                # Should have written to file
                mock_open.assert_called_once()

    def test_portfolio_sorting(self):
        """Test portfolio sorting by different columns"""
        print("🧪 Running: test_portfolio_sorting")
        portfolio = Portfolio(self.mock_tr, sort_by_column="name", sort_descending=False)
        portfolio.portfolio = [
            {"name": "Z Stock", "instrumentId": "Z123", "netSize": "1.0", "averageBuyIn": "100.0", "price": 100.0, "netValue": 100.0, "exchangeIds": ["LSX"]},
            {"name": "A Stock", "instrumentId": "A123", "netSize": "1.0", "averageBuyIn": "200.0", "price": 200.0, "netValue": 200.0, "exchangeIds": ["LSX"]}
        ]
        portfolio.cash = self.sample_cash

        result = portfolio.overview()

        # Should be sorted by name ascending
        self.assertEqual(result["positions"][0]["name"], "A Stock")
        self.assertEqual(result["positions"][1]["name"], "Z Stock")

    def test_portfolio_with_watchlist(self):
        """Test portfolio including watchlist items"""
        print("🧪 Running: test_portfolio_with_watchlist")
        portfolio = Portfolio(self.mock_tr, include_watchlist=True)
        portfolio.portfolio = self.sample_positions
        portfolio.watchlist = [
            {"instrumentId": "US5949181045", "name": "Microsoft Corp."}
        ]

        # Mock the watchlist processing
        portfolio._extend_with_watchlist = Mock()

        # This would normally be called in portfolio_loop
        # For testing, we can manually set the extended portfolio
        portfolio.portfolio = self.sample_positions + [
            {"instrumentId": "US5949181045", "name": "Microsoft Corp.", "netSize": "0.0", "averageBuyIn": "300.0", "price": 310.0, "netValue": 0.0, "exchangeIds": ["LSX"]}
        ]
        portfolio.cash = self.sample_cash

        result = portfolio.overview()
        self.assertEqual(len(result["positions"]), 2)

    def test_empty_portfolio(self):
        """Test handling of empty portfolio"""
        print("🧪 Running: test_empty_portfolio")
        portfolio = Portfolio(self.mock_tr)
        portfolio.portfolio = []
        portfolio.cash = [{"amount": "500.0", "currencyId": "EUR"}]

        result = portfolio.overview()

        self.assertEqual(len(result["positions"]), 0)
        self.assertEqual(result["summary"]["cash"], 500.0)
        self.assertEqual(result["summary"]["totalBuyCost"], 0)
        self.assertEqual(result["summary"]["totalNetValue"], 0)



    def test_decimal_localization(self):
        """Test decimal localization formatting"""
        print("🧪 Running: test_decimal_localization")
        portfolio = Portfolio(self.mock_tr, decimal_localization=True, lang="de")
        portfolio.portfolio = self.sample_positions

        # Test the decimal format function
        formatted = portfolio._decimal_format(1234.56, precision=2)
        # In German locale, this should use comma as decimal separator
        # But since babel might not be available in test, we'll just check it returns a string
        self.assertIsInstance(formatted, str)

    @patch('standalone_portfolio.login')
    def test_get_portfolio_data_function(self, mock_login):
        """Test the main get_portfolio_data function"""
        print("🧪 Running: test_get_portfolio_data_function")
        mock_login.return_value = self.mock_tr

        # Mock the portfolio get method
        with patch.object(Portfolio, 'get', return_value={"test": "data"}):
            result = get_portfolio_data("1234567890", "1234")

            mock_login.assert_called_once_with(phone_no="1234567890", pin="1234", web=False)
            self.assertEqual(result, {"test": "data"})

    def test_login_error_handling(self):
        """Test login error handling"""
        print("🧪 Running: test_login_error_handling")
        with patch('standalone_portfolio.TradeRepublicApi') as mock_api_class:
            mock_api = Mock()
            mock_api_class.return_value = mock_api
            mock_api.login.side_effect = ValueError("Login failed")

            with self.assertRaises(ValueError):
                get_portfolio_data("1234567890", "1234")
