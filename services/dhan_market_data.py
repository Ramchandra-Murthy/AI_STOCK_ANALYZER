"""Read-only DhanHQ market-data adapter.

The adapter deliberately excludes order-management APIs. Credentials are loaded
from the environment and are never logged or persisted by this module.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

NIFTY_50_SECURITY_ID = 13
NIFTY_INDEX_SEGMENT = "IDX_I"


class DhanConfigurationError(RuntimeError):
    """Raised when Dhan market-data configuration is incomplete."""


@dataclass(frozen=True)
class DhanCredentials:
    """Dhan credentials required to construct the official Python client."""

    client_id: str
    access_token: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> DhanCredentials:
        values = os.environ if environ is None else environ
        client_id = values.get("DHAN_CLIENT_ID", "").strip()
        access_token = values.get("DHAN_ACCESS_TOKEN", "").strip()
        missing = [
            name
            for name, value in (
                ("DHAN_CLIENT_ID", client_id),
                ("DHAN_ACCESS_TOKEN", access_token),
            )
            if not value
        ]
        if missing:
            raise DhanConfigurationError(
                f"Missing required Dhan configuration: {', '.join(missing)}"
            )
        return cls(client_id=client_id, access_token=access_token)


def _build_dhan_client(credentials: DhanCredentials) -> Any:
    """Construct the official DhanHQ Python client lazily."""
    try:
        from dhanhq import DhanContext, dhanhq
    except ImportError as exc:
        raise DhanConfigurationError(
            "The optional DhanHQ Python client is not installed. "
            "Install the official 'dhanhq' package before enabling Dhan data."
        ) from exc

    return dhanhq(DhanContext(credentials.client_id, credentials.access_token))


class DhanMarketData:
    """Read-only wrapper around DhanHQ market-data APIs."""

    def __init__(
        self,
        *,
        credentials: DhanCredentials | None = None,
        client: Any | None = None,
    ) -> None:
        if client is not None:
            self._client = client
            return
        self._client = _build_dhan_client(
            credentials if credentials is not None else DhanCredentials.from_env()
        )

    def ticker_data(self, securities: Mapping[str, list[int]]) -> dict[str, Any]:
        """Return LTP data for the requested Dhan security IDs."""
        return self._client.ticker_data(dict(securities))

    def ohlc_data(self, securities: Mapping[str, list[int]]) -> dict[str, Any]:
        """Return OHLC plus LTP data for the requested securities."""
        return self._client.ohlc_data(dict(securities))

    def quote_data(self, securities: Mapping[str, list[int]]) -> dict[str, Any]:
        """Return full quote/depth/OI/volume data for the requested securities."""
        return self._client.quote_data(dict(securities))

    def expiry_list(
        self,
        under_security_id: int,
        under_exchange_segment: str,
    ) -> dict[str, Any]:
        """Return active option expiries for an underlying."""
        return self._client.expiry_list(
            under_security_id,
            under_exchange_segment,
        )

    def option_chain(
        self,
        under_security_id: int,
        under_exchange_segment: str,
        expiry: str,
    ) -> dict[str, Any]:
        """Return the complete option chain for one underlying and expiry."""
        return self._client.option_chain(
            under_security_id,
            under_exchange_segment,
            expiry,
        )

    def intraday_minute_data(
        self,
        security_id: int | str,
        exchange_segment: str,
        instrument_type: str,
        from_date: str,
        to_date: str,
        interval: int = 1,
    ) -> dict[str, Any]:
        """Return read-only intraday OHLCV candles from Dhan."""
        return self._client.intraday_minute_data(
            security_id,
            exchange_segment,
            instrument_type,
            from_date,
            to_date,
            interval=interval,
            oi=False,
        )

    def nifty_ltp(self) -> dict[str, Any]:
        """Return the NIFTY 50 LTP response using Dhan's index instrument."""
        return self.ticker_data({NIFTY_INDEX_SEGMENT: [NIFTY_50_SECURITY_ID]})

    def nifty_expiries(self) -> dict[str, Any]:
        """Return active NIFTY 50 option expiries."""
        return self.expiry_list(NIFTY_50_SECURITY_ID, NIFTY_INDEX_SEGMENT)

    def nifty_option_chain(self, expiry: str) -> dict[str, Any]:
        """Return the NIFTY 50 option chain for a specific expiry."""
        return self.option_chain(
            NIFTY_50_SECURITY_ID,
            NIFTY_INDEX_SEGMENT,
            expiry,
        )
