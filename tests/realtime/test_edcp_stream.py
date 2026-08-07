from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.realtime.stream_hub import manager

client = TestClient(app)

def test_websocket_connection_manager_subscriptions() -> None:
    client_id = "client_alpha_01"
    symbol = "TCS.NS"

    manager.subscribe(client_id, symbol)
    assert symbol in manager.active_subscriptions
    assert client_id in manager.active_subscriptions[symbol]

    payload = manager.broadcast_quote(symbol, 3450.0, 15000)
    assert payload["symbol"] == symbol
    assert payload["price"] == 3450.0
    assert payload["subscriber_count"] == 1

    manager.unsubscribe(client_id, symbol)
    assert symbol not in manager.active_subscriptions

def test_realtime_publishing_api_endpoint() -> None:
    response = client.post("/api/v1/realtime/publish?symbol=INFY.NS&price=1850.50&volume=25000")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["broadcast_payload"]["symbol"] == "INFY.NS"
    assert data["broadcast_payload"]["price"] == 1850.50

def test_realtime_subscriptions_api_endpoint() -> None:
    manager.subscribe("terminal_02", "RELIANCE.NS")
    response = client.get("/api/v1/realtime/subscriptions")
    assert response.status_code == 200
    data = response.json()
    assert "RELIANCE.NS" in data["subscriptions"]
    assert "terminal_02" in data["subscriptions"]["RELIANCE.NS"]
    manager.unsubscribe("terminal_02", "RELIANCE.NS")