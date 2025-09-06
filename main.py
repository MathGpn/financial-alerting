import os
import time
import logging
import pandas as pd
import yfinance as yf

from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Optional, Set

from models import Alert, Financial, Mailer

logger = logging.getLogger(__name__)

if os.path.exists('.env'):
    load_dotenv()

class FinancialMonitor:
    def __init__(self):
        self.symbols = {"SP500": "^GSPC", "Bitcoin": "BTC-USD", "Gold": "GC=F"}
        self.thresholds = {"daily": -2.0, "weekly": -5.0, "monthly": -10.0}
        
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.recipient_email = os.getenv("RECIPIENT_EMAIL", "")
        self.port = 465

        self.alerted_today: Set[Alert] = set()
        self.last_reset = datetime.now().date()

    def run_continuously(self, interval_seconds: int = 120):
        while True:
            now = datetime.now()

            if now.date() != self.last_reset:
                self.alerted_today.clear()
                self.last_reset = now.date()
                logger.info("Reset daily alerts tracker")

            alerts = self.check_alerts()
            filtered_alerts = [a for a in alerts if a not in self.alerted_today]

            if filtered_alerts:
                self.send_email(filtered_alerts)
                for alert in filtered_alerts:
                    self.alerted_today.add(alert)
            else:
                logger.info("No new alerts !")

            time.sleep(interval_seconds)

    def get_price_data(
        self,
        symbol: str,
        day_step: int = 1,
        week_step: int = 7,
        month_step: int = 30,
    ) -> Optional[Dict]:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2mo")
        
        if hist.empty:
            return None
            
        current = hist['Close'].iloc[-1]
        yesterday = hist['Close'].iloc[-(1 + day_step)] if len(hist.index) > day_step else current
        week_ago = hist['Close'].iloc[-(1 + week_step)] if len(hist.index) > week_step else current
        month_ago = hist['Close'].iloc[-(1 + month_step)] if len(hist.index) > month_step else current
        
        return {
            "current": current,
            "daily": ((current - yesterday) / yesterday) * 100,
            "weekly": ((current - week_ago) / week_ago) * 100,
            "monthly": ((current - month_ago) / month_ago) * 100
        }

    def check_alerts(self) -> List[Alert]:
        alerts: List[Alert] = []
        
        for name, symbol in self.symbols.items():
            delta = self.get_price_data(symbol)
            if not delta:
                continue
                
            for period, threshold in self.thresholds.items():
                if delta[period] <= threshold:
                    msg = (
                        f"{name}: {delta[period]:.2f}% ({period}) "
                        f"- Prix: ${delta['current']:.2f}"
                    )
                    alert = Alert.create(name, symbol, period, msg)
                    financial = Financial.create(symbol)
                    data = financial.get_data(period)

                    if isinstance(data, pd.DataFrame):
                        alert.graph = data

                    alerts.append(alert)
        
        return alerts

    def send_email(self, alerts: List[Alert]):
        if not alerts or not self.sender_email or not self.recipient_email:
            logger.info("Pas d'alerte ou variables email manquantes")
            return

        subject = f"Alerte Financiere - {datetime.now().strftime('%Y-%m-%d')}"

        mailer = Mailer(
            self.smtp_server,
            self.port,
            self.sender_email,
            self.sender_password,
            self.recipient_email,
            subject,
            alerts,
        )

        mailer.add_charts()
        mailer.send()


    def debug_prices(self):
        for name, symbol in self.symbols.items():
            data = self.get_price_data(symbol)
            if data:
                logger.info(
                    f"{name}: {data['current']:.2f}$ | "
                    f"1j: {data['daily']:.2f}% | "
                    f"1s: {data['weekly']:.2f}% | "
                    f"1m: {data['monthly']:.2f}%"
                )

    def run(self):
        logger.info(f"Vérification - {datetime.now()}")

        self.debug_prices()
        alerts = self.check_alerts()
        
        if alerts:
            self.send_email(alerts)
        else:
            logger.info("Aucune alerte")

if __name__ == "__main__":
    interval = int(os.getenv('INTERVAL', '90'))
    monitor = FinancialMonitor()
    monitor.run_continuously(interval)