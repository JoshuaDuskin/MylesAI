# Myles Quant stack

Myles Quant combines Drift market research on Solana, simulated forward-paper trading, copy-trader shadow research, and a separately owner-gated live adapter. Component versions are reported by the running services.

## Architecture

- **Research and paper engine:** `quant_service.mjs`
- **Drift paper adapter:** `drift_adapter.mjs`
- **Drift copy research:** `drift_copy_adapter.mjs` and `copy_trader_service.mjs`
- **Dashboard transport:** authenticated Myles tower bridge
- **Network:** Solana mainnet-beta
- **Venue:** Drift perps through the public Velocity Data API
- **Execution:** paper only; wallet signing and live execution are hard-locked

## Paper workflow

1. The engine reads Drift candles for BTC-PERP, ETH-PERP, and SOL-PERP.
2. Candidate strategies are evaluated with fees, slippage, market impact, and a doubled-cost stress run.
3. Walk-forward results and a minimum trade count are required before a strategy can open a paper position.
4. The adaptive governor may rotate a market to a better validated candidate; it cannot change risk bounds or unlock live execution.
5. Drift leaderboard accounts are discovered and shadow-tested separately. A trader is never copied into a live wallet by this service.

## Safety model

Paper positions are simulated and cannot move funds. There is no owner private key or seed phrase in GitHub, the browser source, or Myles's config. Live execution remains disabled until a separate owner review and explicit authorization flow exist.

Paper defaults are conservative: 0.5% risk per trade, 1.5x maximum notional leverage, two concurrent positions, 1.5% stops, 3% targets, and an 8% maximum drawdown halt. A candidate that fails the evidence gate remains a research hypothesis and cannot open a paper position.

## Research versus paper performance safety

An unvalidated research or shadow signal is recorded separately and never becomes an automatic paper order. Existing trades, equity history, and paper balances are preserved. Drawdown stops require an explicit owner reset. These controls improve evidence quality and risk containment; they do not guarantee returns.
