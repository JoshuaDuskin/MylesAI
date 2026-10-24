// Read-only public feeds. Venue quotes are research inputs, never execution marks.
export const RESEARCH_ASSETS = ['BTC','ETH','SOL','XRP','TAO'];
const krakenPairs = {BTC:'XXBTZUSD',ETH:'XETHZUSD',SOL:'SOLUSD',XRP:'XXRPZUSD',TAO:'TAOUSD'};
export const providerState = {};
const cache = new Map();
const finite = value => value !== null && value !== '' && Number.isFinite(Number(value)) ? Number(value) : null;

export async function publicJson(url, {fetcher=fetch, timeout=8000}={}) {
  const response = await fetcher(url, {headers:{accept:'application/json','user-agent':'MylesQuant/Research'},signal:AbortSignal.timeout(timeout)});
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export function quote(asset, price, bid, ask, timestamp, extra={}) {
  price=finite(price); bid=finite(bid); ask=finite(ask);
  if (!(price>0)) return null;
  return {asset,price,bid,ask,spread_bps:bid>0&&ask>=bid?(ask-bid)/price*10000:null,
    observed_at:new Date().toISOString(),source_timestamp:timestamp||null,...extra};
}

export function normalizeGmx(rows) {
  const out={};
  for(const asset of RESEARCH_ASSETS){
    const row=rows.find(x=>String(x.symbol||'').startsWith(asset+'/USD '));
    if(row){const q=quote(asset,Number(row.markPrice)/1e30,Number(row.minPrice)/1e30,Number(row.maxPrice)/1e30,null,
      {funding_rate_long:Number(row.fundingRateLong)/1e30,funding_rate_short:Number(row.fundingRateShort)/1e30,
       funding_unit:'provider native rate; not assumed to be daily',liquidity_long_usd:finite(row.availableLiquidityLong)/1e30,
       liquidity_short_usd:finite(row.availableLiquidityShort)/1e30});if(q)out[asset]=q;}
  }
  return out;
}

async function feed(name, reader, {now=Date.now(),fetcher=fetch}={}) {
  const old=providerState[name]||{};
  if(cache.has(name)&&now<(old.next_attempt_epoch||0))return;
  if(now<(old.next_attempt_epoch||0))return;
  try{
    const rows=await reader(fetcher);
    if(!Object.keys(rows).length)throw new Error('No valid market observations');
    cache.set(name,rows);providerState[name]={last_success_at:new Date(now).toISOString(),last_attempt_at:new Date(now).toISOString(),consecutive_failures:0,error:null,next_attempt_epoch:now+60000};
  }catch(error){
    const failures=(old.consecutive_failures||0)+1;
    providerState[name]={...old,last_attempt_at:new Date(now).toISOString(),consecutive_failures:failures,error:String(error.message||error),next_attempt_epoch:now+Math.min(300000,15000*2**Math.min(failures-1,5))};
  }
}

export async function researchFeeds(options={}) {
  const now=options.now??Date.now();
  options={...options,now};
  await Promise.all([
    feed('gmx',async fetcher=>{
      let last;
      for(const base of ['https://arbitrum.gmxapi.io/v1','https://arbitrum.gmxapi.ai/v1']){
        try{return normalizeGmx(await publicJson(base+'/markets/tickers',{fetcher}));}catch(e){last=e;}
      }throw last;
    },options),
    feed('kraken',async fetcher=>{
      const raw=await publicJson('https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,XRPUSD,TAOUSD',{fetcher});
      if(raw.error?.length)throw new Error(raw.error.join('; '));
      return Object.fromEntries(RESEARCH_ASSETS.map(a=>{const r=raw.result?.[krakenPairs[a]];return[a,r?quote(a,r.c?.[0],r.b?.[0],r.a?.[0],null):null];}).filter(([,v])=>v));
    },options),
    feed('coinbase',async fetcher=>{
      const rows=await Promise.allSettled(RESEARCH_ASSETS.map(async a=>{
        const r=await publicJson(`https://api.exchange.coinbase.com/products/${a}-USD/ticker`,{fetcher});
        const q=quote(a,r.price,r.bid,r.ask,r.time);if(!q)throw new Error('Invalid ticker');
        if(!Number.isFinite(Date.parse(r.time))||now-Date.parse(r.time)>300000)throw new Error('Stale Coinbase trade timestamp');
        return[a,q];
      }));
      const valid=rows.filter(x=>x.status==='fulfilled').map(x=>x.value);
      return Object.fromEntries(valid);
    },options),
  ]);
  const health={},markets={};
  for(const name of ['gmx','kraken','coinbase']){
    const state=providerState[name]||{},age=state.last_success_at?Math.max(0,(now-Date.parse(state.last_success_at))/1000):null;
    const fresh=age!==null&&age<=180&&!state.error;
    health[name]={available:fresh,status:fresh?'verified':state.error?'error':'unavailable',ok_markets:fresh?Object.keys(cache.get(name)||{}).length:0,total_markets:RESEARCH_ASSETS.length,
      last_update_at:state.last_success_at||null,age_seconds:age,error:state.error||null,consecutive_failures:state.consecutive_failures||0,next_retry_at:new Date(state.next_attempt_epoch||now).toISOString(),transport:'REST polling; automatic reconnect with capped exponential backoff'};
    for(const [asset,row] of Object.entries(cache.get(name)||{})){
      markets[asset]??={sources:{}};markets[asset].sources[name]={...row,available:fresh};
    }
  }
  for(const row of Object.values(markets)){
    const prices=Object.values(row.sources).filter(x=>x.available).map(x=>x.price).sort((a,b)=>a-b);
    row.source_count=prices.length;row.consensus_price=prices.length?prices[Math.floor(prices.length/2)]:null;
    row.dispersion_bps=prices.length>1?(prices.at(-1)-prices[0])/row.consensus_price*10000:null;
  }
  return {generated_at:new Date(now).toISOString(),health,markets};
}

export const RESEARCH_TIMEFRAMES = {'1m':60,'5m':300,'15m':900,'1h':3600,'4h':14400,'1d':86400};
export function completedCandles(raw, seconds, now=Date.now()) {
  if(!Array.isArray(raw))throw new Error('Invalid candle response');
  const unique=new Map();
  for(const r of raw){
    const c={timestamp:Number(r[0]),low:Number(r[1]),high:Number(r[2]),open:Number(r[3]),close:Number(r[4]),volume:Number(r[5])};
    if(Object.values(c).every(Number.isFinite)&&c.timestamp>0&&c.low>0&&c.high>=Math.max(c.low,c.open,c.close)&&c.low<=Math.min(c.open,c.close)&&c.volume>=0&&c.timestamp+seconds<=now/1000)unique.set(c.timestamp,c);
  }
  return [...unique.values()].sort((a,b)=>a.timestamp-b.timestamp);
}
export async function researchCandles(asset, {fetcher=fetch,now=Date.now(),timeframe='1h',extended=false}={}) {
  const seconds=RESEARCH_TIMEFRAMES[timeframe];
  if(!seconds||!RESEARCH_ASSETS.includes(asset))throw new Error('Unsupported research market/timeframe');
  const key='candles:'+asset+':'+timeframe,old=cache.get(key),ttl=Math.min(600000,seconds*1000);
  if(old&&now-old.at<ttl)return old.rows;
  // Coinbase has no 4h bucket: aggregate four contiguous completed hourly bars.
  const sourceSeconds=timeframe==='4h'?3600:seconds;
  const raw=await publicJson(`https://api.exchange.coinbase.com/products/${asset}-USD/candles?granularity=${sourceSeconds}`,{fetcher});
  if(extended&&Array.isArray(raw)){
    const pages=timeframe==='4h'?7:2;
    for(let page=1;page<pages;page++){
      const valid=raw.map(r=>Number(r[0])).filter(Number.isFinite);if(!valid.length)break;
      const end=Math.min(...valid),start=end-300*sourceSeconds;
      const extra=await publicJson(`https://api.exchange.coinbase.com/products/${asset}-USD/candles?granularity=${sourceSeconds}&start=${new Date(start*1000).toISOString()}&end=${new Date(end*1000).toISOString()}`,{fetcher});
      if(!Array.isArray(extra)||!extra.some(r=>Number(r[0])<end))break;
      raw.push(...extra);
    }
  }
  let rows=completedCandles(raw,sourceSeconds,now);
  if(timeframe==='4h'){
    const groups=new Map();
    for(const c of rows){const t=Math.floor(c.timestamp/seconds)*seconds;const g=groups.get(t)||[];g.push(c);groups.set(t,g);}
    rows=[...groups.entries()].filter(([t,g])=>g.length===4&&g.every((c,i)=>c.timestamp===t+i*sourceSeconds)&&t+seconds<=now/1000).map(([timestamp,g])=>({timestamp,open:g[0].open,close:g[3].close,low:Math.min(...g.map(c=>c.low)),high:Math.max(...g.map(c=>c.high)),volume:g.reduce((a,c)=>a+c.volume,0)}));
  }
  if(rows.length<60||now/1000-rows.at(-1).timestamp>seconds*3)throw new Error('Insufficient or stale completed candles');
  if(rows.some((r,i)=>i>0&&r.timestamp-rows[i-1].timestamp!==seconds))throw new Error('Gapped candle history; no synthetic bars inserted');
  cache.set(key,{at:now,rows});return rows;
}
