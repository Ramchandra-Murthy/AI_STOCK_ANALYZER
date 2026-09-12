from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections for live institutional market feeds."""

    def __init__(self) -> None:
        self.active_subscriptions: dict[str, set[str]] = {}  # symbol -> set of client session IDs

    def subscribe(self, client_id: str, symbol: str) -> None:
        if symbol not in self.active_subscriptions:
            self.active_subscriptions[symbol] = set()
        self.active_subscriptions[symbol].add(client_id)
        logger.info("Client %s subscribed to live feed for symbol %s", client_id, symbol)

    def unsubscribe(self, client_id: str, symbol: str) -> None:
        if symbol in self.active_subscriptions:
            self.active_subscriptions[symbol].discard(client_id)
            if not self.active_subscriptions[symbol]:
                del self.active_subscriptions[symbol]
        logger.info("Client %s unsubscribed from symbol %s", client_id, symbol)

    def broadcast_quote(self, symbol: str, price: float, volume: int) -> dict[str, Any]:
        subscribers = self.active_subscriptions.get(symbol, set())
        payload = {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "timestamp": datetime.utcnow().isoformat(),
            "subscriber_count": len(subscribers),
        }
        logger.info(
            "Broadcasting live tick for %s at %.2f to %s subscribers",
            symbol,
            price,
            len(subscribers),
        )
        return payload


manager = ConnectionManager()
