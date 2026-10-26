"""Regression tests for benchmark-relative diagnostics in Neural Networks Lab."""

from pathlib import Path


def test_neural_networks_lab_exposes_benchmark_relative_trade_diagnostics() -> None:
    source = Path("pages/Neural_Networks_Lab.py").read_text(encoding="utf-8")
    assert "benchmark_relative_diagnostics" in source
    assert "Benchmark-relative trade diagnostics" in source
    assert "neural_networks_benchmark_relative_diagnostics.csv" in source
    assert "entry-to-exit intervals" in source
