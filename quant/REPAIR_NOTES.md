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

## Multi-timeframe upgrade, core 10.15.18

Public trader feed coverage counts observed position markets, not disconnected
providers. Discovery observes up to ten candidate accounts without selecting them
for copy execution. Public collateral/leverage and incomplete performance evidence
are visible; leaderboard P&L is never relabeled as realized return.

Coinbase research now evaluates five families over 1m, 5m, 15m, 1h, 4h and 1d
for five assets. History is paginated, deduplicated, checked for missing bars and
aggregated from contiguous hours for 4h. Stress/walk-forward gates are unchanged.
These spot proxies cannot automatically enter the Drift perpetual portfolio.
Unknown actual historical funding remains explicitly modeled carrying cost.

Failed Polymarket and trader refreshes retain observation timestamps. Paper
orders validate available margin including fees, position caps and explicit size
limits. Stale execution marks cannot open or trigger mark-based exits. Charts
respect selected time ranges without falling back to older data. Retained closed
trades provide strategy totals. Live order previews are calculations only and
reject stale quotes; all execution remains locked. Cross margin is unavailable
in this isolated paper simulator and is not advertised as supported.

## Chat and evidence upgrade, core 10.15.19

Outgoing messages render and persist before a network wait. Per-request client
identifiers reconcile local pending messages, shared history and durable delivery
states. New requests receive a bounded asynchronous 202 acknowledgment. GET polls
read delivery state separately from inference/action execution. Requests remain
idempotent after reconnect; uncertain interrupted actions fail explicitly and are
not silently repeated. Owner requests remain owner-authenticated, public requests
use only the existing public app allowlist. Known durable owner jobs resume status
tracking after bridge restart. Local history caches are separated by access scope.
Public text responses use real Ollama streaming chunks, observed by the dashboard
through its short progress polls. Incomplete streams fail explicitly, and gameplay
interrupts inference. Existing owner/core conversation calls remain non-streaming.
The browser never simulates tokens or invents progress.

Research drawdown includes starting capital. Historical entry/equity timestamps
reflect completed candle closes. Expanded spot-proxy research applies hour/day
EMA context only from higher-period candles already closed at each decision, with
no future-data access. Expectancy, profit factor and sample counts are retained.
Sharpe/Sortino are null for insufficient or irregular samples; they are descriptive
statistics, not confidence probabilities. Per-strategy exposure caps are optional
and owner-configurable; previous risk settings and paper history are preserved.
New equity observations retain realized/unrealized P&L and exposure summaries;
missing historical components are never reconstructed. Kraken/Coinbase volumes
retain their base-asset unit rather than being mislabeled as dollar volume.

The dashboard starts dark before its first paint, improves text contrast and focus
states, separates Live and Predictions, and retains expanded detail state. Plain
research findings precede advanced tables. A BOM-aware manifest comparison avoids
Windows-authored bridge.json being falsely treated as stale on every supervisor
cycle. Fortnite pause, controller services, wallet data and live execution locks
are unchanged. No actual historical order-book/funding data or unsupported cross
margin is implied by the new statistics.

Worker discovery now checks executable/script arguments and canonical containment rather than matching filenames mentioned in arbitrary command lines. Public history size bounds account for encoded Unicode rather than silently discarding a valid retained conversation.
