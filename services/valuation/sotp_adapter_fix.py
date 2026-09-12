"""
SOTP Legacy Payload Cleaner
Strips unsupported legacy keys (ebit_margins, working_capital_ratios, etc.)
before passing data to modern DCFInput / EROS 3.0 engines.
"""


def clean_legacy_sotp_payload(raw_segment: dict) -> dict:
    legacy_keys_to_purge = {
        "ebit_margins",
        "working_capital_ratios",
        "sales_to_capital_ratios",
        "cost_of_capital",
    }
    return {k: v for k, v in raw_segment.items() if k not in legacy_keys_to_purge}
