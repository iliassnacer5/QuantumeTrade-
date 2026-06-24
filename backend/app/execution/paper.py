"""Broker papier (simulation) — exécution par défaut, sans risque réel.

Remplit l'ordre au dernier prix de marché connu (données réelles si dispo, sinon synthétiques).
C'est le mode imposé tant que l'utilisateur n'a pas validé KYC + activé le réel.
"""

from __future__ import annotations

from app.data import markets
from app.execution.base import OrderResult


class PaperBroker:
    mode = "paper"

    def __init__(self, name: str = "paper") -> None:
        self.name = name

    async def place_order(self, symbol: str, side: str, qty: float) -> OrderResult:
        candles = await markets.load_candles(symbol, interval="1h", limit=60)
        price = candles[-1].close if candles else 0.0
        return OrderResult(
            broker=self.name,
            mode=self.mode,
            symbol=symbol,
            side=side,
            qty=qty,
            status="filled",
            filled_price=round(price, 8),
            raw={"simulated": True},
        )
