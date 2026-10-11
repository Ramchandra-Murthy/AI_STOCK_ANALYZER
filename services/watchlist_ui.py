'''Small adapter joining trusted Streamlit identity to the watchlist service.'''

from __future__ import annotations

from typing import Any

from services.watchlist_identity import get_authenticated_user_id
from services.watchlist_service import add_symbol, create_watchlist, list_symbols, list_watchlists

DEFAULT_WATCHLIST_NAME = "Watchlist 01"


def get_or_create_default_watchlist(
    user: Any, default_symbols: list[str] | None = None
) -> tuple[str, int, list[str]]:
    """Return the authenticated user's first watchlist, creating it if needed.

    Default symbols are seeded only when a user has no watchlists yet. The
    caller must pass Streamlit's trusted st.user object.
    """
    user_id = get_authenticated_user_id(user)
    watchlists = list_watchlists(user_id)
    if not watchlists:
        watchlist_id = create_watchlist(user_id, DEFAULT_WATCHLIST_NAME)
        for symbol in default_symbols or []:
            add_symbol(user_id, watchlist_id, symbol)
        return user_id, watchlist_id, list_symbols(user_id, watchlist_id)

    watchlist_id = int(watchlists[0]["id"])
    return user_id, watchlist_id, list_symbols(user_id, watchlist_id)
