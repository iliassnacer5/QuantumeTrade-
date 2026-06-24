"""Contrat broker + types d'ordres."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class OrderResult:
    """Résultat normalisé d'un passage d'ordre, quel que soit le broker."""

    broker: str
    mode: str  # paper | live
    symbol: str
    side: str  # buy | sell
    qty: float
    status: str  # filled | accepted | rejected
    filled_price: float | None
    raw: dict | None = None


class Broker(Protocol):
    name: str
    mode: str

    async def place_order(self, symbol: str, side: str, qty: float) -> OrderResult: ...
