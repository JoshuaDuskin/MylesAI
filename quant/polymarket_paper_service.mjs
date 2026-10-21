import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const ROOT = process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, 'MylesAI') : path.join(os.homedir(), 'AppData', 'Local', 'MylesAI');
const DATA = path.join(ROOT, 'data');
const STATUS_FILE = path.join(DATA, 'polymarket_paper_status.json');
const API = (process.env.POLYMARKET_GAMMA_API_URL || 'https://gamma-api.polymarket.com').replace(/\/$/, '');
const iso = () => new Date().toISOString();
const n = (v, fallback = 0) => { const x = Number(v); return Number.isFinite(x) ? x : fallback; };
const readJson = (file, fallback = null) => { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; } };
const writeJson = (file, value) => { fs.mkdirSync(path.dirname(file), { recursive: true }); const tmp = `${file}.tmp-${process.pid}`; fs.writeFileSync(tmp, JSON.stringify(value, null, 2)); fs.renameSync(tmp, file); };
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function api(pathname) {
  const response = await fetch(`${API}${pathname}`, { headers: { accept: 'application/json', 'user-agent': 'MylesPaperMonitor/1.0' }, signal: AbortSignal.timeout(20000) });
  const body = await response.text();
  if (!response.ok) throw new Error(`Polymarket Gamma API HTTP ${response.status}: ${body.slice(0, 240)}`);
  return JSON.parse(body);
}

function parseJson(value, fallback = []) {
  if (Array.isArray(value)) return value;
  try { const parsed = JSON.parse(String(value || '')); return Array.isArray(parsed) ? parsed : fallback; } catch { return fallback; }
}

function normalizeMarket(row) {
  const outcomes = parseJson(row.outcomes);
  const prices = parseJson(row.outcomePrices).map(n);
  const tokens = parseJson(row.clobTokenIds);
  const points = outcomes.map((outcome, i) => ({ outcome: String(outcome), price: n(prices[i]), token_id: tokens[i] || null })).filter(x => x.price > 0 && x.price < 1);
  const volume = n(row.volumeNum ?? row.volume);
  const liquidity = n(row.liquidityNum ?? row.liquidity);
  return {
    id: String(row.id || row.conditionId || ''),
    question: String(row.question || row.title || 'Untitled market'),
    slug: row.slug || null,
    end_date: row.endDate || row.end_date || null,
    volume_usd: Number(volume.toFixed(2)),
    liquidity_usd: Number(liquidity.toFixed(2)),
    outcomes: points,
    active: row.active !== false,
    closed: row.closed === true,
    url: row.slug ? `https://polymarket.com/event/${row.slug}` : null,
  };
}

function scoreMarket(market) {
  const depth = Math.min(40, Math.log10(Math.max(1, market.liquidity_usd)) * 10);
  const activity = Math.min(40, Math.log10(Math.max(1, market.volume_usd)) * 8);
  const tradable = market.outcomes.some(x => x.price >= 0.05 && x.price <= 0.95) ? 20 : 0;
  return Number(Math.min(100, depth + activity + tradable).toFixed(2));
}

function signalsFor(markets) {
  return markets.flatMap(market => {
    const candidate = market.outcomes.filter(x => x.price >= 0.05 && x.price <= 0.95).sort((a, b) => b.price - a.price)[0];
    if (!candidate || market.liquidity_usd < 1000 || market.volume_usd < 1000) return [];
    return [{ market_id: market.id, question: market.question, outcome: candidate.outcome, price: candidate.price, confidence: scoreMarket(market), action: 'paper_watch', rationale: 'Liquid active market surfaced for paper review; no order is submitted.' }];
  }).sort((a, b) => b.confidence - a.confidence).slice(0, 12);
}

export async function runPolymarketPaperCycle({ limit = 30 } = {}) {
  const query = new URLSearchParams({ active: 'true', closed: 'false', limit: String(Math.min(100, Math.max(1, Math.trunc(n(limit, 30))))), order: 'volumeNum', ascending: 'false' });
  const raw = await api(`/markets?${query}`);
  const rows = Array.isArray(raw) ? raw : (Array.isArray(raw?.data) ? raw.data : []);
  const markets = rows.map(normalizeMarket).filter(x => x.id && x.active && !x.closed);
  const signals = signalsFor(markets);
  const generated = iso();
  const previous = readJson(STATUS_FILE, {});
  const status = {
    ok: true,
    version: '0.1.0-paper-only',
    generated_at: generated,
    data_source: 'Polymarket Gamma public market API',
    source_health: { gamma_api: { available: true, endpoint: API, updated_at: generated } },
    mode: 'paper_watchlist',
    live_locked: true,
    paper_bankroll_usd: n(previous.paper_bankroll_usd, 1000),
    paper_equity_usd: n(previous.paper_equity_usd, 1000),
    markets: markets.slice(0, 20),
    signals,
    safety_note: 'Read-only paper monitor. It does not authenticate to the CLOB, place orders, hold funds, or move money.',
  };
  writeJson(STATUS_FILE, status);
  return status;
}

async function main() {
  const args = process.argv.slice(2);
  try {
    if (args.includes('--self-test')) { console.log(JSON.stringify({ ok: true, api: API, live_locked: true })); return; }
    if (args.includes('--once')) { console.log(JSON.stringify(await runPolymarketPaperCycle())); return; }
    if (args.includes('--daemon')) { for (;;) { try { await runPolymarketPaperCycle(); } catch (error) { writeJson(STATUS_FILE, { ...readJson(STATUS_FILE, {}), ok: false, generated_at: iso(), error: String(error?.message || error), live_locked: true }); } await sleep(900000); } }
    console.log(JSON.stringify(readJson(STATUS_FILE, { ok: true, version: '0.1.0-paper-only', live_locked: true, markets: [], signals: [] })));
  } catch (error) {
    console.error(JSON.stringify({ ok: false, error: String(error?.message || error), live_locked: true }));
    process.exit(2);
  }
}

main();
