from __future__ import annotations

from typing import Any

from services.research_service import get_stock_profile
from services.sotp_debt_like_liability_service import (
    generate_sotp_debt_like_liabilities,
)
from services.sotp_investment_policy_service import (
    generate_sotp_investment_policy,
)
from services.sotp_ownership_service import (
    generate_sotp_ownership_adjustment,
)
from services.sotp_segment_valuation_service import (
    generate_operating_sotp_valuation,
)


def _num(value: Any):
    if isinstance(value, (int, float)):
        try:
            if value != value:
                return None
        except Exception:
            pass
        return float(value)
    return None


def _crore_to_rupees(value: float) -> float:
    return value * 1e7


def generate_sotp_equity_bridge(
    symbol: str,
) -> dict[str, Any]:

    symbol = symbol.upper().strip()

    # ---------------------------------------------
    # 1. OPERATING SOTP
    # ---------------------------------------------

    operating = generate_operating_sotp_valuation(symbol)

    if operating.get("status") != "OK":
        return {
            "status": "ERROR",
            "symbol": symbol,
            "message": "Operating SOTP unavailable.",
            "operating": operating,
        }

    operating_ev = _num(operating.get("operating_enterprise_value"))

    if operating_ev is None:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "message": "Operating enterprise value unavailable.",
        }

    # ---------------------------------------------
    # 2. AUTHORIZED DEBT-LIKE ADJUSTMENTS
    # ---------------------------------------------

    debt_like = generate_sotp_debt_like_liabilities(symbol)

    authorized_debt_adjustment = _num(debt_like.get("authorized_bridge_adjustment"))

    if authorized_debt_adjustment is None:
        authorized_debt_adjustment = 0.0

    # ---------------------------------------------
    # 3. OWNERSHIP / MINORITY INTEREST
    # ---------------------------------------------

    ownership = generate_sotp_ownership_adjustment(symbol)

    ownership_adjustment = 0.0
    ownership_bridge_ready = False

    if ownership.get("status") == "OK":
        candidate = _num(ownership.get("ownership_adjustment"))

        # Current ownership service does not expose
        # bridge_ready explicitly. Do NOT automatically
        # authorize the accounting NCI adjustment.
        if ownership.get("bridge_ready") is True:
            ownership_adjustment = candidate or 0.0
            ownership_bridge_ready = True

    # ---------------------------------------------
    # 4. INVESTMENT ASSETS
    # ---------------------------------------------

    investment = generate_sotp_investment_policy(symbol)

    investment_adjustment = 0.0

    if investment.get("status") == "OK" and investment.get("bridge_ready") is True:
        investment_adjustment = (
            _num(investment.get("included_investment_adjustment")) or 0.0
        )

    # ---------------------------------------------
    # 5. AUTHORIZED EQUITY VALUE
    # ---------------------------------------------

    total_authorized_adjustment = (
        authorized_debt_adjustment + ownership_adjustment + investment_adjustment
    )

    authorized_equity_value = operating_ev + total_authorized_adjustment

    # ---------------------------------------------
    # 6. SHARES / PRICE
    # ---------------------------------------------

    profile = get_stock_profile(symbol) or {}

    shares = _num(profile.get("shares_outstanding"))

    current_price = _num(profile.get("price"))

    fair_value_per_share = None
    upside_percent = None

    if shares is not None and shares > 0:
        fair_value_per_share = _crore_to_rupees(authorized_equity_value) / shares

    if (
        fair_value_per_share is not None
        and current_price is not None
        and current_price > 0
    ):
        upside_percent = (fair_value_per_share / current_price - 1) * 100

    # ---------------------------------------------
    # 7. PENDING ITEMS
    # ---------------------------------------------

    pending_items = []

    liabilities = debt_like.get("liabilities", {})

    for key, item in liabilities.items():

        if not isinstance(item, dict):
            continue

        if item.get("bridge_ready") is not True:
            pending_items.append(
                {
                    "key": key,
                    "category": "LIABILITY",
                    "value": _num(item.get("value")),
                    "treatment": item.get("treatment"),
                    "reason": item.get("reason"),
                }
            )

    if ownership.get("status") == "OK" and not ownership_bridge_ready:
        pending_items.append(
            {
                "key": "minority_interest",
                "category": "OWNERSHIP",
                "value": _num(ownership.get("minority_interest")),
                "treatment": ownership.get("treatment"),
                "reason": (
                    "Ownership adjustment is informative "
                    "but not authorized for the final bridge "
                    "until bridge_ready is explicitly true."
                ),
            }
        )

    pending_investment_exposure = _num(investment.get("pending_investment_exposure"))

    if pending_investment_exposure is not None and pending_investment_exposure > 0:
        pending_items.append(
            {
                "key": "investment_assets",
                "category": "ASSET",
                "value": pending_investment_exposure,
                "treatment": "PENDING_CLASSIFICATION",
                "reason": (
                    "Investment assets remain excluded "
                    "until classification and valuation "
                    "basis are authorized."
                ),
            }
        )

    # ---------------------------------------------
    # 8. COMPLETENESS / CONFIDENCE
    # ---------------------------------------------

    operating_coverage = _num(operating.get("operating_coverage")) or 0.0

    operating_reliability = _num(operating.get("weighted_reliability")) or 0.0

    bridge_complete = len(pending_items) == 0

    if bridge_complete:
        valuation_status = "FINAL"
    else:
        valuation_status = "PROVISIONAL"

    # This is intentionally conservative.
    confidence_score = operating_coverage * operating_reliability * 100

    if not bridge_complete:
        confidence_score *= 0.75

    if confidence_score >= 80:
        confidence = "HIGH"
    elif confidence_score >= 60:
        confidence = "MODERATE"
    else:
        confidence = "LOW"

    # ---------------------------------------------
    # OUTPUT
    # ---------------------------------------------

    return {
        "status": "OK",
        "version": "V5.0",
        "symbol": symbol,
        "currency": "INR",
        "unit": "crore",
        "operating_enterprise_value": operating_ev,
        "authorized_adjustments": {
            "net_debt_and_debt_like": (authorized_debt_adjustment),
            "ownership": ownership_adjustment,
            "investments": investment_adjustment,
            "total": total_authorized_adjustment,
        },
        "authorized_equity_value": (authorized_equity_value),
        "shares_outstanding": shares,
        "current_price": current_price,
        "fair_value_per_share": (fair_value_per_share),
        "upside_percent": upside_percent,
        "operating_coverage_percent": (operating_coverage * 100),
        "operating_reliability": (operating_reliability),
        "pending_item_count": len(pending_items),
        "pending_items": pending_items,
        "bridge_complete": bridge_complete,
        "valuation_status": valuation_status,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "interpretation": (
            "Fair value is based only on operating "
            "enterprise value and explicitly authorized "
            "equity-bridge adjustments. Pending assets "
            "and liabilities are disclosed but excluded."
        ),
        "warnings": [
            (
                "A PROVISIONAL valuation must not be "
                "presented as completed SOTP fair value."
            ),
            ("Pending positive assets may increase " "equity value when resolved."),
            (
                "Pending debt-like or ownership claims "
                "may reduce equity value when resolved."
            ),
            (
                "No unresolved item is automatically "
                "included merely because a reported "
                "accounting balance exists."
            ),
        ],
        "components": {
            "operating": operating,
            "debt_like": debt_like,
            "ownership": ownership,
            "investment_policy": investment,
        },
    }
