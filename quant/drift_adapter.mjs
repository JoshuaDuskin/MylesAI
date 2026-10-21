const DATA_API_URL = (process.env.DRIFT_DATA_API_URL || 'https://data.velocity.exchange').replace(/\/$/, '');
const ENV = 'mainnet-beta';
const MARKET_SYMBOLS = ['SOL-PERP', 'BTC-PERP', 'ETH-PERP'];
const RESOLUTIONS = { '1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440 };

async function fetchJson(url, label, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      headers: { accept: 'application/json', 'user-agent': 'MylesQuant/DriftPaperAdapter' },
      signal: controller.signal,
    });
    const body = await response.text();
    if (!response.ok) throw new Error(`${label}: HTTP ${response.status} ${response.statusText} - ${body.slice(0, 300)}`);
    return JSON.parse(body);
  } finally {
    clearTimeout(timer);
  }
}

function finiteNumber(value, fallback = null) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function normalizeMarket(row) {
  return {
    symbol: row.symbol,
    market_index: finiteNumber(row.marketIndex),
    market_type: row.marketType,
    status: row.status,
    price: finiteNumber(row.oraclePrice ?? row.markPrice ?? row.price),
    mark_price: finiteNumber(row.markPrice ?? row.price),
    oracle_price: finiteNumber(row.oraclePrice),
    funding_rate_24h: finiteNumber(row.fundingRate24h),
    open_interest: row.openInterest ?? null,
    limits: row.limits ?? null,
  };
}

export async function readDriftMarkets() {
  const raw = await fetchJson(`${DATA_API_URL}/stats/markets`, 'Drift markets');
  const markets = (Array.isArray(raw?.markets) ? raw.markets : [])
    .filter((row) => row.marketType === 'perp' && MARKET_SYMBOLS.includes(row.symbol))
    .map(normalizeMarket);
  return {
    ok: true,
    venue: 'Drift',
    network: 'Solana mainnet-beta',
    chain: 'solana',
    data_api_url: DATA_API_URL,
    paper_only: true,
    live_execution_enabled: false,
    wallet_signing: false,
    markets,
    generated_at: new Date().toISOString(),
  };
}

function candleRow(row) {
  const open = finiteNumber(row.fillOpen ?? row.oracleOpen);
  const high = finiteNumber(row.fillHigh ?? row.oracleHigh ?? open);
  const low = finiteNumber(row.fillLow ?? row.oracleLow ?? open);
  const close = finiteNumber(row.fillClose ?? row.oracleClose ?? open);
  return {
    timestamp: finiteNumber(row.ts),
    open,
    high,
    low,
    close,
    volume: finiteNumber(row.quoteVolume, 0),
  };
}

export async function readDriftCandles(symbol, timeframe = '1m', limit = 3000) {
  const resolution = RESOLUTIONS[timeframe];
  if (!resolution) throw new Error(`Unsupported Drift timeframe ${timeframe}`);
  const url = new URL(`${DATA_API_URL}/market/${encodeURIComponent(symbol)}/candles/${resolution}`);
  url.searchParams.set('limit', String(Math.max(80, Math.min(1000, Math.trunc(finiteNumber(limit, 1000))))));
  const raw = await fetchJson(url, `Drift ${symbol} candles`);
  const rows = (Array.isArray(raw?.records) ? raw.records : Array.isArray(raw?.candles) ? raw.candles : [])
    .map(candleRow)
    .filter((row) => row.timestamp > 0 && row.open > 0 && row.high > 0 && row.low > 0 && row.close > 0)
    .sort((a, b) => a.timestamp - b.timestamp);
  if (rows.length < Math.min(80, Number(limit))) throw new Error(`Drift ${symbol} returned only ${rows.length} usable candles`);
  return rows;
}

export async function readDriftSnapshot(symbol, timeframe = '1m', limit = 3000) {
  const [markets, candles] = await Promise.all([readDriftMarkets(), readDriftCandles(symbol, timeframe, limit)]);
  const market = markets.markets.find((row) => row.symbol === symbol);
  const candle = candles.at(-1);
  return {
    candles,
    latest: {
      price: finiteNumber(market?.price ?? candle?.close),
      timestamp: finiteNumber(candle?.timestamp, Math.floor(Date.now() / 1000)),
      source: 'Drift Data API oracle/market snapshot',
      degraded: !market?.price,
    },
    market,
  };
}

async function main() {
  if (process.argv.includes('--self-test')) {
    console.log(JSON.stringify({ ok: true, venue: 'Drift', network: 'Solana mainnet-beta', data_api_url: DATA_API_URL, paper_only: true, live_execution_enabled: false, wallet_signing: false }));
    return;
  }
  const snapshot = await readDriftSnapshot(process.env.DRIFT_MARKET || 'SOL-PERP', process.env.DRIFT_TIMEFRAME || '1m', 300);
  console.log(JSON.stringify({ ...snapshot, venue: 'Drift', network: 'Solana mainnet-beta', paper_only: true, live_execution_enabled: false, wallet_signing: false }, null, 2));
}

if (process.argv[1]?.replaceAll('\\', '/').endsWith('/drift_adapter.mjs')) {
  main().catch((error) => {
    console.error(JSON.stringify({ ok: false, error: String(error?.stack || error) }));
    process.exitCode = 1;
  });
}
