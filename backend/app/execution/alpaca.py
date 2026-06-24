"""Broker Alpaca (actions US). Par défaut sur l'API **paper** (paper-api.alpaca.markets).

Le réel n'est utilisé que si `mode == "live"` ET que l'appelant a passé les garde-fous (Elite + KYC).
Les clés sont fournies déchiffrées juste pour l'appel ; jamais loggées.
"""

from __future__ import annotations

from app.execution.base import OrderResult

_BASE = {
    "paper": "https://paper-api.alpaca.markets",
    "live": "https://api.alpaca.markets",
}


class AlpacaBroker:
    name = "alpaca"

    def __init__(self, api_key: str, api_secret: str, mode: str = "paper") -> None:
        self.mode = "live" if mode == "live" else "paper"
        self._key = api_key
        self._secret = api_secret

    async def place_order(self, symbol: str, side: str, qty: float) -> OrderResult:
        import httpx

        url = f"{_BASE[self.mode]}/v2/orders"
        headers = {"APCA-API-KEY-ID": self._key, "APCA-API-SECRET-KEY": self._secret}
        body = {
            "symbol": symbol.replace("/", ""),
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": "day",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return OrderResult(
            broker=self.name,
            mode=self.mode,
            symbol=symbol,
            side=side,
            qty=qty,
            status=data.get("status", "accepted"),
            filled_price=float(data["filled_avg_price"]) if data.get("filled_avg_price") else None,
            raw={"id": data.get("id")},
        )
