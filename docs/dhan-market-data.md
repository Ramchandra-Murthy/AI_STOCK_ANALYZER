# Dhan market-data integration

The application now has a read-only adapter boundary for DhanHQ market data.

## Credentials

Set these environment variables outside source control:

- `DHAN_CLIENT_ID`
- `DHAN_ACCESS_TOKEN`

Never commit or log the access token.

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
