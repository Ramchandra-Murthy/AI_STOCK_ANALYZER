from __future__ import annotations

from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect
from typing import Dict, Any
from backend.realtime.stream_hub import manager

router = APIRouter(prefix="/api/v1/realtime", tags=["Real-Time Intelligence"])

@router.post("/publish", status_code=status.HTTP_200_OK)
def publish_live_quote(symbol: str, price: float, volume: int) -> dict:
    """Ingest and broadcast real-time market quote to active WebSocket subscribers."""
    broadcast_data = manager.broadcast_quote(symbol, price, volume)
    return {
        "status": "SUCCESS",
        "message": f"Quote published for {symbol}",
        "broadcast_payload": broadcast_data
    }

@router.get("/subscriptions", status_code=status.HTTP_200_OK)
def get_active_subscriptions() -> dict:
    return {
        "status": "SUCCESS",
        "subscriptions": {k: list(v) for k, v in manager.active_subscriptions.items()}
    }