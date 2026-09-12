from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from services.quantitative.block104_eros_command_center import (
    EROSBlock104CommandCenter,
)


def _status_label(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value)


def render_eros_command_center(
    read_model: Mapping[str, Any],
) -> None:
    """
    EROS 3.0 institutional command-center UI.

    Presentation-only.
    No order creation.
    No broker submission.
    No live execution.
    """

    engine = EROSBlock104CommandCenter()

    model = engine.render_model(read_model=read_model)

    st.header("🏛️ EROS 3.0 Institutional Command Center")

    st.caption("Read-only governance, execution and reconciliation control view")

    # ==========================================================
    # TOP STATUS CARDS
    # ==========================================================

    cards = model["status_cards"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Governance",
        _status_label(cards["governance"]),
    )

    c2.metric(
        "Execution Intent",
        _status_label(cards["intent"]),
    )

    c3.metric(
        "Paper Execution",
        _status_label(cards["execution"]),
    )

    c4.metric(
        "Reconciliation",
        _status_label(cards["reconciliation"]),
    )

    st.divider()

    # ==========================================================
    # SAFETY
    # ==========================================================

    st.subheader("🔒 Execution Safety")

    safety = model["safety"]

    s1, s2, s3, s4 = st.columns(4)

    s1.metric(
        "Broker Submission",
        "FALSE" if safety["broker_submission"] is False else "TRUE",
    )

    s2.metric(
        "Live Execution",
        "FALSE" if safety["live_order_submission"] is False else "TRUE",
    )

    s3.metric(
        "Execution Blocked",
        "TRUE" if safety["execution_blocked"] is True else "FALSE",
    )

    s4.metric(
        "Non-Mutation",
        "TRUE" if safety["non_mutation_invariant"] is True else "FALSE",
    )

    if (
        safety["broker_submission"] is False
        and safety["live_order_submission"] is False
        and safety["execution_blocked"] is True
        and safety["non_mutation_invariant"] is True
    ):
        st.success("Execution safety boundary is intact. " "This interface is read-only.")
    else:
        st.error("Execution safety invariant failure.")

    # ==========================================================
    # PIPELINE
    # ==========================================================

    st.subheader("🔗 EROS Pipeline")

    pipeline = model.get("pipeline", [])

    if pipeline:
        cols = st.columns(len(pipeline))

        for index, item in enumerate(pipeline):
            block_id = item.get(
                "block_id",
                item.get("block", "?"),
            )

            status = item.get(
                "status",
                "UNKNOWN",
            )

            with cols[index]:
                st.metric(
                    f"Block {block_id}",
                    str(status),
                )

    # ==========================================================
    # GOVERNANCE
    # ==========================================================

    st.subheader("🛡️ Governance")

    governance = model["governance"]

    g1, g2, g3 = st.columns(3)

    g1.metric(
        "Status",
        _status_label(governance.get("status")),
    )

    g2.metric(
        "Governance ID",
        _status_label(governance.get("governance_id")),
    )

    g3.metric(
        "Action",
        _status_label(governance.get("execution_action")),
    )

    # ==========================================================
    # EXECUTION INTENT
    # ==========================================================

    st.subheader("🎯 Execution Intent")

    intent = model["intent"]

    i1, i2, i3, i4 = st.columns(4)

    i1.metric(
        "Symbol",
        _status_label(intent.get("symbol")),
    )

    i2.metric(
        "Action",
        _status_label(intent.get("action")),
    )

    i3.metric(
        "Quantity",
        _status_label(intent.get("quantity")),
    )

    i4.metric(
        "Reference Price",
        f"₹{float(intent.get('reference_price', 0)):,.2f}",
    )

    # ==========================================================
    # PAPER EXECUTION
    # ==========================================================

    st.subheader("📊 Paper Execution")

    execution = model["execution"]

    e1, e2, e3, e4 = st.columns(4)

    e1.metric(
        "Execution Status",
        _status_label(execution.get("status")),
    )

    e2.metric(
        "Fill Status",
        _status_label(execution.get("fill_status")),
    )

    e3.metric(
        "Requested Qty",
        _status_label(execution.get("requested_quantity")),
    )

    e4.metric(
        "Filled Qty",
        _status_label(execution.get("filled_quantity")),
    )

    e5, e6, e7, e8 = st.columns(4)

    e5.metric(
        "Reference Price",
        f"₹{float(execution.get('reference_price', 0)):,.2f}",
    )

    e6.metric(
        "Fill Price",
        f"₹{float(execution.get('fill_price', 0)):,.2f}",
    )

    e7.metric(
        "Slippage (bps)",
        _status_label(execution.get("slippage_bps")),
    )

    e8.metric(
        "Transaction Cost",
        f"₹{float(execution.get('transaction_cost', 0)):,.2f}",
    )

    # ==========================================================
    # RECONCILIATION
    # ==========================================================

    st.subheader("🔄 Reconciliation")

    reconciliation = model["reconciliation"]

    r1, r2, r3, r4, r5 = st.columns(5)

    r1.metric(
        "Quantity",
        "PASS" if reconciliation.get("quantity_reconciled") else "FAIL",
    )

    r2.metric(
        "Price",
        "PASS" if reconciliation.get("price_reconciled") else "FAIL",
    )

    r3.metric(
        "Value",
        "PASS" if reconciliation.get("value_reconciled") else "FAIL",
    )

    r4.metric(
        "Cost",
        "PASS" if reconciliation.get("cost_reconciled") else "FAIL",
    )

    r5.metric(
        "Lineage",
        "PASS" if reconciliation.get("lineage_reconciled") else "FAIL",
    )

    # ==========================================================
    # LINEAGE
    # ==========================================================

    st.subheader("🔍 Audit Lineage")

    lineage = model.get("lineage", {})

    if lineage:
        lineage_rows = []

        for key, value in lineage.items():
            lineage_rows.append(
                {
                    "Stage": key,
                    "Evidence ID": value,
                }
            )

        st.dataframe(
            lineage_rows,
            use_container_width=True,
            hide_index=True,
        )

    # ==========================================================
    # UI POLICY
    # ==========================================================

    st.subheader("🔐 UI Policy")

    policy = model["ui_policy"]

    st.info(
        "EROS Command Center is a presentation-only interface. "
        "Order creation, broker submission, live execution, "
        "portfolio mutation, valuation mutation, performance "
        "mutation, risk mutation and optimization are disabled."
    )

    if policy["read_only"]:
        st.caption("READ ONLY • BLOCK 104 • EROS-3.0")
