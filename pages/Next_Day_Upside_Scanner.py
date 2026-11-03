"""Streamlit page for the next-business-day upside candidate scanner (research only)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from scanner.next_day_movers import DISCLAIMER, ScannerConfig, ScanResult, scan_next_day_movers
from scanner.next_day_movers_eval import (
    EvalConfig,
    EvaluationDataError,
    WalkForwardResult,
    evaluate_from_provider,
)

SCAN_KEY = "next_day_scan_result"
EVAL_KEY = "next_day_eval_result"
EVAL_ERROR_KEY = "next_day_eval_error"

st.set_page_config(page_title="Next-Day Upside Scanner", page_icon="🌅", layout="wide")

st.title("🌅 Next-Business-Day Upside Scanner")
st.warning(DISCLAIMER)
st.caption(
    "The score ranks stocks against each other using information available at the last "
    "completed session's close. It is not a probability of a rise, it is not calibrated, "
    "and nothing here places orders."
)

exchange_choice = st.radio("Exchanges", ["NSE + BSE", "NSE", "BSE"], horizontal=True)
exchanges = ("NSE", "BSE") if exchange_choice == "NSE + BSE" else (exchange_choice,)
top_n = st.slider("Shortlist size", min_value=5, max_value=50, value=20, step=5)

scan_tab, evaluation_tab = st.tabs(["Next-session shortlist", "Walk-forward evaluation"])


def _show_data_quality(result: ScanResult) -> None:
    quality = result.data_quality
    if not quality:
        return
    columns = st.columns(3)
    columns[0].metric("Universe requested", quality.get("universe_requested", "n/a"))
    columns[1].metric("Eligible after filters", quality.get("eligible", "n/a"))
    columns[2].metric("Coverage %", quality.get("coverage_pct", "n/a"))
    with st.expander("Data quality details and exclusions"):
        st.json(quality)
        if result.excluded:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Symbol": row.symbol,
                            "Exchange": row.exchange,
                            "Ticker": row.ticker,
                            "Reasons": ", ".join(row.reasons),
                        }
                        for row in result.excluded
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
        st.markdown("**Not scored (no verified source in this repository):**")
        for note in result.unavailable_data:
            st.markdown(f"- {note}")


def _show_scan(result: ScanResult) -> None:
    if result.status == "UNAVAILABLE":
        st.error("No ranking was produced. Unavailable data is reported, never substituted.")
    elif result.status == "DEGRADED":
        st.warning("Ranking produced with degraded inputs. Review the warnings below.")
    else:
        st.success("Ranking produced from complete inputs.")
    for message in (*result.errors, *result.warnings):
        st.warning(message)
    if result.prediction_cutoff is not None and result.target_business_date is not None:
        left, right = st.columns(2)
        left.metric("Prediction cutoff (IST)", result.prediction_cutoff.strftime("%d %b %Y %H:%M"))
        right.metric("Target business date", result.target_business_date.strftime("%d %b %Y"))
    frame = result.to_frame()
    if not frame.empty:
        st.dataframe(frame, hide_index=True, width="stretch")
        st.caption(f"Score type: {result.score_type}. {result.disclaimer}")
    _show_data_quality(result)


def _show_evaluation(result: WalkForwardResult) -> None:
    verdict = result.assessment["verdict"]
    if result.assessment["edge_supported"]:
        st.info(verdict)
    else:
        st.error(verdict)
    st.caption(f"Pre-registered rule: {result.assessment['rule']}")
    st.json(result.assessment["checks"])
    st.markdown(f"Round-trip cost and slippage assumed: **{result.round_trip_cost_bps:.1f} bps**")
    st.subheader("Top-k vs baselines (net of costs unless labelled gross)")
    st.dataframe(result.summary, width="stretch")
    st.subheader("Sequential folds")
    st.dataframe(result.folds, hide_index=True, width="stretch")
    st.subheader("Score quintiles (5 = highest score)")
    st.dataframe(result.quintiles, width="stretch")
    st.subheader("Sample coverage")
    st.json(result.coverage)
    st.subheader("Limitations")
    for note in result.limitations:
        st.markdown(f"- {note}")


with scan_tab:
    if st.button("Run scan for the next business session", type="primary"):
        with st.spinner("Fetching daily data and ranking candidates..."):
            st.session_state[SCAN_KEY] = scan_next_day_movers(
                ScannerConfig(exchanges=exchanges, top_n=top_n)
            )
    scan_result = st.session_state.get(SCAN_KEY)
    if scan_result is None:
        st.info("Run the scan after the market close to rank candidates for the next session.")
    else:
        _show_scan(scan_result)

with evaluation_tab:
    st.caption(
        "Rebuilds the cross-section at each historical close and measures the next session. "
        "This downloads several years of history and can take a while."
    )
    if st.button("Run walk-forward evaluation"):
        st.session_state.pop(EVAL_ERROR_KEY, None)
        with st.spinner("Running walk-forward evaluation..."):
            try:
                st.session_state[EVAL_KEY] = evaluate_from_provider(
                    EvalConfig(top_k=min(top_n, 10), scanner=ScannerConfig(exchanges=exchanges))
                )
            except (EvaluationDataError, ValueError) as exc:
                st.session_state.pop(EVAL_KEY, None)
                st.session_state[EVAL_ERROR_KEY] = str(exc)
    if st.session_state.get(EVAL_ERROR_KEY):
        st.error(f"Evaluation unavailable: {st.session_state[EVAL_ERROR_KEY]}")
    elif st.session_state.get(EVAL_KEY) is not None:
        _show_evaluation(st.session_state[EVAL_KEY])
    else:
        st.info("No evaluation has been run in this session.")
