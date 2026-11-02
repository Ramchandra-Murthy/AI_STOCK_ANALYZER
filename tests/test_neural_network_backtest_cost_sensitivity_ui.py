"""Regression tests for cost sensitivity reporting in Neural Networks Lab."""

from pathlib import Path


def test_neural_networks_lab_exposes_transaction_cost_sensitivity() -> None:
    source = Path("pages/Neural_Networks_Lab.py").read_text(encoding="utf-8")
    assert "transaction_cost_sensitivity" in source
    assert "Transaction-cost sensitivity" in source
    assert "neural_networks_transaction_cost_sensitivity.csv" in source
    assert "linear cost approximation" in source
