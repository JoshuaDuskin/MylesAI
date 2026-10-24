# Quant repair, core 10.15.17

The canonical dashboard and runtime remain in JoshuaDuskin/MylesAI. MylesDashboard is retired; do not build a parallel dashboard.

## Feeds and research

The existing Quant cycle now polls GMX `/markets/tickers`, Kraken public Ticker,
and Coinbase Exchange tickers. Observations cover BTC, ETH, SOL, XRP and TAO where
actually available. Health requires valid observations, expires after 180 seconds,
and includes the last error and a capped exponential retry deadline. No provider
is marked working merely because it is configured. These feeds use REST, not a
WebSocket connection. Quotes are cross-venue research inputs; Drift remains the
paper execution source.

Completed Coinbase hourly candles support supplemental momentum, mean reversion,
scalping, breakout and volatility research. Each candidate includes base,
stressed-cost and walk-forward results. Supplemental candidates cannot open
positions in the preserved Drift account. Funding observations keep their native
provider units; no executable funding-arbitrage edge is claimed.

## Paper accounting and risk

Paper cash, realized net P&L, unrealized P&L, open entry fees, margin and equity
are reported separately. Winning closed trades determine win rate; open gains
do not. Historical balances and fills are not reset or reconstructed. Older
records without fee details remain explicitly incomplete. New closes record
entry/exit fees and modeled carrying costs. Carrying costs are not represented
as actual venue funding payments.

Paper leverage is configurable up to 20x and is capped again by the observed
market limit at entry; unknown limits restrict new entries to 1x. Profiles are
editable paper presets, not profitability claims. Aggregate available margin,
concurrent-position caps, per-trade limits, trailing stops, current-mark stops,
daily loss, drawdown and emergency stops remain enforced. Cross margin is not
implemented. Liquidation prices are isolated estimates with an assumed 0.5%
maintenance reserve and 0.1% fee reserve, not exchange liquidation quotes.

Live configuration remains visible. The GMX adapter is explicitly review-locked:
setup, authorization, transfers and order actions fail before execution. No real
order, wallet permission, approval, deposit or withdrawal is performed by repair.
Wallet balance reads use the user's connected EIP-1193 wallet on Arbitrum. An
unconnected account reports unavailable rather than a fabricated zero balance.
Transaction history links to the connected address's public Arbiscan history;
an in-app indexed transfer ledger and deposit QR remain unavailable.

## Prediction markets and copy research

International Gamma research includes probabilities, liquidity, spreads,
resolution criteria and observed probability history. A separate paper account
can simulate small probability-momentum positions only after three observations
and valid bid/ask/liquidity. Its explicit 1% per-side fee is an assumption,
not a provider fee quote. No CLOB order code is used. International geoblocking
and Polymarket US connectivity/eligibility are separate checks; a public catalog
response does not establish eligibility. No restriction is bypassed. A missing
US authorization is reported as unavailable. News correlation is not implemented.

Drift trader fills are labeled observed fills, not closed trades. Leaderboard
P&L is not labeled verified realized net P&L. Incomplete closed-position,
funding, fee, liquidation and survivorship evidence prevents automatic copy
qualification; discovery still reports what was observed. Live copy is disabled.

## Durable workers

Windows venv wrapper leases transfer atomically to the actual interpreter child.
The lease update API can clear/transfer a PID without argument collisions.
Startup has a timestamp and timeout even with a fresh heartbeat. Importing the
game watcher does not acquire its daemon singleton or exit the importing
updater. The `bin` package cannot silently merge helpers from another checkout.
Fortnite game mode and hidden launches remain in place.

## Official references

- [GMX integration guide](https://docs.gmx.io/docs/api/integration-guide/)
- [Kraken OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data)
- [Coinbase candles](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles)
- [Polymarket API](https://docs.polymarket.com/api-reference/predictions/overview)
- [Polymarket US data guide](https://docs.polymarket.us/data-guide/overview)
- [Polymarket geographic restrictions](https://help.polymarket.com/en/articles/13364163-geographic-restrictions)
