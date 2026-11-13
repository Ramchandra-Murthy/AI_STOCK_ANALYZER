"""Dashboard component for the lightweight market-movers view."""

from modules.market_movers import show


def show_market_movers() -> None:
    """Render the shared market-movers view."""
    show()
