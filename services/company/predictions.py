from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class PredictionRecord:
    prediction_id: str
    symbol: str
    thesis: str
    signal: str # "BUY", "HOLD", "SELL"
    confidence: float
    target_price: float
    horizon_months: int
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    outcome_actual_return: float | None = None
    outcome_status: str = "PENDING" # "PENDING", "SUCCESSFUL", "FAILED"
    evaluated_at: str | None = None

class PredictionLedger:
    """Institutional learning ledger that stores and evaluates historical investment predictions."""

    def __init__(self) -> None:
        self._predictions: Dict[str, List[PredictionRecord]] = {}

    def record_prediction(self, pred: PredictionRecord) -> None:
        if pred.symbol not in self._predictions:
            self._predictions[pred.symbol] = []
        self._predictions[pred.symbol].append(pred)

    def get_predictions(self, symbol: str) -> List[PredictionRecord]:
        return self._predictions.get(symbol, [])

    def evaluate_prediction(self, symbol: str, prediction_id: str, actual_return: float) -> PredictionRecord:
        preds = self._predictions.get(symbol, [])
        for i, p in enumerate(preds):
            if p.prediction_id == prediction_id:
                success = (p.signal == "BUY" and actual_return > 0) or (p.signal == "SELL" and actual_return < 0)
                status = "SUCCESSFUL" if success else "FAILED"
                updated = PredictionRecord(
                    prediction_id=p.prediction_id,
                    symbol=p.symbol,
                    thesis=p.thesis,
                    signal=p.signal,
                    confidence=p.confidence,
                    target_price=p.target_price,
                    horizon_months=p.horizon_months,
                    created_at=p.created_at,
                    outcome_actual_return=actual_return,
                    outcome_status=status,
                    evaluated_at=datetime.utcnow().isoformat()
                )
                preds[i] = updated
                return updated
        raise ValueError(f"Prediction {prediction_id} for {symbol} not found.")
