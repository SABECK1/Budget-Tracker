from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Transaction, TransactionType, TransactionSubType
import io
import json
import csv
import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from decimal import Decimal
from django.utils import timezone
from datetime import datetime

# Import portfolio classes for testing
import sys
import os

# sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'API', 'TradeRepublic'))
# from standalone_portfolio import Portfolio, TradeRepublicApi, get_portfolio_data

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
            name="Investment Buy"
        )
        self.sell_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Investment Sell"
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
        """Test that new regular transactions get subtype from existing transactions with same note"""
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
            transaction_subtype=custom_subtype,
            created_at=timezone.now()
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
            transaction_subtype=custom_stock_subtype,
            created_at=timezone.now()
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


# class PortfolioTestCase(unittest.TestCase):
#     """Test cases for the TradeRepublic portfolio functionality"""

#     def setUp(self):
#         # Mock TradeRepublicApi
#         self.mock_tr = Mock(spec=TradeRepublicApi)
#         self.mock_tr.compact_portfolio = AsyncMock()
#         self.mock_tr.cash = AsyncMock()
#         self.mock_tr.watchlist = AsyncMock()
#         self.mock_tr.recv = AsyncMock()
#         self.mock_tr.unsubscribe = AsyncMock()
#         self.mock_tr.instrument_details = AsyncMock()
#         self.mock_tr.ticker = AsyncMock()

#         # Sample portfolio data
#         self.sample_positions = [
#             {
#                 "instrumentId": "US0378331005",
#                 "netSize": "10.0",
#                 "averageBuyIn": "150.0",
#                 "name": "Apple Inc.",
#                 "exchangeIds": ["LSX"],
#                 "price": 155.0,
#                 "netValue": 1550.0,
#                 "exchangeId": "LSX"
#             }
#         ]

#         self.sample_cash = [{"amount": "1000.0", "currencyId": "EUR"}]

#     def test_portfolio_overview_calculation(self):
#         """Test that portfolio overview calculates totals correctly"""
#         print(" Running: test_portfolio_overview_calculation")
#         portfolio = Portfolio(self.mock_tr)

#         # Mock the portfolio data
#         portfolio.portfolio = self.sample_positions
#         portfolio.cash = self.sample_cash

#         result = portfolio.overview()

#         # Check positions
#         self.assertEqual(len(result["positions"]), 1)
#         pos = result["positions"][0]
#         self.assertEqual(pos["name"], "Apple Inc.")
#         self.assertEqual(pos["isin"], "US0378331005")
#         self.assertEqual(pos["quantity"], 10.0)
#         self.assertEqual(pos["price"], 155.0)
#         self.assertEqual(pos["buyCost"], 1500.0)  # 150 * 10
#         self.assertEqual(pos["netValue"], 1550.0)
#         self.assertEqual(pos["diff"], 50.0)  # 1550 - 1500
#         self.assertAlmostEqual(pos["diffP"], 3.333, places=3)  # (50/1500)*100

#         # Check summary
#         summary = result["summary"]
#         self.assertEqual(summary["totalBuyCost"], 1500.0)
#         self.assertEqual(summary["totalNetValue"], 1550.0)
#         self.assertEqual(summary["diff"], 50.0)
#         self.assertAlmostEqual(summary["diffP"], 3.333, places=3)
#         self.assertEqual(summary["cash"], 1000.0)
#         self.assertEqual(summary["total"], 2500.0)  # 1000 + 1500
#         self.assertEqual(summary["totalWithNet"], 2550.0)  # 1000 + 1550

#     def test_portfolio_to_csv(self):
#         """Test CSV generation"""
#         print(" Running: test_portfolio_to_csv")
#         portfolio = Portfolio(self.mock_tr, output=None)
#         portfolio.portfolio = self.sample_positions

#         csv_lines = portfolio.portfolio_to_csv()

#         self.assertEqual(len(csv_lines), 1)
#         # Check CSV format: Name;ISIN;quantity;price;avgCost;netValue
#         expected = "Apple Inc.;US0378331005;10;155;150;1550"
#         self.assertEqual(csv_lines[0], expected)

#     def test_portfolio_to_csv_with_output(self):
#         """Test CSV generation with output file"""
#         print(" Running: test_portfolio_to_csv_with_output")
#         with patch('builtins.open', create=True) as mock_open:
#             with patch('pathlib.Path.mkdir'):
#                 portfolio = Portfolio(self.mock_tr, output="test.csv")
#                 portfolio.portfolio = self.sample_positions

#                 csv_lines = portfolio.portfolio_to_csv()

#                 # Should still return csv_lines
#                 self.assertEqual(len(csv_lines), 1)
#                 # Should have written to file
#                 mock_open.assert_called_once()

#     def test_portfolio_sorting(self):
#         """Test portfolio sorting by different columns"""
#         print(" Running: test_portfolio_sorting")
#         portfolio = Portfolio(self.mock_tr, sort_by_column="name", sort_descending=False)
#         portfolio.portfolio = [
#             {"name": "Z Stock", "instrumentId": "Z123", "netSize": "1.0", "averageBuyIn": "100.0", "price": 100.0, "netValue": 100.0, "exchangeIds": ["LSX"]},
#             {"name": "A Stock", "instrumentId": "A123", "netSize": "1.0", "averageBuyIn": "200.0", "price": 200.0, "netValue": 200.0, "exchangeIds": ["LSX"]}
#         ]
#         portfolio.cash = self.sample_cash

#         result = portfolio.overview()

#         # Should be sorted by name ascending
#         self.assertEqual(result["positions"][0]["name"], "A Stock")
#         self.assertEqual(result["positions"][1]["name"], "Z Stock")

#     def test_portfolio_with_watchlist(self):
#         """Test portfolio including watchlist items"""
#         print(" Running: test_portfolio_with_watchlist")
#         portfolio = Portfolio(self.mock_tr, include_watchlist=True)
#         portfolio.portfolio = self.sample_positions
#         portfolio.watchlist = [
#             {"instrumentId": "US5949181045", "name": "Microsoft Corp."}
#         ]

#         # Mock the watchlist processing
#         portfolio._extend_with_watchlist = Mock()

#         # This would normally be called in portfolio_loop
#         # For testing, we can manually set the extended portfolio
#         portfolio.portfolio = self.sample_positions + [
#             {"instrumentId": "US5949181045", "name": "Microsoft Corp.", "netSize": "0.0", "averageBuyIn": "300.0", "price": 310.0, "netValue": 0.0, "exchangeIds": ["LSX"]}
#         ]
#         portfolio.cash = self.sample_cash

#         result = portfolio.overview()
#         self.assertEqual(len(result["positions"]), 2)

#     def test_empty_portfolio(self):
#         """Test handling of empty portfolio"""
#         print(" Running: test_empty_portfolio")
#         portfolio = Portfolio(self.mock_tr)
#         portfolio.portfolio = []
#         portfolio.cash = [{"amount": "500.0", "currencyId": "EUR"}]

#         result = portfolio.overview()

#         self.assertEqual(len(result["positions"]), 0)
#         self.assertEqual(result["summary"]["cash"], 500.0)
#         self.assertEqual(result["summary"]["totalBuyCost"], 0)
#         self.assertEqual(result["summary"]["totalNetValue"], 0)



#     def test_decimal_localization(self):
#         """Test decimal localization formatting"""
#         print(" Running: test_decimal_localization")
#         portfolio = Portfolio(self.mock_tr, decimal_localization=True, lang="de")
#         portfolio.portfolio = self.sample_positions

#         # Test the decimal format function
#         formatted = portfolio._decimal_format(1234.56, precision=2)
#         # In German locale, this should use comma as decimal separator
#         # But since babel might not be available in test, we'll just check it returns a string
#         self.assertIsInstance(formatted, str)

#     @patch('standalone_portfolio.login')
#     def test_get_portfolio_data_function(self, mock_login):
#         """Test the main get_portfolio_data function"""
#         print(" Running: test_get_portfolio_data_function")
#         mock_login.return_value = self.mock_tr

#         # Mock the portfolio get method
#         with patch.object(Portfolio, 'get', return_value={"test": "data"}):
#             result = get_portfolio_data("1234567890", "1234")

#             mock_login.assert_called_once_with(phone_no="1234567890", pin="1234", web=False)
#             self.assertEqual(result, {"test": "data"})

#     def test_login_error_handling(self):
#         """Test login error handling"""
#         print(" Running: test_login_error_handling")
#         with patch('standalone_portfolio.TradeRepublicApi') as mock_api_class:
#             mock_api = Mock()
#             mock_api_class.return_value = mock_api
#             mock_api.login.side_effect = ValueError("Login failed")

#             with self.assertRaises(ValueError):
#                 get_portfolio_data("1234567890", "1234")


class PortfolioViewTestCase(APITestCase):
    """Test cases for the portfolio_view API endpoint"""

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

        # Create transaction subtypes for stocks
        self.buy_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Investment Buy"
        )
        self.sell_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Investment Sell"
        )

    def test_portfolio_requires_authentication(self):
        """Test that portfolio endpoint requires authentication"""
        response = self.client.get('/api/portfolio/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_portfolio_empty_for_new_user(self):
        """Test portfolio returns empty data for user with no stock transactions"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['holdings'], [])
        self.assertEqual(data['total_value'], 0)
        self.assertEqual(data['holdings_count'], 0)

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_with_single_buy_transaction(self, mock_fetch_prices):
        """Test portfolio calculation with a single buy transaction"""
        self.client.login(username='testuser', password='testpass123')

        # Mock price fetch to return consistent test price
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 18.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 18.0]],
                    'preday': [[1693439999000, 17.50]],
                    'history_data': [[1693526400000, 18.0]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # Create a buy transaction
        Transaction.objects.create(
            user=self.user,
            amount=-150.00,  # Negative for buy
            quantity=10,
            isin='US0378331005',  # AAPL
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['holdings']), 1)
        holding = data['holdings'][0]

        self.assertEqual(holding['isin'], 'US0378331005')
        self.assertEqual(holding['shares'], 10.0)
        self.assertEqual(holding['avg_price'], 15.0)  # 150 / 10
        self.assertEqual(holding['current_price'], 18.0)  # Mocked price
        self.assertEqual(holding['value'], 180.0)  # 10 * 18.0
        self.assertEqual(holding['total_invested'], 150.0)  # Original amount

        self.assertEqual(data['total_value'], 180.0)  # Should be current value with mocked price
        self.assertEqual(data['holdings_count'], 1)

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_with_buy_and_sell_same_stock(self, mock_fetch_prices):
        """Test portfolio calculation with buy and sell transactions for same stock"""
        self.client.login(username='testuser', password='testpass123')

        # Mock price fetch to return consistent test price
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 16.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 16.0]],
                    'preday': [[1693439999000, 15.50]],
                    'history_data': [[1693526400000, 16.0]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # Buy 10 shares at $15 each
        Transaction.objects.create(
            user=self.user,
            amount=-150.00,
            quantity=10,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Sell 3 shares at $16 each
        Transaction.objects.create(
            user=self.user,
            amount=48.00,  # 3 * 16
            quantity=3,
            isin='US0378331005',
            transaction_subtype=self.sell_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['holdings']), 1)
        holding = data['holdings'][0]
        
        self.assertEqual(holding['isin'], 'US0378331005')
        self.assertEqual(holding['shares'], 7.0)  # 10 - 3
        # Average price calculation: total_invested / net_quantity
        # Total invested = -150 + 48 = -102
        # Net quantity = 10 + (-3) = 7
        # Avg price = |-102| / 7 = 102 / 7 ≈ 14.57
        expected_avg_price = 102 / 7
        self.assertAlmostEqual(holding['avg_price'], expected_avg_price, places=2)
        self.assertEqual(holding['current_price'], 16.0)  # Mocked price
        self.assertEqual(holding['value'], 112.0)  # 7 * 16.0
        self.assertEqual(data['total_value'], 112.0)  # 7 * 16.0

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_filters_zero_net_positions(self, mock_fetch_prices):
        """Test that stocks with zero net positions are filtered out"""
        self.client.login(username='testuser', password='testpass123')

        # Mock for MSFT only (AAPL won't be fetched since net quantity = 0)
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US5949181045': {
                    'isin': 'US5949181045',
                    'name': 'Microsoft Corp.',
                    'current_price': 20.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 20.0]],
                    'preday': [[1693439999000, 19.50]],
                    'history_data': [[1693526400000, 20.0]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # Buy 5 shares
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Sell 5 shares (net position = 0)
        Transaction.objects.create(
            user=self.user,
            amount=100.00,
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.sell_subtype,
            created_at=timezone.now()
        )

        # Buy shares of different stock
        Transaction.objects.create(
            user=self.user,
            amount=-200.00,
            quantity=10,
            isin='US5949181045',  # MSFT
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Should only show MSFT, not AAPL (which has net zero)
        self.assertEqual(len(data['holdings']), 1)
        holding = data['holdings'][0]

        self.assertEqual(holding['isin'], 'US5949181045')
        self.assertEqual(holding['shares'], 10.0)
        self.assertEqual(holding['current_price'], 20.0)
        self.assertEqual(holding['value'], 200.0)
        self.assertEqual(data['total_value'], 200.0)
        self.assertEqual(data['holdings_count'], 1)

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_with_multiple_stocks(self, mock_fetch_prices):
        """Test portfolio calculation with multiple different stocks"""
        self.client.login(username='testuser', password='testpass123')

        # Mock price fetch to return consistent test prices
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 19.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 19.0]],
                    'preday': [[1693439999000, 18.50]],
                    'history_data': [[1693526400000, 19.0]]
                },
                'US5949181045': {
                    'isin': 'US5949181045',
                    'name': 'Microsoft Corp.',
                    'current_price': 25.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 25.0]],
                    'preday': [[1693439999000, 24.50]],
                    'history_data': [[1693526400000, 25.0]]
                },
                'US02079K3059': {
                    'isin': 'US02079K3059',
                    'name': 'Alphabet Inc.',
                    'current_price': 30.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 30.0]],
                    'preday': [[1693439999000, 29.50]],
                    'history_data': [[1693526400000, 30.0]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # AAPL: Buy 10 shares at $15
        Transaction.objects.create(
            user=self.user,
            amount=-150.00,
            quantity=10,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # MSFT: Buy 5 shares at $20
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,
            quantity=5,
            isin='US5949181045',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # GOOGL: Buy 8 shares at $25
        Transaction.objects.create(
            user=self.user,
            amount=-200.00,
            quantity=8,
            isin='US02079K3059',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['holdings']), 3)
        self.assertEqual(data['holdings_count'], 3)

        # Check total value: (10*19) + (5*25) + (8*30) = 190 + 125 + 240 = 555
        self.assertEqual(data['total_value'], 555.0)

        # Verify specific holdings
        holdings_by_isin = {h['isin']: h for h in data['holdings']}
        self.assertAlmostEqual(holdings_by_isin['US0378331005']['value'], 190.0, places=2)
        self.assertAlmostEqual(holdings_by_isin['US5949181045']['value'], 125.0, places=2)
        self.assertAlmostEqual(holdings_by_isin['US02079K3059']['value'], 240.0, places=2)

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_ignores_non_stock_transactions(self, mock_fetch_prices):
        """Test that non-stock transactions are ignored in portfolio calculation"""
        self.client.login(username='testuser', password='testpass123')

        # Mock price fetch for the stock
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 22.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 22.0]],
                    'preday': [[1693439999000, 21.50]],
                    'history_data': [[1693526400000, 22.0]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # Create regular expense transaction (no ISIN)
        regular_expense = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Regular Expense"
        )
        Transaction.objects.create(
            user=self.user,
            amount=-50.00,
            quantity=0,
            isin='',  # Empty ISIN
            transaction_subtype=regular_expense,
            created_at=timezone.now()
        )

        # Create stock transaction
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Should only show the stock transaction
        self.assertEqual(len(data['holdings']), 1)
        holding = data['holdings'][0]
        self.assertEqual(holding['isin'], 'US0378331005')
        self.assertEqual(holding['current_price'], 22.0)
        self.assertEqual(holding['value'], 110.0)  # 5 * 22.0
        self.assertEqual(data['total_value'], 110.0)  # 5 * 22.0

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_with_fractional_shares(self, mock_fetch_prices):
        """Test portfolio calculation with fractional share quantities"""
        self.client.login(username='testuser', password='testpass123')

        # Mock price fetch for the stock
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 14.5,
                    'success': True,
                    'intraday_data': [[1693526400000, 14.5]],
                    'preday': [[1693439999000, 14.0]],
                    'history_data': [[1693526400000, 14.5]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # Buy fractional shares
        Transaction.objects.create(
            user=self.user,
            amount=-157.50,  # 12.5 * 12.6
            quantity=12.5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Sell some fractional shares
        Transaction.objects.create(
            user=self.user,
            amount=50.40,  # 4 * 12.6
            quantity=4,
            isin='US0378331005',
            transaction_subtype=self.sell_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['holdings']), 1)
        holding = data['holdings'][0]

        self.assertEqual(holding['shares'], 8.5)  # 12.5 - 4
        self.assertEqual(holding['current_price'], 14.5)  # Mocked price
        self.assertEqual(holding['value'], 123.25)  # 8.5 * 14.5
        self.assertEqual(data['total_value'], 123.25)  # 8.5 * 14.5
        # Total invested = -157.50 + 50.40 = -107.10
        # Avg price = |107.10| / 8.5 ≈ 12.6
        expected_avg_price = 107.10 / 8.5
        self.assertAlmostEqual(holding['avg_price'], expected_avg_price, places=2)

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_calculation_with_fees_and_taxes(self, mock_fetch_prices):
        """Test that fees and taxes are properly included in calculations"""
        self.client.login(username='testuser', password='testpass123')

        # Mock price fetch for the stock
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 28.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 28.0]],
                    'preday': [[1693439999000, 27.50]],
                    'history_data': [[1693526400000, 28.0]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # Buy with fees
        Transaction.objects.create(
            user=self.user,
            amount=-105.00,  # 100 + 5 fee
            quantity=10,
            isin='US0378331005',
            fee=5.00,
            tax=0.00,
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        holding = data['holdings'][0]

        # Average price should be based on total amount including fees
        # Total invested = -105, Net quantity = 10
        # Avg price = |105| / 10 = 10.5
        self.assertEqual(holding['avg_price'], 10.5)
        self.assertEqual(holding['total_invested'], 105.0)
        self.assertEqual(holding['current_price'], 28.0)  # Mocked price
        self.assertEqual(holding['value'], 280.0)  # 10 * 28.0
        self.assertEqual(data['total_value'], 280.0)  # 10 * 28.0

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_user_isolation(self, mock_fetch_prices):
        """Test that users only see their own portfolio data"""

        # Mock price fetch for AAPL (User 1's stock)
        async def mock_price_fetch(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 26.0,
                    'success': True,
                    'intraday_data': [[1693526400000, 26.0]],
                    'preday': [[1693439999000, 25.50]],
                    'history_data': [[1693526400000, 26.0]]
                }
            }
        mock_fetch_prices.side_effect = mock_price_fetch

        # Create second user
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        # User 1 buys AAPL
        Transaction.objects.create(
            user=self.user,
            amount=-130.00,  # 5 shares at $26
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # User 2 buys MSFT
        Transaction.objects.create(
            user=user2,
            amount=-200.00,
            quantity=10,
            isin='US5949181045',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Login as user 1
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/api/portfolio/')

        data = response.json()
        self.assertEqual(len(data['holdings']), 1)
        holding = data['holdings'][0]
        self.assertEqual(holding['isin'], 'US0378331005')
        self.assertEqual(holding['current_price'], 26.0)
        self.assertEqual(holding['value'], 130.0)  # 5 * 26.0
        self.assertEqual(data['total_value'], 130.0)  # 5 * 26.0

    def test_portfolio_with_only_sell_transactions(self):
        """Test portfolio with only sell transactions (should be empty)"""
        self.client.login(username='testuser', password='testpass123')

        # Only sell transactions (no buys)
        Transaction.objects.create(
            user=self.user,
            amount=100.00,
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.sell_subtype,
            created_at=timezone.now()
        )

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        # Should be empty since net quantity is negative
        self.assertEqual(len(data['holdings']), 0)
        self.assertEqual(data['total_value'], 0)
        self.assertEqual(data['holdings_count'], 0)


class AdjustHoldingTestCase(APITestCase):
    """Test cases for the adjust_holding_view API endpoint"""

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

        # Create transaction subtypes for stocks
        self.buy_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Investment Buy"
        )
        self.sell_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Investment Sell"
        )

    def test_adjust_holding_requires_authentication(self):
        """Test that adjust holding endpoint requires authentication"""
        response = self.client.post('/api/adjust-holding/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_adjust_holding_buy_additional_shares(self):
        """Test buying additional shares for existing position"""
        self.client.login(username='testuser', password='testpass123')

        # Create initial buy transaction
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,  # 5 shares at $20
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Adjust to 10 shares at current price $25
        response = self.client.post('/api/adjust-holding/',
            data=json.dumps({"isin": "US0378331005", "new_shares": "10.0", "current_price": "25.0"}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Holding adjusted successfully', response.json()['message'])

        # Check new transaction was created
        new_transaction = Transaction.objects.filter(user=self.user, isin='US0378331005').latest('created_at')
        self.assertEqual(new_transaction.transaction_subtype, self.buy_subtype)
        self.assertEqual(new_transaction.amount, Decimal('-125.00'))  # 5 * 25 * -1 = -125.00 not -250.00
        self.assertEqual(new_transaction.quantity, 5.0)

    def test_adjust_holding_sell_shares(self):
        """Test selling portion of existing position"""
        self.client.login(username='testuser', password='testpass123')

        # Create initial buy transaction
        Transaction.objects.create(
            user=self.user,
            amount=-200.00,  # 10 shares at $20
            quantity=10,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Adjust to 5 shares at current price $25
        response = self.client.post('/api/adjust-holding/', 
            data=json.dumps({
                'isin': 'US0378331005',
                'new_shares': '5.0',
                'current_price': '25.0'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check new transaction was created
        new_transaction = Transaction.objects.filter(user=self.user, isin='US0378331005').latest('created_at')
        self.assertEqual(new_transaction.transaction_subtype, self.sell_subtype)
        self.assertEqual(new_transaction.amount, 125.00)  # 5 * 25
        self.assertEqual(new_transaction.quantity, 5.0)

    def test_adjust_holding_no_change(self):
        """Test when no change is needed in shares"""
        self.client.login(username='testuser', password='testpass123')

        # Create initial buy transaction
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,  # 5 shares at $20
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Adjust to same number of shares
        response = self.client.post('/api/adjust-holding/', 
            data=json.dumps({
                'isin': 'US0378331005',
                'new_shares': '5.0',
                'current_price': '25.0'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('No change in shares', response.json()['message'])

    def test_adjust_holding_create_new_position(self):
        """Test creating a new position from zero shares"""
        self.client.login(username='testuser', password='testpass123')

        # Start with a new ISIN, no existing transactions
        response = self.client.post('/api/adjust-holding/', 
            data=json.dumps({
                'isin': 'US5949181045',  # MSFT
                'new_shares': '10.0',
                'current_price': '30.0'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check new transaction was created
        new_transaction = Transaction.objects.filter(user=self.user, isin='US5949181045').latest('created_at')
        self.assertEqual(new_transaction.transaction_subtype, self.buy_subtype)
        self.assertEqual(new_transaction.amount, -300.00)  # 10 * 30 * -1
        self.assertEqual(new_transaction.quantity, 10.0)

    def test_adjust_holding_negative_shares_error(self):
        """Test error when trying to adjust to negative shares"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/api/adjust-holding/', 
            data=json.dumps({
                'isin': 'US0378331005',
                'new_shares': '-5.0',
                'current_price': '20.0'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Shares cannot be negative', response.json()['error'])

    def test_adjust_holding_missing_isin_error(self):
        """Test error when ISIN is missing"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/api/adjust-holding/', 
            data=json.dumps({
                'new_shares': '10.0',
                'current_price': '20.0'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ISIN is required', response.json()['error'])

    def test_adjust_holding_invalid_json(self):
        """Test handling of invalid JSON"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(
            '/api/adjust-holding/',
            'invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid JSON', response.json()['error'])

    # Commenting out as this scenario cannot occur with current setup since subtypes are forced to be buy or sell depending on share change
    # def test_adjust_holding_subtype_not_exist_error(self):
    #     """Test handling when required transaction subtypes don't exist"""
    #     self.client.login(username='testuser', password='testpass123')

    #     # Delete buy subtype to simulate error
    #     self.buy_subtype.delete()

    #     response = self.client.post('/api/adjust-holding/', {
    #         'isin': 'US0378331005',
    #         'new_shares': 10.0,
    #         'current_price': 20.0
    #     })

    #     self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     self.assertIn('Required transaction subtypes not found', response.json()['error'])

    def test_adjust_holding_with_note(self):
        """Test adjusting holding with a custom note"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/api/adjust-holding/', 
            data=json.dumps({
                'isin': 'US0378331005',
                'new_shares': '10.0',
                'current_price': '25.0',
                'note': 'Manual adjustment for accounting'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check note was saved
        new_transaction = Transaction.objects.filter(user=self.user, isin='US0378331005').latest('created_at')
        self.assertEqual(new_transaction.note, 'Manual adjustment for accounting')


class PortfolioWithMockPriceTestCase(APITestCase):
    """Test cases for portfolio_view with mocked stock price fetching"""

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

        # Create transaction subtypes for stocks
        self.buy_subtype = TransactionSubType.objects.create(
            transaction_type=self.expense_type,
            name="Buy"
        )
        self.sell_subtype = TransactionSubType.objects.create(
            transaction_type=self.income_type,
            name="Sell"
        )

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_with_fetched_prices(self, mock_fetch_prices):
        """Test portfolio with actual fetched prices"""
        self.client.login(username='testuser', password='testpass123')

        # Create a buy transaction
        Transaction.objects.create(
            user=self.user,
            amount=-150.00,  # 10 shares at $15
            quantity=10,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype,
            created_at=timezone.now()
        )

        # Mock the async function to return data in the format expected by the view
        import asyncio
        async def mock_async_fetch(*args, **kwargs):
            # Return as dictionary with ISIN as keys, matching the format used in view
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Apple Inc.',
                    'current_price': 18.50,
                    'success': True,
                    'intraday_data': [[1693526400000, 18.50]],
                    'preday': [[1693439999000, 18.00]],
                    'history_data': [[1693526400000, 18.50]]
                }
            }

        mock_fetch_prices.side_effect = mock_async_fetch

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        holding = data['holdings'][0]

        self.assertEqual(holding['name'], 'Apple Inc.')
        self.assertEqual(holding['current_price'], 18.50)
        self.assertEqual(holding['value'], 185.0)  # 10 * 18.50
        self.assertEqual(data['total_value'], 185.0)

    @patch('Tracker.views.fetch_multiple_prices')
    @patch('Tracker.views.get_history')
    def test_portfolio_price_fetch_failure_fallback(self, mock_get_history, mock_fetch_prices):
        """Test portfolio when price fetch fails, falls back to average price"""
        self.client.login(username='testuser', password='testpass123')

        # Create a buy transaction
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,  # 5 shares at $20
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype
        )

        # Mock failed concurrent price fetch
        mock_fetch_prices.side_effect = Exception("Price fetch failed")

        # Mock successful synchronous fallback fetch
        mock_get_history.return_value = ("Apple Inc.", [[datetime.now().timestamp() * 1000, 18.50]])

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        holding = data['holdings'][0]

        # Should use the real retrieved price from fallback
        self.assertEqual(holding['current_price'], 18.50)
        self.assertEqual(holding['value'], 92.5)
        self.assertEqual(holding['name'], 'Apple Inc.')

    @patch('Tracker.views.fetch_multiple_prices')
    def test_portfolio_multiple_stocks_with_prices(self, mock_fetch_prices):
        """Test portfolio with multiple stocks and different price scenarios"""
        self.client.login(username='testuser', password='testpass123')

        # Create multiple transactions
        Transaction.objects.create(
            user=self.user,
            amount=-100.00,  # AAPL: 5 shares at $20
            quantity=5,
            isin='US0378331005',
            transaction_subtype=self.buy_subtype
        )
        Transaction.objects.create(
            user=self.user,
            amount=-60.00,  # MSFT: 3 shares at $20
            quantity=3,
            isin='US5949181045',
            transaction_subtype=self.buy_subtype
        )

        # Mock price fetch - return success for MSFT and failure for AAPL
        async def mock_async_fetch_multistock(*args, **kwargs):
            return {
                'US0378331005': {
                    'isin': 'US0378331005',
                    'name': 'Error (US0378331005)',
                    'current_price': None,
                    'success': False
                },
                'US5949181045': {
                    'isin': 'US5949181045',
                    'name': 'Microsoft Corp.',
                    'current_price': 25.00,
                    'success': True,
                    'intraday_data': [[1693526400000, 25.00]],
                    'preday': [[1693439999000, 24.50]],
                    'history_data': [[1693526400000, 25.00]]
                }
            }

        mock_fetch_prices.side_effect = mock_async_fetch_multistock

        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['holdings']), 2)

        # Check AAPL (fallback price)
        aapl_holding = next(h for h in data['holdings'] if h['isin'] == 'US0378331005')
        self.assertEqual(aapl_holding['current_price'], 20.0)
        self.assertEqual(aapl_holding['value'], 100.0)
        self.assertEqual(aapl_holding['name'], 'Unknown (US0378331005)')

        # Check MSFT (successful fetch)
        msft_holding = next(h for h in data['holdings'] if h['isin'] == 'US5949181045')
        self.assertEqual(msft_holding['name'], 'Microsoft Corp.')
        self.assertEqual(msft_holding['current_price'], 25.00)
        self.assertEqual(msft_holding['value'], 75.0)  # 3 * 25
