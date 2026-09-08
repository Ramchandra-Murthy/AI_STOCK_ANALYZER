# EROS 3.0 — Live Market Integrity Reconstruction

## Problem repaired

The prior market-data path could manufacture plausible prices through mock data and
fallback parity values. That made a provider failure look like usable market data.

The repaired invariant is:

> No market price enters live EROS scoring or execution unless it is sourced from
> the canonical live-market provider, passes freshness/integrity validation, and
> is explicitly classified as LIVE.

## Canonical flow

    Yahoo Finance
        |
        v
    YahooFinanceDataProvider
        |
        v
    MarketDataPacket
        |
        v
    MarketDataIntegrityGate
        |
        +--> LIVE --------------------+
        |                             |
        +--> STALE / FALLBACK /       |
             INVALID                  |
             |                        v
             +----------------> MarketDataDecisionGate
                                      |
                             +--------+--------+
                             |                 |
                        USE_LIVE          REJECT_*
                             |                 |
                             v                 v
                       EROS scoring       audit/trace only
                             |
                             v
                     investment decision
                             |
                             v
                       execution engine
                             |
                             v
                     Block 85 certification
                             |
                             v
                     Block 86 control plane

## Safety rules

1. Provider failure returns an unavailable packet, never a synthetic price.
2. STALE, FALLBACK, and INVALID are observable diagnostic states but are
   blocked from live scoring.
3. The execution engine no longer substitutes 2500.0 when a market price is
   missing.
4. Block 85 requires live market evidence before execution certification.
5. Existing Block 86 non-bypass governance remains the final control layer.
6. Tests inject deterministic provider doubles; production uses the real provider.

## Next reconstruction step

With the market-data boundary repaired, EROS can proceed upward through the
existing scoring/decision/execution chain without creating another parallel
market-data implementation.

The next implementation target is therefore live-data-driven scoring and
decision lineage, not another market-data adapter.
