from __future__ import annotations

from services.scoring.block18_orchestrator import UnifiedInvestmentResult


class Block19ReportGenerator:
    """
    EROS 3.0 Block 19 Institutional Report Generator.
    Transforms a UnifiedInvestmentResult object into a comprehensive, professional Markdown report
    for portfolio managers, investment committees, and automated distribution.
    """

    @staticmethod
    def generate_markdown(result: UnifiedInvestmentResult) -> str:
        dec = result.decision
        res = result.research
        reas = result.reasoning
        conf = result.confidence

        lines: list[str] = []
        lines.append("# EROS 3.0 — INSTITUTIONAL INVESTMENT REPORT")
        lines.append(f"**Symbol**: {result.symbol}  ")
        lines.append(
            f"**Final Verdict**: **{result.final_action}** (Adjusted Confidence: {result.adjusted_confidence*100:.1f}%)  "
        )
        lines.append(f"**Engine Version**: {result.details['engine_version']}  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Executive Summary
        lines.append("## 1. Executive Summary")
        lines.append(
            f"- **Composite AI Score**: `{dec.composite_score:.2f}/100` (Rating: `{dec.rating}`)"
        )
        lines.append(
            f"- **Economic Moat**: `{res.moat_classification}` (Score: `{res.moat_score:.1f}/100`"
        )
        lines.append(
            f"- **Research Confidence**: `{conf.confidence_rating}` (`{conf.overall_confidence*100:.1f}%`)"
        )
        lines.append(
            f"- **Portfolio Target Weight**: `{dec.target_weight*100:.2f}%` (Incremental: `{dec.incremental_weight*100:.2f}%`)"
        )
        lines.append(
            f"- **Net Expected Return**: `{dec.net_expected_return*100:.2f}%` (After TCA Execution Cost: ₹`{dec.execution_cost:,.2f}`)`"
        )
        lines.append("")

        # 2. Pillar Breakdown
        lines.append("## 2. Quantitative Pillar Breakdown")
        lines.append("| Pillar | Score |")
        lines.append("| :--- | :--- |")
        lines.append(f"| Growth (Block 11) | `{dec.growth_score:.1f}` |")
        lines.append(f"| Quality / Fundamentals (Block 12) | `{dec.quality_score:.1f}` |")
        lines.append(f"| Profitability (Block 12) | `{dec.profitability_score:.1f}` |")
        lines.append(f"| Capital Allocation (Block 12) | `{dec.capital_allocation_score:.1f}` |")
        lines.append(f"| Valuation (Block 13) | `{dec.valuation_score:.1f}` |")
        lines.append(f"| Momentum (Block 14) | `{dec.momentum_score:.1f}` |")
        lines.append(f"| Risk & Resilience (Block 15) | `{dec.risk_score:.1f}` |")
        lines.append("")

        # 3. Research & Economic Moat
        lines.append("## 3. Research Intelligence & Economic Moat")
        lines.append(f"> **Investment Thesis**: {res.thesis_summary}")
        lines.append("")
        lines.append("**Key Growth Drivers**:")
        for driver in res.drivers:
            lines.append(f"- {driver}")
        lines.append("")
        lines.append(f"**Primary Risk**: {res.primary_risk}")
        lines.append("")

        # 4. Business Reasoning & Contradictions
        lines.append("## 4. Evidence & Business Reasoning")
        lines.append(f"- **Synthesized Recommendation**: `{reas.recommendation}`")
        lines.append(f"- **Hypotheses Generated**: `{reas.hypothesis_count}`")
        lines.append(
            f"- **Contradictions Flagged**: `{reas.contradiction_count}` (High Severity: `{reas.high_severity_contradictions}`)"
        )
        lines.append("")
        if reas.hypotheses_summaries:
            lines.append("**Verified Hypotheses**:")
            for h in reas.hypotheses_summaries:
                lines.append(f"- ✅ {h}")
            lines.append("")
        if reas.contradictions_summaries:
            lines.append("**Identified Contradictions**:")
            for c in reas.contradictions_summaries:
                lines.append(f"- ⚠️ {c}")
            lines.append("")

        # 5. Portfolio & Execution Details
        lines.append("## 5. Portfolio Allocation & Execution")
        lines.append(f"- **Current Portfolio Weight**: `{dec.portfolio_weight*100:.2f}%`")
        lines.append(f"- **Target Portfolio Weight**: `{dec.target_weight*100:.2f}%`")
        lines.append(f"- **Incremental Trade Weight**: `{dec.incremental_weight*100:.2f}%`")
        lines.append(f"- **Estimated Execution Cost (TCA)**: ₹`{dec.execution_cost:,.2f}`")
        lines.append("")
        if dec.details.get("execution_details", {}).get("generated_orders"):
            lines.append("**Generated Orders**:")
            for order in dec.details["execution_details"]["generated_orders"]:
                lines.append(
                    f"- `{order['action']} {order['quantity']:,} shares of {order['symbol']} at limit price ₹{order['limit_price']:,.2f}` (Slippage: `{order['estimated_slippage']*100:.2f}%`)"
                )
            lines.append("")

        # 6. Summary Rationale
        lines.append("## 6. Investment Committee Rationale")
        for rat in result.summary_rationale:
            lines.append(f"- {rat}")
        lines.append("")
        lines.append("---")
        lines.append("*Generated by EROS 3.0 Institutional Investment Engine*")

        return "\n".join(lines)
