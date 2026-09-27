# Myles Quant v0.6.2

Myles Quant combines GMX market research, a chart-based scalp terminal, simulated forward-paper trading, and an owner-gated GMX live execution adapter.

## v0.6 architecture

- **Research / paper engine:** `quant_service.mjs`
- **GMX live adapter:** `gmx_live.mjs`
- **Dashboard transport:** authenticated Myles tower bridge
- **Network:** Arbitrum One (`42161`)
- **Funding asset:** USDC
- **Owner custody:** funds stay in the owner's wallet; the owner private key is never given to Myles
- **Trading delegation:** GMX One-Click Trading subaccount, derived from the owner wallet's GMX session signature
- **Subaccount secret at rest:** Windows DPAPI, CurrentUser scope, on the tower only
- **Live enablement:** explicit owner-wallet signature opens an 8-hour LIVE scalp session; a separate owner-wallet signature enables LIVE Auto
- **Manual live orders:** after the owner explicitly arms an 8-hour live session, manual open/close/cancel actions use the limited GMX one-click subaccount without another wallet popup; restart/expiry fails closed
- **Live risk changes:** max margin, notional, leverage, position count, and LIVE Auto sizing/stop/target limits are bound into a fresh owner-wallet signature before they can change
- **LIVE Auto qualification:** automatic live actions are ignored unless the selected market/strategy pair currently passes the Quant validation gate
- **Withdrawals:** always owner-wallet signed; Myles never receives withdrawal authority

## Live workflow

1. Open the canonical Myles Control Center and pair it to the tower.
2. Go to **Trading Bot → Funding**.
3. Open the page inside an injected-wallet browser (Coinbase Wallet / MetaMask mobile browser or a desktop wallet extension).
4. Connect the owner wallet and switch to Arbitrum One.
5. Choose **Set up one-click** and sign the two GMX authorization prompts.
6. Put USDC in that owner wallet on Arbitrum and approve USDC for the GMX router.
7. Explicitly **ARM LIVE EXECUTION**. This requires another owner-wallet signature.
8. Use **Trade → LIVE** for real manual Long/Short orders with attached stop-loss and take-profit orders. While the 8-hour owner-armed session is active, manual live actions are one-click; the owner wallet is not prompted for every scalp.
9. LIVE Auto remains OFF until separately enabled with another owner-wallet signature. Even when enabled, it only acts on closed-candle signals whose market/strategy research gate is currently passing.

## Safety model

The GMX one-click subaccount may execute only the authorized trading actions. The main wallet remains the account owner. The dashboard's withdraw flow creates a USDC transfer that the owner wallet itself must sign. There is no owner private key or seed phrase in GitHub, the browser source, or Myles's config.

Live defaults are intentionally conservative: $100 max margin per trade, $250 max notional, 2x max leverage, 2 concurrent positions, an 8-hour armed session, and LIVE Auto OFF. Any live-adapter restart automatically disarms both manual LIVE and LIVE Auto. The Advanced page exposes these limits, but changing them requires the configured owner wallet to sign the exact new limit set.
