"""Streamlit page for the next-business-day upside candidate scanner (research only)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from scanner.next_day_movers import (
    DATA_SOURCE,
    DISCLAIMER,
    UNSUPPORTED_DATA,
    ScannerConfig,
    ScanResult,
    scan_next_day_movers,
)
from scanner.next_day_movers_eval import (
    LIMITATIONS,
    EvalConfig,
    EvaluationDataError,
    WalkForwardResult,
    evaluate_from_provider,
)
from scanner.next_day_paper_log import (
    DEFAULT_LOG_PATH,
    PAPER_CAVEAT,
    read_log,
    record_shortlist,
    settle_outcomes,
    summarise_paper_log,
)
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

SCAN_KEY = "next_day_scan_result"
EVAL_KEY = "next_day_eval_result"
EVAL_ERROR_KEY = "next_day_eval_error"
SCAN_SELECTION_KEY = "next_day_scan_selection"
EVAL_SELECTION_KEY = "next_day_eval_selection"

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

selection = (exchanges, top_n)


def _describe(chosen: tuple[tuple[str, ...], int]) -> str:
    return f"{' + '.join(chosen[0])}, shortlist size {chosen[1]}"


def _warn_if_selection_changed(key: str) -> None:
    """Flag a result that was produced for a different exchange / size selection."""
    shown = st.session_state.get(key)
    if shown is not None and shown != selection:
        st.warning(
            f"The result below was produced for {_describe(shown)}, but the current selection is "
            f"{_describe(selection)}. Run it again to refresh."
        )


with st.expander("Scope, assumptions and limitations (read before using the output)"):
    st.markdown(f"""
- **Universe:** curated lists, not the full market: {len(NSE_CANDIDATES)} NSE symbols and
  {len(BSE_CANDIDATES)} BSE scrip codes, validated and de-duplicated. A BSE listing that pairs
  with an NSE listing of the same company is dropped so a company is not ranked twice. Selected:
  **{" + ".join(exchanges)}**.
- **Data:** {DATA_SOURCE}. It is delayed and can have gaps or revisions; it is not an exchange
  feed.
- **Cutoff:** the last completed regular session's close plus a 15-minute settling buffer. The
  target is the next trading day in the repository's holiday calendar. If the calendar does not
  cover the date, or stocks traded on a day it marks closed, **no ranking is produced**.
- **Exclusions are explicit:** stale, missing, invalid, suspended, insufficient-history,
  illiquid and (NSE, when available) surveillance-flagged symbols are listed with reasons under
  *Data quality details and exclusions*.
- **Not scored:** {"; ".join(UNSUPPORTED_DATA)}.
- **Evaluation assumptions:** buy at the next session's open and sell at its close, equal
  weight, approximate costs and slippage. The pre-registered rule is fixed; it has not been
  tuned to the results.
""")
    st.markdown("**Limitations**")
    for note in LIMITATIONS:
        st.markdown(f"- {note}")

scan_tab, evaluation_tab, paper_tab = st.tabs(
    ["Next-session shortlist", "Walk-forward evaluation", "Paper-trading log"]
)


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
    coverage = result.coverage
    st.markdown(
        f"Evaluation period: **{coverage['history_start']} to {coverage['history_end']}** "
        f"({coverage['dates_evaluated']} dates evaluated). Universe: "
        f"{coverage['symbols_used']} of {coverage['symbols_requested']} requested symbols "
        f"with usable history (today's curated list, so survivorship-biased)."
    )
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
            st.session_state[SCAN_SELECTION_KEY] = selection
    scan_result = st.session_state.get(SCAN_KEY)
    if scan_result is None:
        st.info("Run the scan after the market close to rank candidates for the next session.")
    else:
        _warn_if_selection_changed(SCAN_SELECTION_KEY)
        st.caption(
            f"Generated {scan_result.generated_at.strftime('%d %b %Y %H:%M %Z')}. "
            "Re-run to refresh; results are not updated automatically."
        )
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
                st.session_state[EVAL_SELECTION_KEY] = selection
            except (EvaluationDataError, ValueError) as exc:
                st.session_state.pop(EVAL_KEY, None)
                st.session_state[EVAL_ERROR_KEY] = str(exc)
    if st.session_state.get(EVAL_ERROR_KEY):
        st.error(f"Evaluation unavailable: {st.session_state[EVAL_ERROR_KEY]}")
    elif st.session_state.get(EVAL_KEY) is not None:
        _warn_if_selection_changed(EVAL_SELECTION_KEY)
        _show_evaluation(st.session_state[EVAL_KEY])
    else:
        st.info("No evaluation has been run in this session.")

with paper_tab:
    st.info(PAPER_CAVEAT)
    st.caption(
        f"Log file: `{DEFAULT_LOG_PATH}` on this server's local disk (it can be lost when the app "
        "is redeployed). Shortlists can only be saved before their target session opens and are "
        "never overwritten; outcomes are recorded only after that session completes. Nothing "
        "here places orders."
    )
    if st.button("Save the current shortlist to the paper log"):
        saved = st.session_state.get(SCAN_KEY)
        chosen = st.session_state.get(SCAN_SELECTION_KEY)
        if saved is None or chosen is None:
            st.warning("Run a scan first; there is no shortlist to save.")
        else:
            outcome = record_shortlist(
                saved, exchanges=chosen[0], top_n=chosen[1], path=DEFAULT_LOG_PATH
            )
            if outcome.recorded:
                st.success(f"Saved the shortlist for {outcome.key}.")
            else:
                st.warning(f"Not saved: {outcome.reason}.")
    if st.button("Record outcomes for completed sessions"):
        with st.spinner("Fetching target-session bars..."):
            report = settle_outcomes(DEFAULT_LOG_PATH)
        for message in report.errors:
            st.error(f"Provider error, nothing recorded: {message}")
        if report.settled:
            st.success(f"Recorded outcomes for: {', '.join(report.settled)}")
        for key, reason in report.pending.items():
            st.info(f"{key} is still pending: {reason}")
        if not report.settled and not report.pending and not report.errors:
            st.info("Nothing to settle.")
    summary = summarise_paper_log(DEFAULT_LOG_PATH)
    st.json(summary.totals)
    if summary.totals["unreadable_lines"]:
        st.error(f"{summary.totals['unreadable_lines']} unreadable log line(s) were skipped.")
    if summary.sessions.empty:
        st.info("No completed paper sessions yet.")
    else:
        st.dataframe(summary.sessions, hide_index=True, width="stretch")
        st.caption(summary.caveat)
    with st.expander("Logged shortlists"):
        logged = read_log(DEFAULT_LOG_PATH).shortlists
        st.write(sorted(logged) or "None yet.")
