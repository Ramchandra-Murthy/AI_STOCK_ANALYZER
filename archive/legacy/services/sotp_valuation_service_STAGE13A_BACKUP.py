import math

# ==========================================================
# HELPERS
# ==========================================================


def _safe_float(value):
    """Convert a value to a finite float or return None."""

    try:
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def _valid_positive(value):
    """Return positive finite float or None."""

    value = _safe_float(value)

    if value is None or value <= 0:
        return None

    return value


def _clean_symbol(symbol):
    """Normalize NSE symbol."""

    if not symbol:
        return ""

    symbol = str(symbol).strip().upper()

    if symbol.endswith(".NS"):
        symbol = symbol[:-3]

    return symbol


# ==========================================================
# SOTP COMPANY CONFIGURATION
# ==========================================================

SOTP_CONFIG = {
    "RELIANCE": {
        "company": "Reliance Industries Limited",
        "enabled": True,
        "profile": "HIGHLY DIVERSIFIED",
        "segments": {
            "o2c": {
                "name": "Oil-to-Chemicals",
                "valuation_method": "EV/EBITDA",
            },
            "digital": {
                "name": "Digital Services / Jio",
                "valuation_method": "EV/EBITDA",
            },
            "retail": {
                "name": "Retail",
                "valuation_method": "EV/EBITDA",
            },
            "upstream": {
                "name": "Oil & Gas Exploration and Production",
                "valuation_method": "EV/EBITDA",
            },
            "new_energy": {
                "name": "New Energy",
                "valuation_method": "STRATEGIC_VALUE",
            },
            "other": {
                "name": "Other Businesses and Investments",
                "valuation_method": "ASSET_VALUE",
            },
        },
    },
}


# ==========================================================
# CONFIGURATION
# ==========================================================


def get_sotp_configuration(symbol):
    """
    Return SOTP configuration for a company.
    """

    base_symbol = _clean_symbol(symbol)

    config = SOTP_CONFIG.get(base_symbol)

    if not isinstance(config, dict):
        return {
            "status": "UNAVAILABLE",
            "symbol": base_symbol,
            "eligible": False,
            "message": ("No SOTP configuration is available for " f"{base_symbol}."),
        }

    if not config.get("enabled", False):
        return {
            "status": "UNAVAILABLE",
            "symbol": base_symbol,
            "eligible": False,
            "message": (f"SOTP valuation is disabled for {base_symbol}."),
        }

    return {
        "status": "OK",
        "symbol": base_symbol,
        "eligible": True,
        "company": config.get("company", base_symbol),
        "profile": config.get("profile", "DIVERSIFIED"),
        "segments": config.get("segments", {}),
    }


# ==========================================================
# SEGMENT TEMPLATE
# ==========================================================


def _build_segment_template(segment_key, segment_config):
    """
    Build an empty segment valuation record.

    Financial inputs and valuation multiples will be added
    in later V5 stages.
    """

    if not isinstance(segment_config, dict):
        segment_config = {}

    return {
        "segment_key": segment_key,
        "name": segment_config.get(
            "name",
            segment_key,
        ),
        "valuation_method": segment_config.get(
            "valuation_method",
            "UNKNOWN",
        ),
        "financial_metric": None,
        "financial_metric_name": None,
        "valuation_multiple": None,
        "enterprise_value": None,
        "equity_value": None,
        "reliability": None,
        "source": None,
        "status": "PENDING",
    }


# ==========================================================
# SOTP ENGINE V5
# ==========================================================


def generate_sotp_valuation(symbol, company_data=None):
    """
    Sum-of-the-Parts Valuation Engine V5.

    Stage 13A:
        - validates SOTP eligibility
        - loads company segment configuration
        - builds the segment valuation structure
        - does NOT yet assign segment financial values
        - does NOT yet calculate fair value

    Later stages will add:
        - segment financial metrics
        - segment-specific benchmark multiples
        - segment enterprise values
        - investments
        - net debt
        - equity value
        - fair value per share
        - confidence scoring
    """

    base_symbol = _clean_symbol(symbol)

    configuration = get_sotp_configuration(base_symbol)

    if configuration.get("status") != "OK":
        return configuration

    segments_config = configuration.get(
        "segments",
        {},
    )

    if not isinstance(segments_config, dict):
        segments_config = {}

    segments = {}

    for segment_key, segment_config in segments_config.items():

        segments[segment_key] = _build_segment_template(
            segment_key,
            segment_config,
        )

    shares_outstanding = None
    current_price = None

    if isinstance(company_data, dict):

        shares_outstanding = _valid_positive(company_data.get("shares_outstanding"))

        current_price = _valid_positive(company_data.get("price"))

    return {
        "status": "OK",
        "version": "V5.0",
        "symbol": base_symbol,
        "company": configuration.get(
            "company",
            base_symbol,
        ),
        "eligible": True,
        "profile": configuration.get(
            "profile",
            "DIVERSIFIED",
        ),
        "current_price": current_price,
        "shares_outstanding": shares_outstanding,
        "segment_count": len(segments),
        "segments": segments,
        "gross_enterprise_value": None,
        "other_investments": None,
        "net_debt": None,
        "equity_value": None,
        "fair_value_per_share": None,
        "upside_percent": None,
        "confidence": None,
        "confidence_score": None,
        "valuation_status": "PENDING",
        "message": ("SOTP V5 structure initialized. " "Segment financial valuation is pending."),
    }
