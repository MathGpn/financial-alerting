import unittest
from unittest.mock import patch, Mock
import pandas as pd
from main import FinancialMonitor

class TestFinancialMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = FinancialMonitor()

    @patch('yfinance.Ticker')
    def test_get_price_data_empty(self, mock_ticker):
        #  yfinance returns an empty DataFrame
        mock_ticker.return_value.history.return_value = pd.DataFrame()

        data = self.monitor.get_price_data('DUMMY')
        self.assertIsNone(data)

    @patch('yfinance.Ticker')
    def test_get_price_data_success(self, mock_ticker):
        # yfinance returns valid data
        mock_data = {
            'Close': [100, 102, 105, 110]  # Example data
        }
        mock_hist = pd.DataFrame(mock_data)
        # Pad the data to be long enough for all periods
        mock_hist = pd.concat([mock_hist] * 10, ignore_index=True)

        mock_ticker.return_value.history.return_value = mock_hist

        # Manually set values for assertion
        mock_hist.loc[mock_hist.index[-1], 'Close'] = 110
        mock_hist.loc[mock_hist.index[-2], 'Close'] = 105
        mock_hist.loc[mock_hist.index[-8], 'Close'] = 102
        mock_hist.loc[mock_hist.index[-23], 'Close'] = 100

        data = self.monitor.get_price_data('DUMMY')

        self.assertIsNotNone(data)
        self.assertAlmostEqual(data['current'], 110)
        self.assertAlmostEqual(data['daily_change'], ((110 - 105) / 105) * 100)
        self.assertAlmostEqual(data['weekly_change'], ((110 - 102) / 102) * 100)
        self.assertAlmostEqual(data['monthly_change'], ((110 - 100) / 100) * 100)

    @patch('main.FinancialMonitor.get_price_data')
    def test_check_alerts_no_alerts(self, mock_get_price_data):
        # No data crosses the alert threshold
        mock_get_price_data.return_value = {
            "current": 100,
            "daily_change": -1.0,
            "weekly_change": -2.0,
            "monthly_change": -3.0
        }

        alerts = self.monitor.check_alerts()
        self.assertEqual(len(alerts), 0)

    @patch('main.FinancialMonitor.get_price_data')
    def test_check_alerts_with_alerts(self, mock_get_price_data):
        # Data that should trigger daily, weekly, and monthly alerts
        mock_get_price_data.side_effect = [
            { # SP500
                "current": 4000,
                "daily_change": -3.0,  # Alert
                "weekly_change": -4.0,
                "monthly_change": -5.0
            },
            { # Bitcoin
                "current": 30000,
                "daily_change": -1.0,
                "weekly_change": -6.0, # Alert
                "monthly_change": -7.0
            },
            { # Gold
                "current": 1800,
                "daily_change": -1.0,
                "weekly_change": -2.0,
                "monthly_change": -11.0 # Alert
            }
        ]

        alerts = self.monitor.check_alerts()

        self.assertEqual(len(alerts), 3)
        self.assertIn("SP500: -3.00% (daily)", alerts[0])
        self.assertIn("Bitcoin: -6.00% (weekly)", alerts[1])
        self.assertIn("Gold: -11.00% (monthly)", alerts[2])

    @patch('smtplib.SMTP_SSL')
    def test_send_email_with_alerts(self, mock_smtp_ssl):
        # Configure email settings
        self.monitor.sender_email = "sender@example.com"
        self.monitor.recipient_email = "recipient@example.com"
        self.monitor.sender_password = "password"

        mock_server = Mock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        alerts = ["Test Alert 1", "Test Alert 2"]
        self.monitor.send_email(alerts)

        mock_smtp_ssl.assert_called_with(self.monitor.smtp_server, 465)
        mock_server.ehlo.assert_called_once()
        mock_server.login.assert_called_with("sender@example.com", "password")
        mock_server.sendmail.assert_called_once()

        # Check email content
        args, _ = mock_server.sendmail.call_args
        sent_from, sent_to, email_text = args
        self.assertEqual(sent_from, "sender@example.com")
        self.assertEqual(sent_to, "recipient@example.com")
        self.assertIn("Subject: Alerte Financiere", email_text)
        self.assertIn("Test Alert 1\nTest Alert 2", email_text)

    @patch('smtplib.SMTP_SSL')
    def test_send_email_no_alerts(self, mock_smtp_ssl):
        self.monitor.send_email([])
        mock_smtp_ssl.assert_not_called()

    @patch('smtplib.SMTP_SSL')
    def test_send_email_no_config(self, mock_smtp_ssl):
        self.monitor.sender_email = None
        self.monitor.send_email(["Test Alert"])
        mock_smtp_ssl.assert_not_called()

    @patch('main.FinancialMonitor.send_email')
    @patch('main.FinancialMonitor.check_alerts')
    @patch('main.FinancialMonitor.debug_prices')
    def test_run_with_alerts(self, mock_debug_prices, mock_check_alerts, mock_send_email):
        mock_check_alerts.return_value = ["Test Alert"]

        self.monitor.run()

        mock_debug_prices.assert_called_once()
        mock_check_alerts.assert_called_once()
        mock_send_email.assert_called_with(["Test Alert"])

    @patch('main.FinancialMonitor.send_email')
    @patch('main.FinancialMonitor.check_alerts')
    @patch('main.FinancialMonitor.debug_prices')
    def test_run_no_alerts(self, mock_debug_prices, mock_check_alerts, mock_send_email):
        mock_check_alerts.return_value = []

        self.monitor.run()

        mock_debug_prices.assert_called_once()
        mock_check_alerts.assert_called_once()
        mock_send_email.assert_not_called()

    @patch('main.FinancialMonitor.get_price_data')
    @patch('builtins.print')
    def test_debug_prices(self, mock_print, mock_get_price_data):
        mock_get_price_data.return_value = {
            "current": 100,
            "daily_change": -1.0,
            "weekly_change": -2.0,
            "monthly_change": -3.0
        }

        self.monitor.debug_prices()

        # 3 assets in self.symbols
        self.assertEqual(mock_print.call_count, 3)

    @patch('smtplib.SMTP_SSL')
    @patch('builtins.print')
    def test_send_email_exception(self, mock_print, mock_smtp_ssl):
        self.monitor.sender_email = "sender@example.com"
        self.monitor.recipient_email = "recipient@example.com"
        self.monitor.sender_password = "password"

        mock_server = Mock()
        mock_server.login.side_effect = Exception("Test SMTP Error")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        self.monitor.send_email(["Test Alert"])

        mock_print.assert_called_with("Erreur email: Test SMTP Error")
