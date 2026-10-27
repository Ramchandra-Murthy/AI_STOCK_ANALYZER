# Dhan market-data integration

The application now has a read-only adapter boundary for DhanHQ market data.

## Credentials

Set these environment variables outside source control:

- `DHAN_CLIENT_ID`
- `DHAN_ACCESS_TOKEN`

For Streamlit Community Cloud, the same names can be configured in the app's
**Settings → Secrets**. The adapter reads environment variables first and uses
Streamlit secrets only when a value is missing from the environment.

Never commit or log the access token. A successful configuration check does not
prove the token is valid; Dhan HTTP 401 responses must still be treated as an
authentication failure, and option-chain decisions remain blocked when provider
data is unavailable.

## Official client

The adapter uses Dhan's official `dhanhq` Python client when enabled. The
dependency is intentionally not added to the locked production dependency set
in this first boundary PR; the next integration step will add and regenerate
the lockfile before enabling Dhan in deployed scanners.

## Initial scope

The adapter supports:

- LTP/ticker data
- OHLC data
- full quote data
- option-expiry lookup
- option-chain retrieval
- NIFTY 50 convenience methods

No order-placement or order-management API is exposed by this module.


## Live Top-10 provider

The live Top-10 scanner can prefer Dhan intraday candles when both Dhan credentials and
a symbol-to-security-ID map are configured. Yahoo Finance remains the automatic fallback
for unmapped or failed Dhan symbols.

Set the credentials in Streamlit Secrets and use exchange-qualified security-map keys:

```toml
DHAN_CLIENT_ID = "..."
DHAN_ACCESS_TOKEN = "..."
DHAN_SECURITY_MAP_JSON = '{"NSE:RELIANCE":2885,"NSE:TCS":11536,"BSE:RELIANCE":500325}'
```

The IDs above are examples only; verify every ID against Dhan's current instrument list.
Use keys such as `NSE:SYMBOL` and `BSE:SYMBOL`, or exact ticker forms `SYMBOL.NS` and
`SYMBOL.BO`. Legacy unqualified keys such as `RELIANCE` are treated as NSE-only; they are
not reused for BSE because exchange-specific IDs can differ. The scanner reports whether
Dhan actually returned candles and logs API failure payloads without logging credentials.
No order-management API is used by this provider.

The scanner requests 1-minute intraday OHLCV candles from Dhan. Dhan documents 1-minute
and 5-minute intraday candle intervals for active instruments.
