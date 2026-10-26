"""Tests for the isolated neural-network research baseline."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.features import build_direction_dataset, build_features


def sample_ohlcv(rows: int = 180) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series(100 + np.arange(rows) * 0.2 + np.sin(np.arange(rows)), index=index)
    return pd.DataFrame(
        {
            "Open": close * 0.999,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 100_000 + np.arange(rows) * 100,
        },
        index=index,
    )


def test_features_have_expected_columns_and_causal_index() -> None:
    features = build_features(sample_ohlcv())
    assert list(features.columns) == [
        "return_1d",
        "return_5d",
        "return_20d",
        "volatility_20d",
        "sma_distance_20d",
        "relative_volume_20d",
        "volume_zscore_20d",
        "rsi_14",
        "atr_pct_14",
        "range_pct",
    ]


def test_features_do_not_change_when_future_rows_change() -> None:
    data = sample_ohlcv()
    original = build_features(data)
    changed = data.copy()
    changed.loc[changed.index[-1], ["Open", "High", "Low", "Close", "Volume"]] *= 3
    updated = build_features(changed)
    # A future observation must not affect any earlier feature vector.
    pd.testing.assert_frame_equal(original.iloc[:-1], updated.iloc[:-1])


def test_dataset_excludes_rows_without_future_label() -> None:
    data = sample_ohlcv()
    features, target = build_direction_dataset(data, horizon=5)
    assert features.index.equals(target.index)
    # Signal at t, enter at t+1 close, exit at t+horizon+1 close.
    assert features.index.max() == data.index[-7]
    assert set(target.unique()).issubset({0, 1})


def test_missing_columns_raise_clear_error() -> None:
    with pytest.raises(ValueError, match="Missing required OHLCV columns"):
        build_features(pd.DataFrame({"Close": [1, 2]}))


def test_chronological_split_purges_overlapping_label_windows() -> None:
    from neural_networks.baseline import chronological_split

    data = sample_ohlcv(rows=520)
    features, target = build_direction_dataset(data, horizon=5)
    X_train, X_test, y_train, y_test = chronological_split(features, target, 0.70, horizon=5)

    assert X_train.index.equals(y_train.index)
    assert X_test.index.equals(y_test.index)
    split_at = int(len(features) * 0.70)
    assert X_train.index[-1] == features.index[split_at - 7]
    assert X_test.index[0] == features.index[split_at]
    # For horizon=5, the last training label exits six source rows after its signal.
    source_positions = {date: i for i, date in enumerate(data.index)}
    assert source_positions[X_train.index[-1]] + 6 < source_positions[X_test.index[0]]


def test_baseline_comparison_and_walk_forward_preserve_chronology() -> None:
    from neural_networks.evaluation import (
        compare_holdout_baselines,
        walk_forward_evaluation,
    )

    data = sample_ohlcv(rows=520)
    features, target = build_direction_dataset(data, horizon=5)

    comparison = compare_holdout_baselines(features, target, train_fraction=0.70, horizon=5)
    assert set(comparison["Model"]) == {
        "Majority-class",
        "Logistic regression",
        "MLP",
    }
    assert comparison["Accuracy"].between(0, 1).all()

    walk_forward = walk_forward_evaluation(features, target, n_splits=3, horizon=5)
    assert len(walk_forward) == 9
    assert set(walk_forward["Model"]) == {
        "Majority-class",
        "Logistic regression",
        "MLP",
    }
    assert (walk_forward["Train end"] < walk_forward["Test start"]).all()
    for _, fold in walk_forward.groupby("Fold"):
        train_end = pd.Timestamp(fold["Train end"].iloc[0])
        test_start = pd.Timestamp(fold["Test start"].iloc[0])
        assert (test_start - train_end).days >= 8
    assert walk_forward["Accuracy"].between(0, 1).all()


def test_cost_aware_backtest_uses_non_overlapping_trades_and_costs() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=240)
    signal_dates = data.index[100:180]
    probabilities = np.full(len(signal_dates), 0.9)

    summary_free, trades_free = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.5,
        cost_bps_per_side=0,
    )
    summary_costed, trades_costed = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.5,
        cost_bps_per_side=10,
    )

    assert len(trades_free) > 0
    assert len(trades_free) == len(trades_costed)
    assert (
        trades_free["Exit date"].iloc[:-1].to_numpy()
        <= trades_free["Signal date"].shift(-1).iloc[:-1].to_numpy()
    ).all()
    assert summary_costed.loc[0, "Total return"] <= summary_free.loc[0, "Total return"]
    assert summary_costed.loc[0, "Trades"] == len(trades_costed)


def test_cost_aware_backtest_rejects_empty_signals() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=180)
    with pytest.raises(ValueError, match="at least one holdout signal"):
        backtest_holdout_signals(data["Close"], pd.Index([]), [], horizon=5)


def test_feature_ablation_uses_same_holdout_window_for_each_variant() -> None:
    from neural_networks.evaluation import compare_feature_ablation

    data = sample_ohlcv(rows=520)
    result = compare_feature_ablation(data, horizon=5, train_fraction=0.70)
    assert len(result) == 4
    assert set(result["Feature set"]) == {"Original factors", "Expanded factors"}
    assert set(result["Model"]) == {"Logistic regression", "MLP"}
    assert result["Test rows"].nunique() == 1
    assert result["Test start"].nunique() == 1
    assert result["Test end"].nunique() == 1
    assert result.loc[result["Feature set"] == "Original factors", "Feature count"].eq(6).all()
    assert result.loc[result["Feature set"] == "Expanded factors", "Feature count"].eq(10).all()
    assert result["Accuracy"].between(0, 1).all()


def test_factor_information_coefficient_reports_chronological_windows() -> None:
    from neural_networks.evaluation import factor_information_coefficient

    data = sample_ohlcv(rows=520)
    result = factor_information_coefficient(data, horizon=5, n_windows=5)
    summary = result.loc[result["Window"] == "Summary"]
    detail = result.loc[result["Window"] != "Summary"]

    assert len(summary) == 10
    assert len(detail) == 50
    assert summary["Factor"].nunique() == 10
    assert detail.groupby("Factor")["Window"].nunique().eq(5).all()
    assert summary["Valid windows"].between(0, 5).all()
    assert summary["Positive windows"].between(0, 5).all()
    assert detail["Observations"].gt(0).all()
    assert summary["Window start"].notna().all()
    assert summary["Window end"].notna().all()


def test_factor_ic_bootstrap_interval_is_bounded_and_reproducible() -> None:
    from neural_networks.evaluation import _block_bootstrap_spearman_ic_interval

    index = pd.RangeIndex(100)
    factor = pd.Series(np.linspace(0, 1, 100), index=index)
    returns = pd.Series(np.linspace(0, 1, 100) + np.sin(np.arange(100)) * 0.05, index=index)

    first = _block_bootstrap_spearman_ic_interval(
        factor, returns, n_bootstrap=60, block_size=5, random_state=7
    )
    second = _block_bootstrap_spearman_ic_interval(
        factor, returns, n_bootstrap=60, block_size=5, random_state=7
    )
    assert first == second
    assert -1 <= first[0] <= first[1] <= 1


def test_factor_ic_bootstrap_interval_returns_nan_for_constant_factor() -> None:
    from neural_networks.evaluation import _block_bootstrap_spearman_ic_interval

    factor = pd.Series(np.ones(50))
    returns = pd.Series(np.arange(50, dtype=float))
    lower, upper = _block_bootstrap_spearman_ic_interval(factor, returns)
    assert np.isnan(lower)
    assert np.isnan(upper)


def test_walk_forward_stability_summary_reports_per_model_dispersion() -> None:
    from neural_networks.evaluation import summarize_walk_forward_stability

    folds = pd.DataFrame(
        {
            "Model": ["MLP", "MLP", "MLP", "Logistic regression", "Logistic regression"],
            "Fold": [1, 2, 3, 1, 2],
            "Accuracy": [0.6, 0.8, 0.7, 0.55, 0.65],
            "Balanced accuracy": [0.58, 0.78, 0.68, 0.54, 0.64],
            "ROC-AUC": [0.61, 0.81, np.nan, 0.56, 0.66],
        }
    )

    result = summarize_walk_forward_stability(folds).set_index("Model")

    assert result.loc["MLP", "Folds"] == 3
    assert result.loc["MLP", "Accuracy mean"] == pytest.approx(0.7)
    assert result.loc["MLP", "Accuracy std"] == pytest.approx(0.1)
    assert result.loc["MLP", "Accuracy min"] == pytest.approx(0.6)
    assert result.loc["MLP", "Accuracy max"] == pytest.approx(0.8)
    assert result.loc["MLP", "ROC-AUC mean"] == pytest.approx(0.71)
    assert result.loc["MLP", "ROC-AUC std"] == pytest.approx(np.std([0.61, 0.81], ddof=1))


def test_walk_forward_stability_summary_validates_required_columns() -> None:
    from neural_networks.evaluation import summarize_walk_forward_stability

    with pytest.raises(ValueError, match="missing columns"):
        summarize_walk_forward_stability(pd.DataFrame({"Model": ["MLP"]}))


def test_backtest_benchmark_uses_complete_holdout_window_after_last_trade() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=240)
    signal_dates = data.index[100:180]
    probabilities = np.full(len(signal_dates), 0.9)
    cost_bps = 10.0

    summary, trades = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.5,
        cost_bps_per_side=cost_bps,
    )

    assert not trades.empty
    assert trades["Exit date"].max() < data.index[-1]
    benchmark = summary.loc[summary["Strategy"] == "Buy and hold"].iloc[0]
    full_period_prices = data.loc[signal_dates[0] :, "Close"]
    gross_benchmark_return = full_period_prices.iloc[-1] / full_period_prices.iloc[0] - 1.0
    side_cost = cost_bps / 10_000.0
    expected_net_return = (1.0 - side_cost) ** 2 * (1.0 + gross_benchmark_return) - 1.0
    assert benchmark["Total return"] == pytest.approx(expected_net_return)


def test_factor_ic_display_normalizes_mixed_window_types() -> None:
    source = open("pages/Neural_Networks_Lab.py", encoding="utf-8").read()
    assert "factor_ic_display = factor_ic.copy()" in source
    assert 'factor_ic_display["Window"] = factor_ic_display["Window"].astype(str)' in source
    assert 'data=factor_ic.to_csv(index=False).encode("utf-8")' in source


def test_backtest_equity_return_matches_compounded_non_overlapping_trade_returns() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=260)
    signal_dates = data.index[100:180]
    probabilities = np.full(len(signal_dates), 0.9)
    summary, trades = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.5,
        cost_bps_per_side=12.0,
    )

    assert not trades.empty
    compounded_trade_return = float((1.0 + trades["Net return after costs"]).prod() - 1.0)
    strategy_return = float(
        summary.loc[summary["Strategy"] == "MLP threshold strategy", "Total return"].iloc[0]
    )
    assert strategy_return == pytest.approx(compounded_trade_return, abs=1e-10)


def test_backtest_skips_signals_without_a_complete_future_exit() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=180)
    signal_dates = data.index[-10:]
    probabilities = np.full(len(signal_dates), 0.9)
    summary, trades = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.5,
        cost_bps_per_side=10.0,
    )

    assert not trades.empty
    assert (trades["Exit date"] <= data.index[-1]).all()
    assert trades["Signal date"].max() <= data.index[-7]
    assert summary.loc[summary["Strategy"] == "MLP threshold strategy", "Trades"].iloc[0] == len(
        trades
    )


def test_backtest_threshold_above_all_probabilities_produces_no_trades() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=200)
    signal_dates = data.index[100:130]
    probabilities = np.full(len(signal_dates), 0.4)
    summary, trades = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.8,
        cost_bps_per_side=10.0,
    )

    assert trades.empty
    strategy = summary.loc[summary["Strategy"] == "MLP threshold strategy"].iloc[0]
    assert strategy["Trades"] == 0
    assert strategy["Total return"] == pytest.approx(0.0)



def test_mlp_baseline_reports_training_convergence_diagnostics() -> None:
    from neural_networks.baseline import train_baseline

    data = sample_ohlcv(rows=520)
    features, target = build_direction_dataset(data, horizon=5)
    model, metrics = train_baseline(features, target, train_fraction=0.70, horizon=5)
    network = model.named_steps["network"]

    assert metrics["training_iterations"] == network.n_iter_
    assert metrics["max_iterations"] == network.max_iter == 300
    assert metrics["reached_iteration_limit"] is (network.n_iter_ >= network.max_iter)
    assert metrics["final_training_loss"] == pytest.approx(network.loss_)
    assert metrics["training_loss_curve"] == pytest.approx(network.loss_curve_)
    assert len(metrics["training_loss_curve"]) == network.n_iter_
    assert np.isfinite(metrics["training_loss_curve"]).all()
    assert isinstance(metrics["convergence_warnings"], list)
    assert all(isinstance(message, str) for message in metrics["convergence_warnings"])
