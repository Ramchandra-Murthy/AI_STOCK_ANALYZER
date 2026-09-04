from pathlib import Path

p = Path("/app/services/scoring/fundamental.py")
text = p.read_text(encoding="utf-8-sig")

old = '''        details = {
            "ratios": {
                "gross_margin": ratios.gross_margin,
                "ebitda_margin": ratios.ebitda_margin,
                "ebit_margin": ratios.ebit_margin,
                "net_margin": ratios.net_margin,
                "roe": ratios.roe,
                "roa": ratios.roa,
                "roce": ratios.roce,
                "roic": ratios.roic,
                "current_ratio": ratios.current_ratio,
                "quick_ratio": ratios.quick_ratio,
                "debt_to_equity": ratios.debt_to_equity,
                "net_debt_to_ebitda": ratios.net_debt_to_ebitda,
                "fcf_margin": ratios.fcf_margin,
                "cash_conversion_ratio": ratios.cash_conversion_ratio,
                "asset_turnover": ratios.asset_turnover,
                "inventory_turnover": ratios.inventory_turnover,
            },
            "profitability": profitability_components,
            "quality": quality_components,
            "financial_strength": financial_strength_components,
            "capital_efficiency": capital_efficiency_components,
            "cash_flow_quality": cash_flow_components,
            "weights": pillar_weights,
        }
'''

new = '''        raw_ratios = {
            "gross_margin": ratios.gross_margin,
            "ebitda_margin": ratios.ebitda_margin,
            "ebit_margin": ratios.ebit_margin,
            "net_margin": ratios.net_margin,
            "roe": ratios.roe,
            "roa": ratios.roa,
            "roce": ratios.roce,
            "roic": ratios.roic,
            "current_ratio": ratios.current_ratio,
            "quick_ratio": ratios.quick_ratio,
            "debt_to_equity": ratios.debt_to_equity,
            "net_debt_to_ebitda": ratios.net_debt_to_ebitda,
            "fcf_margin": ratios.fcf_margin,
            "cash_conversion_ratio": ratios.cash_conversion_ratio,
            "asset_turnover": ratios.asset_turnover,
            "inventory_turnover": ratios.inventory_turnover,
        }

        details = {
            # Block 10 audit identity
            "engine_version": "EROS-3.0-BLOCK-10",

            # Canonical Block 10 audit contract
            "raw_ratios": raw_ratios,
            "profitability_components": profitability_components,
            "quality_components": quality_components,
            "capital_allocation_components": capital_efficiency_components,

            # Existing detailed contract retained for compatibility
            "ratios": raw_ratios,
            "profitability": profitability_components,
            "quality": quality_components,
            "financial_strength": financial_strength_components,
            "capital_efficiency": capital_efficiency_components,
            "cash_flow_quality": cash_flow_components,
            "weights": pillar_weights,
        }
'''

if old not in text:
    raise SystemExit("PATCH ABORTED: expected details block not found")

p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("SUCCESS: Added Block 10 audit contract to FundamentalScoringEngine")