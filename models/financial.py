import pandas as pd
import yfinance as yf

from typing import Optional
from dataclasses import dataclass

@dataclass
class Financial:
    
    _ticker: str

    @classmethod
    def create(cls, ticker: str) -> 'Financial':
        return cls(_ticker=ticker)

    @property
    def ticker(self) -> str:
        return self._ticker

    @property
    def week_data(self) -> Optional[pd.DataFrame]:
        ticker = yf.Ticker(self.ticker)
        return ticker.history(period="5d", interval='1h')

    @property
    def day_data(self) -> Optional[pd.DataFrame]:
        ticker = yf.Ticker(self.ticker)
        return ticker.history(period="1d", interval='1h')

    @property
    def month_data(self) -> Optional[pd.DataFrame]:
        ticker = yf.Ticker(self.ticker)
        return ticker.history(period="1mo")

    def get_data(self, period: str) -> Optional[pd.DataFrame]:
        if period == "daily":
            return self.day_data

        if period == "weekly":
            return self.week_data

        if period == "monthly":
            return self.month_data

        raise ValueError(f"Wrong period name !")