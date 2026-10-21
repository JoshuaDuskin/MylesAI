import fs from 'node:fs';
import path from 'node:path';

const API = (process.env.DRIFT_DATA_API_URL || 'https://data.velocity.exchange').replace(/\/$/, '');
const ALLOWED_SYMBOLS = new Set(['SOL-PERP', 'BTC-PERP', 'ETH-PERP']);

const iso = () => new Date().toISOString();
const n = (value, fallback = 0) => {
  const x = Number(value);
  return Number.isFinite(x) ? x : fallback;
};
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, n(v, lo)));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const readJson = (file, fallback = null) => { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; } };
const writeJson = (file, value) => { fs.mkdirSync(path.dirname(file), { recursive: true }); const tmp = `${file}.tmp-${process.pid}`; fs.writeFileSync(tmp, JSON.stringify(value, null, 2)); fs.renameSync(tmp, file); };

async function api(pathname) {
  const response = await fetch(`${API}${pathname}`, { headers: { accept: 'application/json', 'user-agent': 'MylesQuant/DriftCopyPaper' }, signal: AbortSignal.timeout(20000) });
  const body = await response.text();
  if (!response.ok) throw new Error(`Drift Data API HTTP ${response.status}: ${body.slice(0, 240)}`);
  return JSON.parse(body);
}

function scoreCandidate(row, tradeCount) {
  const pnl = n(row.pnl), volume = n(row.volume);
  return Number(clamp((pnl > 0 ? 35 : 0) + Math.min(30, Math.max(0, pnl) / 200) + Math.min(20, volume / 2500) + Math.min(15, tradeCount / 2), 0, 100).toFixed(2));
}

async function accountForAuthority(authority) {
  const raw = await api(`/authority/${encodeURIComponent(authority)}/accounts`);
  return raw.accounts?.[0] || null;
}

async function discover(cfg) {
  const raw = await api(`/stats/leaderboard?limit=${Math.min(100, Math.max(1, Math.trunc(n(cfg.max_candidates, 20))))}&sort=pnl`);
  const rows = Array.isArray(raw?.data?.leaderboard) ? raw.data.leaderboard : [];
  const candidates = [];
  for (const row of rows) {
    try {
      const account = await accountForAuthority(row.authority);
      if (!account?.accountId) continue;
      const trades = await api(`/user/${encodeURIComponent(account.accountId)}/trades`);
      const user = await api(`/user/${encodeURIComponent(account.accountId)}`);
      const tradeCount = Array.isArray(trades?.records) ? trades.records.length : 0;
      const positions = Array.isArray(user?.positions) ? user.positions.filter(p => ALLOWED_SYMBOLS.has(p.symbol)).length : 0;
      candidates.push({
        account: account.accountId,
        authority: row.authority,
        period_days: cfg.validation_period_days,
        closed_trades: tradeCount,
        realized_pnl_usd: Number(n(row.pnl).toFixed(2)),
        volume_usd: Number(n(row.volume).toFixed(2)),
        open_markets: positions,
        score: scoreCandidate(row, tradeCount),
        last_trade_at: trades?.records?.[0]?.ts ? new Date(n(trades.records[0].ts) * 1000).toISOString() : null,
      });
    } catch (error) {
      candidates.push({ account: null, authority: row.authority, score: 0, error: String(error?.message || error) });
    }
    await sleep(60);
  }
  candidates.sort((a, b) => n(b.score) - n(a.score));
  const qualified = candidates.filter(x => x.account && x.realized_pnl_usd > 0 && x.closed_trades >= n(cfg.min_closed_trades, 12) && x.score >= n(cfg.min_score, 55));
  const selected = cfg.auto_select && !cfg.selected_accounts.length ? qualified.slice(0, n(cfg.max_selected_traders, 3)).map(x => x.account) : cfg.selected_accounts;
  if (selected.length && JSON.stringify(selected) !== JSON.stringify(cfg.selected_accounts)) {
    cfg.selected_accounts = selected;
    const saved = { ...cfg };
    delete saved.__file;
    writeJson(cfg.__file, saved);
  }
  return { candidates, qualified, selected_accounts: selected };
}

async function priceMap() {
  const raw = await api('/stats/markets');
  return new Map((raw?.markets || []).filter(x => ALLOWED_SYMBOLS.has(x.symbol)).map(x => [x.symbol, n(x.oraclePrice || x.markPrice || x.price)]));
}

async function sourcePositions(selected, candidateMap) {
  const prices = await priceMap(), output = [];
  for (const account of selected) {
    try {
      const user = await api(`/user/${encodeURIComponent(account)}`);
      const collateral = n(user?.account?.totalCollateral);
      for (const position of user?.positions || []) {
        if (!ALLOWED_SYMBOLS.has(position.symbol)) continue;
        const base = n(position.baseAssetAmount), price = n(prices.get(position.symbol));
        if (!base || !price) continue;
        const size = Math.abs(base) * price;
        output.push({ account, symbol: position.symbol, side: base > 0 ? 'long' : 'short', size_usd: Number(size.toFixed(4)), collateral_usd: collateral, leverage: collateral > 0 ? Number((size / collateral).toFixed(3)) : 1, trader_score: n(candidateMap.get(account)?.score, 50), source: 'drift_leaderboard' });
      }
    } catch (error) {
      output.push({ account, error: String(error?.message || error) });
    }
  }
  return output;
}

function consensus(rows) {
  const grouped = new Map();
  for (const row of rows.filter(x => x.symbol && x.side && x.account)) {
    const item = grouped.get(row.symbol) || { long: 0, short: 0, longAccounts: [], shortAccounts: [] };
    item[row.side] += n(row.trader_score, 50);
    item[`${row.side}Accounts`].push(row.account);
    grouped.set(row.symbol, item);
  }
  return [...grouped.entries()].flatMap(([symbol, item]) => {
    const total = item.long + item.short;
    if (!total) return [];
    const side = item.long >= item.short ? 'long' : 'short';
    const confidence = Math.max(item.long, item.short) / total;
    if (confidence < 0.6) return [];
    const accounts = [...new Set(item[`${side}Accounts`])];
    return [{ symbol, side, confidence: Number((confidence * 100).toFixed(1)), source_count: accounts.length, accounts }];
  });
}

export async function runDriftCopyCycle({ config, previous = {}, forceDiscovery = false, configFile, shadowCopy, liveCopy }) {
  const cfg = { ...config, __file: configFile };
  let discovery = { candidates: previous.candidates || [], qualified: previous.qualified || [], selected_accounts: cfg.selected_accounts || [] };
  let discoveryAt = previous.discovery_at || null;
  const ageMs = Date.now() - Date.parse(discoveryAt || 0);
  if (forceDiscovery || (cfg.auto_discovery && (!Number.isFinite(ageMs) || ageMs > n(cfg.discovery_interval_seconds, 900) * 1000))) {
    discovery = await discover(cfg);
    discoveryAt = iso();
  }
  const selected = cfg.selected_accounts?.length ? cfg.selected_accounts : discovery.selected_accounts || [];
  const map = new Map((discovery.candidates || []).map(x => [x.account, x]));
  const positions = await sourcePositions(selected, map);
  const signals = consensus(positions);
  const actions = cfg.shadow_copy_enabled ? shadowCopy(cfg, signals) : [];
  const liveActions = cfg.live_copy_enabled ? liveCopy(cfg, signals) : [];
  const liveActive = false;
  const generated = iso();
  return {
    ok: true,
    version: '0.10.0-drift-paper-copy',
    generated_at: generated,
    discovery_at: discoveryAt,
    next_discovery_at: new Date(Date.now() + n(cfg.discovery_interval_seconds, 900) * 1000).toISOString(),
    data_source: 'Drift/Velocity public Data API',
    source_health: { drift_api: { available: true, endpoint: API, updated_at: generated } },
    research_findings: { candidates: discovery.candidates?.length || 0, qualified: discovery.qualified?.length || 0, consensus_signals: signals.length, shadow_actions: actions.length, live_actions: 0, statement: signals.length ? `${signals.length} Drift trader-consensus signal(s) are being shadow-tested.` : 'No verified Drift consensus signal is present.' },
    mode: 'paper_shadow_copy',
    live_copy_enabled: liveActive,
    safety_note: 'Drift copy research is paper-only. Live copy and wallet signing are disabled until separately validated and owner-authorized.',
    config: { ...cfg, __file: undefined },
    selected_accounts: selected,
    candidates: discovery.candidates || [],
    qualified: discovery.qualified || [],
    source_positions: positions,
    signals,
    recent_actions: actions,
    recent_live_actions: [],
  };
}
