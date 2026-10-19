import streamlit as st


def format_ai_score(score):
    """Format an AI score without implying a score exists for an empty portfolio."""
    return "N/A" if score is None else f"{score}/100"


def show_kpi_cards(summary):
    """Display portfolio KPIs in a responsive grid that stays compact on mobile."""
    ai_score = summary.get("ai_score", 80)
    has_unpriced_holdings = summary.get("unpriced_holdings", 0) > 0
    investment_label = "💰 Valued Investment" if has_unpriced_holdings else "💰 Investment"
    value_label = "📈 Valued Current Value" if has_unpriced_holdings else "📈 Current Value"
    profit_label = "💵 Profit / Loss (valued)" if has_unpriced_holdings else "💵 Profit / Loss"
    return_label = "📊 Return (valued)" if has_unpriced_holdings else "📊 Return"

    cards = [
        (investment_label, f"₹{summary['investment']:,.2f}"),
        (value_label, f"₹{summary['current_value']:,.2f}"),
        (profit_label, f"₹{summary['profit']:,.2f}"),
        (return_label, f"{summary['return']:.2f}%"),
        ("📁 Holdings", str(summary["holdings"])),
        ("🤖 AI Score", format_ai_score(ai_score)),
    ]

    card_markup = "".join(
        f"""
        <div class="portfolio-kpi-card">
            <div class="portfolio-kpi-label">{label}</div>
            <div class="portfolio-kpi-value">{value}</div>
        </div>
        """
        for label, value in cards
    )

    st.markdown(
        f"""
        <style>
        .portfolio-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
            gap: 10px;
            margin: 8px 0 16px;
        }}
        .portfolio-kpi-card {{
            box-sizing: border-box;
            min-width: 0;
            padding: 12px;
            border: 1px solid #e6e6e6;
            border-radius: 10px;
            background: var(--secondary-background-color);
        }}
        .portfolio-kpi-label {{
            color: var(--text-color);
            opacity: 0.75;
            font-size: 0.82rem;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }}
        .portfolio-kpi-value {{
            color: var(--text-color);
            font-size: clamp(1rem, 4vw, 1.45rem);
            font-weight: 600;
            line-height: 1.35;
            margin-top: 6px;
            overflow-wrap: anywhere;
        }}
        @media (max-width: 360px) {{
            .portfolio-kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 7px;
            }}
            .portfolio-kpi-card {{
                padding: 9px;
            }}
        }}
        </style>
        <div class="portfolio-kpi-grid">{card_markup}</div>
        """,
        unsafe_allow_html=True,
    )
