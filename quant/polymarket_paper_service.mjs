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
  const prices = parseJson(row.outcomePrices).map(value=>n(value,NaN));
  const tokens = parseJson(row.clobTokenIds);
  const points = outcomes.map((outcome, i) => ({ outcome: String(outcome), price: n(prices[i]), token_id: tokens[i] || null })).filter(x => x.price > 0 && x.price < 1);
  const volume = n(row.volumeNum ?? row.volume);
  const liquidity = n(row.liquidityNum ?? row.liquidity);
  return {
    provider: 'Polymarket International',
    category: row.category || row.events?.[0]?.category || 'Uncategorized',
    resolution_criteria: String(row.description||'Provider has not supplied resolution criteria').slice(0,4000),
    resolution_source: row.resolutionSource || null,
    best_bid: row.bestBid==null?null:n(row.bestBid),
    best_ask: row.bestAsk==null?null:n(row.bestAsk),
    spread: row.bestAsk!=null&&row.bestBid!=null?n(row.bestAsk)-n(row.bestBid):null,
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
    return [{ market_id: market.id, question: market.question, outcome: candidate.outcome, price: candidate.price, liquidity_score: scoreMarket(market), confidence: null, action: 'paper_watch', rationale: 'Liquid active market surfaced for paper review; no order is submitted.' }];
  }).sort((a, b) => b.liquidity_score - a.liquidity_score).slice(0, 12);
}

export function simulatePredictionPaper(previous,markets,history,now=Date.now()) {
  const paper=previous.paper_simulation||{cash_usd:n(previous.paper_equity_usd,1000),positions:[],trades:[]};
  const rows=structuredClone(paper),byId=new Map(markets.map(m=>[m.id,m]));
  const fee=.01; // Explicit conservative paper assumption; not a provider fee quote.
  for(const p of rows.positions){
    const m=byId.get(p.market_id),o=m?.outcomes.find(x=>x.outcome===p.outcome);
    p.mark_available=!!o;if(!o)continue;p.mark=o.price;
    if(m.best_bid>0&&(o.price<=p.entry-.03||o.price>=p.entry+.05||now-p.opened_epoch>=86400000)){
      const proceeds=p.shares*m.best_bid,exitFee=proceeds*fee;
      rows.cash_usd+=proceeds-exitFee;rows.trades.push({...p,exit:m.best_bid,exit_fee:exitFee,net_pnl:proceeds-exitFee-p.cost_usd,closed_at:new Date(now).toISOString()});p.closed=true;
    }
  }
  rows.positions=rows.positions.filter(p=>!p.closed);
  for(const m of markets){
    if(rows.positions.length>=2)break;
    if(rows.positions.some(p=>p.market_id===m.id)||m.liquidity_usd<10000||!(m.best_ask>0&&m.best_ask<1&&m.best_bid>0)||m.spread>.05)continue;
    const h=history[m.id]||[],o=m.outcomes[0];if(!o||h.length<3)continue;
    const earlier=h.at(-3).outcomes.find(x=>x.outcome===o.outcome);
    if(!earlier||o.price-earlier.price<.02)continue;
    const budget=Math.min(25,rows.cash_usd*.025);if(budget<1)continue;
    const shares=budget/(m.best_ask*(1+fee));rows.cash_usd-=budget;
    rows.positions.push({market_id:m.id,provider:'Polymarket International',outcome:o.outcome,entry:m.best_ask,shares,cost_usd:budget,entry_fee:shares*m.best_ask*fee,mark:o.price,mark_available:true,opened_epoch:now,opened_at:new Date(now).toISOString()});
  }
  rows.trades=rows.trades.slice(-500);
  rows.equity_usd=rows.cash_usd+rows.positions.reduce((sum,p)=>sum+p.shares*p.mark,0);
  rows.assumptions={fee_per_side_pct:1,max_positions:2,max_trade_usd:25,entry:'observed ask',exit:'observed bid',strategy:'three-observation probability momentum',not_a_profitability_claim:true};
  return rows;
}

export async function runPolymarketPaperCycle({ limit = 30 } = {}) {
  const query = new URLSearchParams({ active: 'true', closed: 'false', limit: String(Math.min(100, Math.max(1, Math.trunc(n(limit, 30))))), order: 'volumeNum', ascending: 'false' });
  const raw = await api(`/markets?${query}`);
  const rows = Array.isArray(raw) ? raw : (Array.isArray(raw?.data) ? raw.data : []);
  const markets = rows.map(normalizeMarket).filter(x => x.id && x.active && !x.closed);
  const signals = signalsFor(markets);
  const generated = iso();
  const previous = readJson(STATUS_FILE, {});
  const history=previous.price_history&&typeof previous.price_history==='object'?previous.price_history:{};
  for(const m of markets){history[m.id]=[...(Array.isArray(history[m.id])?history[m.id]:[]),{at:generated,outcomes:m.outcomes.map(x=>({outcome:x.outcome,price:x.price}))}].slice(-96);}
  const activeHistory=Object.fromEntries(markets.slice(0,20).map(m=>[m.id,history[m.id]]));
  const paperSimulation=simulatePredictionPaper(previous,markets,history);
  const providerChecks=await Promise.allSettled([
    fetch('https://polymarket.com/api/geoblock',{signal:AbortSignal.timeout(8000)}).then(async r=>{if(!r.ok)throw new Error('Geographic check HTTP '+r.status);const x=await r.json();return {blocked:x.blocked===true,country:x.country||null};}),
    fetch('https://api.polymarket.us/v1/markets?active=true&closed=false&limit=20',{headers:{accept:'application/json'},signal:AbortSignal.timeout(8000)}).then(async r=>{if(!r.ok)throw new Error('Polymarket US HTTP '+r.status+'; authorized market-data account may be required');return r.json();})
  ]);
  const geo=providerChecks[0].status==='fulfilled'?providerChecks[0].value:{blocked:null,error:String(providerChecks[0].reason?.message||'Geographic check unavailable')};
  const us=providerChecks[1].status==='fulfilled'?providerChecks[1].value:null;
  const usRows=Array.isArray(us?.markets)?us.markets.filter(x=>x.active===true&&x.closed!==true):[];

  const status = {
    ok: true,
    version: '0.1.0-paper-only',
    generated_at: generated,
    data_source: 'Polymarket Gamma public market API',
    source_health: { gamma_api: { available: markets.length>0, endpoint: API, updated_at: generated },polymarket_us:{available:usRows.length>0,updated_at:generated,error:providerChecks[1].status==='rejected'?String(providerChecks[1].reason?.message):null} },
    provider:'Polymarket International',
    geographic_eligibility:geo,
    us_markets:usRows.map(x=>({id:x.id,question:x.question,provider:'Polymarket US',category:x.category,resolution_criteria:x.description||null})),
    us_account_eligibility:'Not verified; US account, identity and jurisdiction checks are required separately',
    price_history:activeHistory,
    paper_strategy_status:'Paper momentum simulation waits for three observed probability snapshots, quoted bid/ask, and liquidity. No live orders.',
    paper_simulation:paperSimulation,
    news_correlation_status:'Not available: no verified news feed is configured',
    mode: 'paper_watchlist',
    live_locked: true,
    paper_bankroll_usd: n(previous.paper_bankroll_usd, 1000),
    paper_equity_usd: paperSimulation.equity_usd,
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

if(process.argv[1]?.replaceAll('\\','/').endsWith('/polymarket_paper_service.mjs'))main();
