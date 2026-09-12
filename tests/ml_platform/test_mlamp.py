from __future__ import annotations

from services.ml_platform.model_registry import MachineLearningPlatform
from services.ml_platform.models import ModelArtifact


def test_model_artifact_immutability() -> None:
    art = ModelArtifact(
        model_id="XGB-Alpha-v1",
        model_type="XGBoost",
        version="1.0.0",
        metrics={"auc": 0.84, "rmse": 0.12},
        status="CHAMPION",
    )
    assert art.model_id == "XGB-Alpha-v1"
    assert art.metrics["auc"] == 0.84
    assert art.timestamp is not None
    assert isinstance(art.metadata, dict)


def test_machine_learning_platform() -> None:
    artifact = MachineLearningPlatform.register_model(
        "XGB-Alpha-v1", "XGBoost", "1.0.0", {"auc": 0.84}
    )
    assert artifact.model_id == "XGB-Alpha-v1"

    inference = MachineLearningPlatform.run_inference(
        "XGB-Alpha-v1", {"ROIC": 0.18, "FCF_Yield": 0.06}
    )
    assert inference["model_id"] == "XGB-Alpha-v1"
    assert "prediction_score" in inference

    drift = MachineLearningPlatform.detect_drift(0.15, 0.16, 0.10)
    assert drift["drift_detected"] is False
