import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import aiohttp
from django.test import TestCase
from Tracker.stocks import (
    get_id,
    get_history,
    get_id_async,
    get_history_async,
    fetch_multiple_prices,
    fetch_single_price,
    get_symbol_and_industry,
)


class StocksTestCase(TestCase):
    """Test cases for stock-related functionality"""

    @patch("Tracker.stocks.requests.get")
    def test_get_id_success(self, mock_get):
        """Test successful ISIN to ID conversion"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "12345", "displayname": "Test Company"}
        ]
        mock_get.return_value = mock_response

        result_id, result_name = get_id("DE1234567890")

        self.assertEqual(result_id, "12345")
        self.assertEqual(result_name, "Test Company")
        mock_get.assert_called_once()

    @patch("Tracker.stocks.requests.get")
    def test_get_id_http_error(self, mock_get):
        """Test handling of HTTP errors in get_id"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(AssertionError):
            get_id("DE1234567890")

    @patch("Tracker.stocks.requests.get")
    def test_get_id_empty_response(self, mock_get):
        """Test handling of empty response in get_id"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        with self.assertRaises(IndexError):
            get_id("DE1234567890")

    @patch("Tracker.stocks.get_id")
    @patch("Tracker.stocks.requests.get")
    def test_get_history_success(self, mock_get, mock_get_id):
        """Test successful history retrieval"""
        mock_get_id.return_value = ("12345", "Test Company")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "series": {
                "intraday": {"data": [[1234567890, 100.50], [1234567891, 101.25]]}
            }
        }
        mock_get.return_value = mock_response

        name, intraday_data = get_history("DE1234567890")

        self.assertEqual(name, "Test Company")
        self.assertEqual(len(intraday_data), 2)
        self.assertEqual(intraday_data[0], [1234567890, 100.50])

    @patch("Tracker.stocks.get_id")
    @patch("Tracker.stocks.requests.get")
    def test_get_history_http_error(self, mock_get, mock_get_id):
        """Test handling of HTTP errors in get_history"""
        mock_get_id.return_value = ("12345", "Test Company")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with self.assertRaises(AssertionError):
            get_history("DE1234567890")

    @patch("Tracker.stocks.aiohttp.ClientSession.get")
    async def test_get_id_async_success(self, mock_get):
        """Test successful async ISIN to ID conversion"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {"id": "12345", "displayname": "Test Company"}
        ]
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result_id, result_name = await get_id_async("DE1234567890", session)

        self.assertEqual(result_id, "12345")
        self.assertEqual(result_name, "Test Company")

    @patch("Tracker.stocks.aiohttp.ClientSession.get")
    async def test_get_id_async_http_error(self, mock_get):
        """Test handling of HTTP errors in async get_id"""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result_id, result_name = await get_id_async("DE1234567890", session)

        self.assertIsNone(result_id)
        self.assertIsNone(result_name)

    @patch("Tracker.stocks.get_id_async")
    @patch("Tracker.stocks.aiohttp.ClientSession.get")
    async def test_get_history_async_success(self, mock_get, mock_get_id_async):
        """Test successful async history retrieval"""
        mock_get_id_async.return_value = ("12345", "Test Company")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "series": {
                "intraday": {"data": [[1234567890, 100.50]]},
                "history": {"data": [[1234567890, 99.00]]},
            },
            "info": {"plotlines": [{"value": 98.50}]},
        }
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            name, intraday_data, preday, history_data = await get_history_async(
                "DE1234567890", session
            )

        self.assertEqual(name, "Test Company")
        self.assertEqual(len(intraday_data), 1)
        self.assertEqual(preday, 98.50)
        self.assertEqual(len(history_data), 1)

    @patch("Tracker.stocks.get_id_async")
    @patch("Tracker.stocks.aiohttp.ClientSession.get")
    async def test_get_history_async_http_error(self, mock_get, mock_get_id_async):
        """Test handling of HTTP errors in async get_history"""
        mock_get_id_async.return_value = ("12345", "Test Company")

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            name, intraday_data, preday, history_data = await get_history_async(
                "DE1234567890", session
            )

        self.assertEqual(name, "Unknown (DE1234567890)")
        self.assertEqual(intraday_data, [])

    @patch("Tracker.stocks.get_symbol_and_industry")
    @patch("Tracker.stocks.get_history_async")
    @patch("Tracker.stocks.asyncio.to_thread")
    async def test_fetch_single_price_success(
        self, mock_to_thread, mock_get_history_async, mock_get_symbol
    ):
        """Test successful single price fetch"""
        mock_get_history_async.return_value = (
            "Test Company",
            [[1234567890, 100.50]],
            99.00,
            [[1234567890, 98.00]],
        )
        mock_get_symbol.return_value = {"industry": "Technology", "sector": "Software"}
        mock_to_thread.return_value = {"industry": "Technology", "sector": "Software"}

        result = await fetch_single_price("DE1234567890", 5)

        self.assertEqual(result["isin"], "DE1234567890")
        self.assertEqual(result["name"], "Test Company")
        self.assertEqual(result["current_price"], 100.50)
        self.assertTrue(result["success"])
        self.assertEqual(result["industry"], "Technology")
        self.assertEqual(result["sector"], "Software")

    @patch("Tracker.stocks.get_history_async")
    async def test_fetch_single_price_exception(self, mock_get_history_async):
        """Test handling of exceptions in fetch_single_price"""
        mock_get_history_async.side_effect = Exception("Test error")

        result = await fetch_single_price("DE1234567890", 5)

        self.assertEqual(result["isin"], "DE1234567890")
        self.assertEqual(result["name"], "Error (DE1234567890)")
        self.assertIsNone(result["current_price"])
        self.assertFalse(result["success"])

    @patch("Tracker.stocks.fetch_single_price")
    async def test_fetch_multiple_prices_success(self, mock_fetch_single):
        """Test successful multiple price fetch"""
        mock_fetch_single.side_effect = [
            {"isin": "DE1234567890", "name": "Company A", "success": True},
            {"isin": "DE0987654321", "name": "Company B", "success": True},
        ]

        result = await fetch_multiple_prices(["DE1234567890", "DE0987654321"], 5)

        self.assertEqual(len(result), 2)
        self.assertIn("DE1234567890", result)
        self.assertIn("DE0987654321", result)
        self.assertEqual(result["DE1234567890"]["name"], "Company A")
        self.assertEqual(result["DE0987654321"]["name"], "Company B")

    @patch("Tracker.stocks.requests.get")
    def test_get_symbol_and_industry_success(self, mock_get):
        """Test successful symbol and industry retrieval"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "quotes": [
                {"symbol": "AAPL", "longname": "Apple Inc.", "shortname": "Apple"}
            ]
        }

        with patch("Tracker.stocks.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.info = {
                "industry": "Technology",
                "sector": "Consumer Electronics",
            }

            result = get_symbol_and_industry("US0378331005")

            self.assertEqual(result["symbol"], "AAPL")
            self.assertEqual(result["name"], "Apple Inc.")
            self.assertEqual(result["industry"], "Technology")
            self.assertEqual(result["sector"], "Consumer Electronics")
            self.assertEqual(result["source"], "api")

    @patch("Tracker.stocks.requests.get")
    def test_get_symbol_and_industry_no_quotes(self, mock_get):
        """Test handling when no quotes are found"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"quotes": []}

        result = get_symbol_and_industry("US0378331005")

        self.assertEqual(result["symbol"], "Not found")
        self.assertEqual(result["name"], "Unknown (US0378331005)")
        self.assertEqual(result["industry"], "Unknown")
        self.assertEqual(result["sector"], "Unknown")
        self.assertEqual(result["source"], "none")

    @patch("Tracker.stocks.requests.get")
    def test_get_symbol_and_industry_http_error(self, mock_get):
        """Test handling of HTTP errors in get_symbol_and_industry"""
        mock_get.return_value.status_code = 404

        result = get_symbol_and_industry("US0378331005")

        self.assertEqual(result["symbol"], "Not found")
        self.assertEqual(result["name"], "Unknown (US0378331005)")
        self.assertEqual(result["industry"], "Unknown")
        self.assertEqual(result["sector"], "Unknown")
        self.assertEqual(result["source"], "none")

    @patch("Tracker.stocks.yf.Ticker")
    @patch("Tracker.stocks.requests.get")
    def test_get_symbol_and_industry_yfinance_error(self, mock_get, mock_ticker):
        """Test handling of yfinance errors"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "quotes": [
                {"symbol": "AAPL", "longname": "Apple Inc.", "shortname": "Apple"}
            ]
        }
        mock_ticker.return_value.info = {}

        result = get_symbol_and_industry("US0378331005")

        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["industry"], "Unknown")
        self.assertEqual(result["sector"], "Unknown")
