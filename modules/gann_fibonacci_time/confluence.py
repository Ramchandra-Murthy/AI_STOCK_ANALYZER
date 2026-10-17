"""Deterministic confluence tagging for research events."""
from __future__ import annotations

def find_confluence(time_zone_indices: list[int] | tuple[int, ...], price_projections: list[dict[str, int | float | str]], observed_prices: dict[int, float], tolerance_pct: float = 0.5) -> list[dict[str, int | float]]:
    """Tag a time-zone bar when its close is near a projected Gann level."""
    if not 0 <= tolerance_pct < 100:
        raise ValueError("tolerance_pct must be in [0, 100).")
    zones, matches = set(time_zone_indices), []
    for projection in price_projections:
        index, projected = projection["target_index"], float(projection["price"])
        if index not in zones or index not in observed_prices:
            continue
        observed = float(observed_prices[index])
        if observed <= 0 or projected <= 0:
            continue
        distance = abs(observed - projected) / projected * 100
        if distance <= tolerance_pct:
            matches.append({"bar_index": index, "ratio": float(projection["ratio"]), "projected_price": projected, "observed_price": observed, "distance_pct": distance})
    return sorted(matches, key=lambda item: (int(item["bar_index"]), float(item["distance_pct"])))
