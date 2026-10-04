import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { GmxApiSdk } = require('@gmx-io/sdk/v2');

const ROOT = process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, 'MylesAI') : path.join(os.homedir(), 'AppData', 'Local', 'MylesAI');
const DATA = path.join(ROOT, 'data');
const QUANT = path.join(ROOT, 'quant');
const CONFIG_FILE = path.join(DATA, 'copy_trader_config.json');
const STATUS_FILE = path.join(DATA, 'copy_trader_status.json');
const QUANT_STATUS_FILE = path.join(DATA, 'trading_status.json');
const QUANT_SCRIPT = path.join(QUANT, 'quant_service.mjs');
const LIVE_STATUS_FILE = path.join(DATA, 'gmx_live_status.json');
const LIVE_SCRIPT = path.join(QUANT, 'gmx_live.mjs');
const LIVE_COPY_STATE_FILE = path.join(DATA, 'copy_trader_live_state.json');
const API = 'https://arbitrum.gmxapi.io/v1';
const VERSION = '0.9.0';
const CHAIN_ID = 42161;
const SYMBOLS = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'TAO/USD'];
const sdk = new GmxApiSdk({ chainId: CHAIN_ID });

const iso = () => new Date().toISOString();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, Number(v)));
const readJson = (file, fallback = null) => { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; } };
function writeJson(file, value) { fs.mkdirSync(path.dirname(file), { recursive: true }); const tmp = `${file}.tmp-${process.pid}`; fs.writeFileSync(tmp, JSON.stringify(value, null, 2)); fs.renameSync(tmp, file); }
function address(value) { const s = String(value || '').toLowerCase(); return /^0x[0-9a-f]{40}$/.test(s) ? s : null; }
function usd30(value) { try { return Number(BigInt(String(value || 0))) / 1e30; } catch { return Number(value || 0); } }
function defaults() { return { version: VERSION, enabled: true, auto_discovery: true, auto_select: true, shadow_copy_enabled: true, live_copy_enabled: false, discovery_period_days: 30, validation_period_days: 90, discovery_interval_seconds: 900, max_candidates: 20, max_selected_traders: 3, min_closed_trades: 12, min_win_rate_pct: 52, min_score: 55, max_copy_positions: 2, copy_margin_usd: 25, copy_leverage: 1.25, stop_loss_pct: 1.0, take_profit_pct: 2.0, poll_seconds: 60, selected_accounts: [] }; }
function config() { const d = defaults(), x = readJson(CONFIG_FILE, {}); return { ...d, ...x, selected_accounts: Array.isArray(x.selected_accounts) ? x.selected_accounts.map(address).filter(Boolean) : [] }; }
function saveConfig(input) {
  const old = config(), x = input?.config && typeof input.config === 'object' ? input.config : input;
  if (!x || typeof x !== 'object') throw new Error('config object required');
  const next = { ...old, ...x, version: VERSION, live_copy_enabled: x.live_copy_enabled === undefined ? old.live_copy_enabled : !!x.live_copy_enabled };
  next.selected_accounts = Array.isArray(x.selected_accounts) ? [...new Set(x.selected_accounts.map(address).filter(Boolean))].slice(0, 10) : old.selected_accounts;
  next.max_selected_traders = Math.round(clamp(next.max_selected_traders, 1, 5));
  next.min_closed_trades = Math.round(clamp(next.min_closed_trades, 5, 200));
  next.min_win_rate_pct = clamp(next.min_win_rate_pct, 0, 100);
  next.min_score = clamp(next.min_score, 0, 100);
  next.max_copy_positions = Math.round(clamp(next.max_copy_positions, 1, 5));
  next.copy_margin_usd = clamp(next.copy_margin_usd, 1, 1000);
  next.copy_leverage = clamp(next.copy_leverage, 1, 1.5);
  next.stop_loss_pct = clamp(next.stop_loss_pct, .25, 5);
  next.take_profit_pct = clamp(next.take_profit_pct, .25, 12);
  next.discovery_interval_seconds = Math.round(clamp(next.discovery_interval_seconds, 300, 21600));
  next.poll_seconds = Math.round(clamp(next.poll_seconds, 30, 1800));
  writeJson(CONFIG_FILE, next); return next;
}

async function api(pathname, options = {}) {
  let last;
  for (const base of [API, 'https://arbitrum.gmxapi.ai/v1']) {
    for (let attempt = 1; attempt <= 2; attempt += 1) {
      try { const r = await fetch(`${base}${pathname}`, { ...options, headers: { accept: 'application/json', ...(options.body ? { 'content-type': 'application/json' } : {}), ...(options.headers || {}) }, signal: AbortSignal.timeout(20000) }); if (!r.ok) throw new Error(`HTTP ${r.status}`); return await r.json(); } catch (e) { last = e; if (attempt < 2) await sleep(500 * attempt); }
    }
  }
  throw last || new Error('GMX API unavailable');
}
function realizedRows(rows) { return (rows || []).filter(t => t && t.pnlUsd !== undefined && String(t.eventName || '') === 'OrderExecuted' && [4, 5, 6, 7].includes(Number(t.orderType))); }
function metrics(account, trades, days) {
  const rows = realizedRows(trades), pnls = rows.map(x => usd30(x.pnlUsd)).filter(Number.isFinite), total = pnls.reduce((a, b) => a + b, 0), wins = pnls.filter(x => x > 0).length;
  let curve = 0, peak = 0, maxDrawdown = 0, grossWin = 0, grossLoss = 0;
  for (const pnl of pnls.slice().reverse()) { curve += pnl; peak = Math.max(peak, curve); maxDrawdown = Math.max(maxDrawdown, peak - curve); if (pnl > 0) grossWin += pnl; else grossLoss += Math.abs(pnl); }
  const winRate = pnls.length ? wins / pnls.length * 100 : 0, profitFactor = grossLoss > 0 ? grossWin / grossLoss : grossWin > 0 ? 9.99 : 0;
  const consistency = Math.max(0, 100 - (maxDrawdown / Math.max(1, grossWin)) * 100);
  const score = clamp((total > 0 ? 20 : 0) + Math.min(25, pnls.length / 2) + Math.min(20, winRate * .25) + Math.min(20, profitFactor * 8) + Math.min(15, consistency * .15), 0, 100);
  return { account, period_days: days, closed_trades: pnls.length, realized_pnl_usd: Number(total.toFixed(2)), win_rate_pct: Number(winRate.toFixed(2)), profit_factor: Number(profitFactor.toFixed(2)), max_realized_drawdown_usd: Number(maxDrawdown.toFixed(2)), consistency_pct: Number(consistency.toFixed(2)), score: Number(score.toFixed(2)), last_trade_at: rows[0]?.timestamp ? new Date(Number(rows[0].timestamp) * 1000).toISOString() : null };
}
async function tradesFor(account, days, limit = 300) { const since = Math.floor(Date.now() / 1000) - days * 86400; const q = new URLSearchParams({ address: account, since: String(since), limit: String(Math.min(300, limit)) }); const x = await api(`/trades?${q}`); return x.trades || []; }
async function discover(cfg) {
  const since = Math.floor(Date.now() / 1000) - cfg.discovery_period_days * 86400;
  const raw = await api('/trades/search', { method: 'POST', body: JSON.stringify({ forAllAccounts: true, fromTimestamp: since, limit: 300, showDebugValues: false }) });
  const counts = new Map(); for (const t of realizedRows(raw.trades || [])) { const a = address(t.account); if (a) counts.set(a, (counts.get(a) || 0) + 1); }
  const seed = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, cfg.max_candidates).map(x => x[0]);
  const candidates = [];
  for (const a of seed) { try { candidates.push(metrics(a, await tradesFor(a, cfg.validation_period_days), cfg.validation_period_days)); } catch (e) { candidates.push({ account: a, error: String(e?.message || e), score: 0 }); } await sleep(80); }
  candidates.sort((a, b) => Number(b.score || 0) - Number(a.score || 0));
  const qualified = candidates.filter(x => x.realized_pnl_usd > 0 && x.closed_trades >= cfg.min_closed_trades && x.win_rate_pct >= cfg.min_win_rate_pct && x.score >= cfg.min_score);
  if (cfg.auto_select && !cfg.selected_accounts.length) { cfg.selected_accounts = qualified.slice(0, cfg.max_selected_traders).map(x => x.account); writeJson(CONFIG_FILE, cfg); }
  return { candidates, qualified, selected_accounts: cfg.selected_accounts };
}
function normalizePosition(p) { const name = String(p?.indexName || p?.market?.name || p?.marketName || ''); const symbol = SYMBOLS.find(s => name.startsWith(s)); if (!symbol) return null; const size = usd30(p.sizeInUsd || 0), collateral = usd30(p.collateralUsd || p.remainingCollateralUsd || 0); return { symbol, side: p.isLong ? 'long' : 'short', size_usd: size, collateral_usd: collateral, leverage: collateral > 0 ? size / collateral : 1 }; }
async function sourcePositions(selected, candidateMap) {
  const out = [];
  for (const account of selected) { try { const rows = await sdk.fetchPositionsInfo({ address: account, includeRelatedOrders: false }); const rank = candidateMap.get(account)?.score || 50; for (const p of rows || []) { const x = normalizePosition(p); if (x) out.push({ ...x, account, trader_score: rank }); } } catch (e) { out.push({ account, error: String(e?.message || e) }); } }
  return out;
}
function consensus(rows) {
  const perTrader = new Map();
  for (const p of rows.filter(x => x.symbol && x.side && x.account)) { const key = `${p.account}|${p.symbol}`, x = perTrader.get(key) || { account: p.account, symbol: p.symbol, long_size: 0, short_size: 0, trader_score: Number(p.trader_score || 50) }; x[`${p.side}_size`] += Number(p.size_usd || 0); perTrader.set(key, x); }
  const grouped = new Map();
  for (const p of perTrader.values()) { if (p.long_size === p.short_size) continue; const side = p.long_size > p.short_size ? 'long' : 'short', g = grouped.get(p.symbol) || { long: 0, short: 0, sources: [] }; g[side] += p.trader_score; g.sources.push({ ...p, side }); grouped.set(p.symbol, g); }
  const result = [];
  for (const [symbol, g] of grouped) { const total = g.long + g.short, side = g.long >= g.short ? 'long' : 'short', winning = Math.max(g.long, g.short), confidence = total ? winning / total : 0; if (confidence >= .6) result.push({ symbol, side, confidence: Number((confidence * 100).toFixed(1)), source_count: g.sources.filter(x => x.side === side).length, accounts: [...new Set(g.sources.filter(x => x.side === side).map(x => x.account))] }); }
  return result;
}
function quantAction(payload) { const r = spawnSync(process.execPath, [QUANT_SCRIPT, '--manual-order', JSON.stringify(payload)], { cwd: QUANT, encoding: 'utf8', windowsHide: true, timeout: 150000 }); const line = String(r.stdout || r.stderr || '').trim().split(/\r?\n/).filter(Boolean).at(-1); let parsed = {}; try { parsed = JSON.parse(line || '{}'); } catch { parsed = { ok: false, error: line || `exit ${r.status}` }; } if (r.status !== 0 || parsed.ok === false) throw new Error(parsed.error || `Quant exit ${r.status}`); return parsed; }
function liveAction(payload) { const r = spawnSync(process.execPath, [LIVE_SCRIPT, '--order', JSON.stringify(payload)], { cwd: QUANT, encoding: 'utf8', windowsHide: true, timeout: 190000 }); const line = String(r.stdout || r.stderr || '').trim().split(/\r?\n/).filter(Boolean).at(-1); let parsed = {}; try { parsed = JSON.parse(line || '{}'); } catch { parsed = { ok: false, error: line || `exit ${r.status}` }; } if (r.status !== 0 || parsed.ok === false) throw new Error(parsed.error || `Live executor exit ${r.status}`); return parsed; }
function freshLiveStatus() { const r = spawnSync(process.execPath, [LIVE_SCRIPT, '--status'], { cwd: QUANT, encoding: 'utf8', windowsHide: true, timeout: 60000 }); const line = String(r.stdout || r.stderr || '').trim().split(/\r?\n/).filter(Boolean).at(-1); let parsed = {}; try { parsed = JSON.parse(line || '{}'); } catch { parsed = { ok: false, error: line || `exit ${r.status}` }; } if (r.status !== 0 || parsed.ok === false) throw new Error(parsed.error || `Live status exit ${r.status}`); return parsed; }
function shadowCopy(cfg, signals) {
  const q = readJson(QUANT_STATUS_FILE, {}), open = Array.isArray(q.positions) ? q.positions : [], copyOpen = open.filter(x => x.source === 'copy'), actions = [];
  for (const p of copyOpen) { const sig = signals.find(x => x.symbol === p.symbol); if (!sig || sig.side !== p.side) { try { quantAction({ action: 'close', symbol: p.symbol, source: 'copy' }); actions.push({ action: 'close', symbol: p.symbol }); } catch (e) { actions.push({ action: 'close', symbol: p.symbol, error: String(e?.message || e) }); } } }
  const refreshed = readJson(QUANT_STATUS_FILE, {}), positions = Array.isArray(refreshed.positions) ? refreshed.positions : [];
  for (const sig of signals) { if (positions.some(x => x.symbol === sig.symbol) || positions.filter(x => x.source === 'copy').length + actions.filter(x => x.action === 'open' && !x.error).length >= cfg.max_copy_positions) continue; try { quantAction({ action: 'open', symbol: sig.symbol, side: sig.side, margin_usd: cfg.copy_margin_usd, leverage: cfg.copy_leverage, stop_loss_pct: cfg.stop_loss_pct, take_profit_pct: cfg.take_profit_pct, source: 'copy', strategy: `copy:${sig.accounts.join(',')}` }); actions.push({ action: 'open', ...sig }); } catch (e) { actions.push({ action: 'open', ...sig, error: String(e?.message || e) }); } }
  return actions;
}
function liveCopy(cfg, signals) {
  let live = readJson(LIVE_STATUS_FILE, {}), auth = live.copy_trading || {}, now = Math.floor(Date.now() / 1000), actions = [];
  if (!cfg.live_copy_enabled || !live.armed || !auth.enabled || Number(auth.authorized_until || 0) <= now) return actions;
  try { live = freshLiveStatus(); auth = live.copy_trading || {}; } catch (e) { return [{ action: 'skip', reason: 'live_status_unavailable', error: String(e?.message || e) }]; }
  if (!live.armed || !auth.enabled || Number(auth.authorized_until || 0) <= now) return actions;
  const authorized = new Set((auth.authorized_accounts || []).map(address).filter(Boolean));
  const selected = (cfg.selected_accounts || []).map(address).filter(Boolean);
  if (!selected.length || selected.some(a => !authorized.has(a))) return [{ action: 'skip', reason: 'selected_traders_not_owner_authorized' }];
  const usableSignals = signals.filter(s => Array.isArray(s.accounts) && s.accounts.length && s.accounts.every(a => authorized.has(address(a))));
  const state = readJson(LIVE_COPY_STATE_FILE, { positions: {} }); state.positions = state.positions || {};
  let current = Array.isArray(live.positions) ? live.positions.filter(x => x && !x.error) : [];
  for (const [symbol, tracked] of Object.entries({ ...state.positions })) {
    const position = current.find(x => x.symbol === symbol && x.side === tracked.side);
    if (!position) { delete state.positions[symbol]; continue; }
    const sig = usableSignals.find(x => x.symbol === symbol);
    if (!sig || sig.side !== tracked.side) {
      const exact = tracked.position_key && String(position.key || '') === String(tracked.position_key) && String(position.raw_size_usd || '') === String(tracked.raw_size_usd || '') && String(position.entry_price ?? '') === String(tracked.entry_price ?? '');
      if (!exact) { actions.push({ action: 'skip_close', symbol, reason: 'position_fingerprint_changed_manual_overlap_possible' }); continue; }
      try { liveAction({ action: 'close', symbol, side: tracked.side, source: 'copy' }); actions.push({ action: 'close', symbol, side: tracked.side }); current = current.filter(x => x !== position); delete state.positions[symbol]; }
      catch (e) { actions.push({ action: 'close', symbol, side: tracked.side, error: String(e?.message || e) }); }
    }
  }
  for (const sig of usableSignals) {
    if (state.positions[sig.symbol] || current.some(x => x.symbol === sig.symbol) || Object.keys(state.positions).length >= Number(auth.max_open_positions || 1)) continue;
    try {
      liveAction({ action: 'open', symbol: sig.symbol, side: sig.side, margin_usd: Number(auth.max_margin_usd), leverage: Number(auth.max_leverage), stop_loss_pct: Number(auth.stop_loss_pct), take_profit_pct: Number(auth.take_profit_pct), source: 'copy' });
      let fingerprint = {}; try { const refreshed = freshLiveStatus(), p = (refreshed.positions || []).find(x => x.symbol === sig.symbol && x.side === sig.side); if (p) fingerprint = { position_key: p.key, raw_size_usd: p.raw_size_usd, entry_price: p.entry_price }; } catch {}
      state.positions[sig.symbol] = { side: sig.side, accounts: sig.accounts.map(address).filter(Boolean), opened_at: iso(), ...fingerprint };
      actions.push({ action: 'open', symbol: sig.symbol, side: sig.side, accounts: sig.accounts });
    } catch (e) { actions.push({ action: 'open', symbol: sig.symbol, side: sig.side, error: String(e?.message || e) }); }
  }
  state.updated_at = iso(); writeJson(LIVE_COPY_STATE_FILE, state); return actions;
}
async function cycle(forceDiscovery = false) {
  const cfg = config(), previous = readJson(STATUS_FILE, {}); if (!cfg.enabled) return previous;
  let discovery = { candidates: previous.candidates || [], qualified: previous.qualified || [], selected_accounts: cfg.selected_accounts }, didDiscover = false;
  const age = Date.now() - Date.parse(previous.discovery_at || 0); if (forceDiscovery || cfg.auto_discovery && (!Number.isFinite(age) || age > cfg.discovery_interval_seconds * 1000)) { discovery = await discover(cfg); didDiscover = true; }
  const selected = cfg.selected_accounts.length ? cfg.selected_accounts : discovery.selected_accounts || [], map = new Map((discovery.candidates || []).map(x => [x.account, x]));
  const positions = await sourcePositions(selected, map), signals = consensus(positions), actions = cfg.shadow_copy_enabled ? shadowCopy(cfg, signals) : [], liveActions = liveCopy(cfg, signals), liveStatus = readJson(LIVE_STATUS_FILE, {}), liveActive = !!(cfg.live_copy_enabled && liveStatus.armed && liveStatus.copy_trading?.enabled && Number(liveStatus.copy_trading?.authorized_until || 0) > Math.floor(Date.now() / 1000));
  const generated=iso(),status = { ok: true, version: VERSION, generated_at: generated, discovery_at: didDiscover ? generated : previous.discovery_at, next_discovery_at: new Date(Date.now() + cfg.discovery_interval_seconds * 1000).toISOString(), data_source: 'GMX official API and SDK', source_health: { gmx_api: { available: true, endpoint: API, updated_at: generated }, gmx_sdk: { available: true, updated_at: generated } }, research_findings: { candidates: discovery.candidates?.length || 0, qualified: discovery.qualified?.length || 0, consensus_signals: signals.length, shadow_actions: actions.length, live_actions: liveActions.length, statement: signals.length ? `${signals.length} current GMX trader-consensus signal(s) are being shadow-tested.` : 'No qualified trader consensus is present; no paper copy entry is manufactured.' }, mode: liveActive ? 'owner_authorized_live_copy' : 'paper_shadow_copy', live_copy_enabled: liveActive, safety_note: liveActive ? 'REAL GMX copying is active only for the owner-signed trader list and risk envelope. Manual positions are never adopted or closed by copy trading.' : 'Live copy is off. Paper shadow-copy may continue independently.', config: cfg, selected_accounts: selected, candidates: discovery.candidates || [], qualified: discovery.qualified || [], source_positions: positions, signals, recent_actions: actions, recent_live_actions: liveActions };
  writeJson(STATUS_FILE, status); return status;
}
async function main() { const args = process.argv.slice(2), payload = flag => { const i = args.indexOf(flag); return i >= 0 ? JSON.parse(args[i + 1] || '{}') : null; }; try { if (args.includes('--status')) { console.log(JSON.stringify(readJson(STATUS_FILE, { ok: true, version: VERSION, generated_at: null, candidates: [], signals: [] }))); return; } const p = payload('--config'); if (p) { const c = saveConfig(p); console.log(JSON.stringify({ ok: true, config: c })); return; } if (args.includes('--discover')) { console.log(JSON.stringify(await cycle(true))); return; } if (args.includes('--once')) { console.log(JSON.stringify(await cycle(false))); return; } if (args.includes('--daemon')) { for (;;) { try { await cycle(false); } catch (e) { writeJson(STATUS_FILE, { ...readJson(STATUS_FILE, {}), ok: false, generated_at: iso(), error: String(e?.message || e) }); } await sleep(config().poll_seconds * 1000); } } console.log(JSON.stringify({ ok: true, version: VERSION })); } catch (e) { console.error(JSON.stringify({ ok: false, error: String(e?.message || e) })); process.exit(2); } }
main();
