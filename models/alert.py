import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go

from typing import Optional 
from dataclasses import dataclass


@dataclass(eq=True)
class Alert:

    _product: str
    _symbol: str
    _period: str
    _msg: Optional[str]
    _graph: Optional[bytes]

    @classmethod
    def create(
        cls,
        product: str,
        symbol: str,
        period: str,
        msg: Optional[str] = None,
        graph: Optional[bytes] = None,
    ) -> 'Alert':
        return cls(
            _product=product,
            _symbol=symbol,
            _period=period,
            _msg=msg,
            _graph=graph,
        )

    """Properties section"""

    @property
    def product(self) -> str:
        return self._product

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def graph(self) -> Optional[bytes]:
        return self._graph

    @property
    def msg(self) -> Optional[str]:
        return self._msg

    @property
    def period(self) -> Optional[str]:
        return self._period

    """Setters section"""

    @graph.setter
    def graph(self, df: pd.DataFrame):
        self._graph = self.make_chart(df)

    def make_chart(self, df: pd.DataFrame) -> bytes:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines+markers",
            name="Close",
            line=dict(color="cyan", width=2)
        ))

        fig.update_layout(
            title=f"{self.product} Price Evolution",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_dark",
            margin=dict(l=40, r=40, t=40, b=40)
        )

        return pio.to_image(fig, format="png")

    def __eq__(self, other):
        if isinstance(other, Alert):
            return (
                self.product == other.product
                and self.symbol == other.symbol
                and self.period == other.period
            )

        return False

    def __hash__(self):
        return hash((self.product, self.symbol, self.period))