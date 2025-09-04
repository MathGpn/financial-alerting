import yfinance as yf
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()

class FinancialMonitor:
    def __init__(self):
        self.symbols = {"SP500": "^GSPC", "Bitcoin": "BTC-USD", "Gold": "GC=F"}
        self.thresholds = {"daily": -1.0, "weekly": -10.0, "monthly": -20.0}
        
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.sender_email = os.getenv("EMAIL_SENDER")
        self.sender_password = os.getenv("EMAIL_PASSWORD") 
        self.recipient_email = os.getenv("EMAIL_RECEIVER")

    def get_price_data(self, symbol: str) -> Dict:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2mo")
        
        if hist.empty:
            return None
            
        current = hist['Close'].iloc[-1]
        yesterday = hist['Close'].iloc[-2] if len(hist) >= 2 else current
        week_ago = hist['Close'].iloc[-8] if len(hist) >= 8 else current
        month_ago = hist['Close'].iloc[-23] if len(hist) >= 23 else current
        
        return {
            "current": current,
            "daily_change": ((current - yesterday) / yesterday) * 100,
            "weekly_change": ((current - week_ago) / week_ago) * 100,
            "monthly_change": ((current - month_ago) / month_ago) * 100
        }

    def check_alerts(self) -> List[str]:
        alerts = []
        
        for name, symbol in self.symbols.items():
            data = self.get_price_data(symbol)
            if not data:
                continue
                
            for period, threshold in self.thresholds.items():
                change_key = f"{period}_change"
                if data[change_key] <= threshold:
                    alerts.append(
                        f"🚨 {name}: {data[change_key]:.2f}% ({period}) "
                        f"- Prix: ${data['current']:.2f}"
                    )
        
        return alerts

    def send_email(self, alerts: List[str]):
        if not alerts or not self.sender_email or not self.recipient_email:
            print("⚠️ Pas d'alerte ou variables email manquantes")
            return

        subject = f"Alerte Financière - {datetime.now().strftime('%Y-%m-%d')}"
        body = "\n".join(alerts)

        msg = MIMEText(body, "plain", "utf-8")
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email

        try:
            with smtplib.SMTP_SSL(self.smtp_server, 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print(f"✅ Email envoyé à {self.recipient_email} ({len(alerts)} alertes)")
        except Exception as e:
            print(f"❌ Erreur email: {e}")


    def debug_prices(self):
        for name, symbol in self.symbols.items():
            data = self.get_price_data(symbol)
            if data:
                print(f"{name}: {data['current']:.2f}$ | "
                      f"1j: {data['daily_change']:.2f}% | "
                      f"1s: {data['weekly_change']:.2f}% | "
                      f"1m: {data['monthly_change']:.2f}%")

    def run(self):
        print(f"Vérification - {datetime.now()}")
        print("DEBUG EMAIL CONFIG:")
        print("  sender:", self.sender_email)
        print("  receiver:", self.recipient_email)
        print("  password:", "OK" if self.sender_password else "MISSING")

        self.debug_prices()
        alerts = self.check_alerts()
        
        if alerts:
            print("\n".join(alerts))
            self.send_email(alerts)
        else:
            print("Aucune alerte")

if __name__ == "__main__":
    monitor = FinancialMonitor()
    monitor.run()