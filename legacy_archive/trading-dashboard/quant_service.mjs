import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, 'MylesAI') : path.join(os.homedir(), 'AppData', 'Local', 'MylesAI');
const DATA_DIR = path.join(ROOT, 'data');
const STATE_FILE = path.join(DATA_DIR, 'quant_paper_state_v3.json');
const STATUS_FILE = path.join(DATA_DIR, 'trading_status.json');
const RESEARCH_HISTORY_FILE = path.join(DATA_DIR, 'quant_research_history.json');
const RESEARCH_STATE_FILE = path.join(DATA_DIR, 'quant_research_paper_state_v3.json');
const PAPER_ARCHIVE_DIR = path.join(DATA_DIR, 'quant_paper_archives');
const MARKET_RESEARCH_FILE = path.join(DATA_DIR, 'quant_market_research.json');
const MULTI_SOURCE_FILE = path.join(DATA_DIR, 'quant_multi_source_intelligence.json');
const TOURNAMENT_STATE_FILE = path.join(DATA_DIR, 'quant_research_tournament_v1.json');
const RUNTIME_STATE_FILE = path.join(DATA_DIR, 'quant_runtime_activity_v1.json');
const CONFIG_FILE = path.join(__dirname, 'quant_config.json');
const VERSION = '0.9.4';
const VALID_PERIODS = new Set(['1m','5m','15m','30m','1h','2h','4h','1d']);
const SUPPORTED_RESEARCH_MARKETS = ['BTC/USD','ETH/USD','SOL/USD','XRP/USD','TAO/USD'];
function periodSeconds(p){return ({'1m':60,'5m':300,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400})[String(p)]||300;}

const DEFAULT_CONFIG = {
  schema_version: 3,
  venue: 'GMX',
  chain_id: 42161,
  timeframe: '5m',
  history_limit: 5000,
  poll_seconds: 60,
  starting_equity: 10000,
  market_settings: {
    'BTC/USD': { enabled: true, auto_trade_enabled: true, paper_strategy: 'trend_momentum' },
    'ETH/USD': { enabled: true, auto_trade_enabled: true, paper_strategy: 'trend_momentum' },
    'SOL/USD': { enabled: true, auto_trade_enabled: true, paper_strategy: 'trend_momentum' },
    'XRP/USD': { enabled: true, auto_trade_enabled: true, paper_strategy: 'trend_momentum' },
    'TAO/USD': { enabled: true, auto_trade_enabled: true, paper_strategy: 'trend_momentum' },
  },
  strategies: {
    scalp_trend: { enabled: true },
    trend_momentum: { enabled: true },
    mean_reversion: { enabled: true },
    donchian_breakout: { enabled: true },
    bollinger_reversion: { enabled: true },
    pullback_trend: { enabled: true },
    atr_breakout: { enabled: true },
    rsi_reclaim: { enabled: true },
  },
  multi_source: {
    enabled: true,
    refresh_seconds: 60,
    max_price_dispersion_bps: 40,
    sources: { gmx: true, kraken: true, coinbase: true },
    orderbook_levels: 25,
    trade_sample: 100,
  },
  paper: { enabled: true, auto_trading_enabled: true, adaptive_strategy_selection: true, emergency_stop: false, entry_cooldown_bars: 0 },
  research_exploration: { enabled: true, continuous_market_research_enabled: true, paper_lab_enabled: true, fallback_near_miss: true, fallback_max_stress_loss_pct: 0.75, fallback_min_profit_factor: 0.85, fallback_min_win_rate_pct: 30, risk_per_trade_pct: 0.10, max_concurrent_positions: 3, refresh_seconds: 300, candidate_pool_size: 32, trades_per_candidate: 6, rotation_candles: 72, loser_rotation_trades: 4, max_epoch_drawdown_pct: 10, max_epoch_trades: 500, eligible_only: true, entry_cooldown_bars: 0, tournament_enabled: true, tournament_slots: 8, tournament_slot_equity: 1250, tournament_risk_per_trade_pct: 0.25, tournament_max_stress_loss_pct: 25, tournament_min_profit_factor: 0.20, tournament_max_drawdown_pct: 30 },
  risk: {
    max_risk_per_trade_pct: 0.50,
    max_notional_leverage: 1.50,
    max_position_usd: 0,
    stop_loss_pct: 1.50,
    take_profit_pct: 3.00,
    max_daily_loss_pct: 2.00,
    max_drawdown_pct: 8.00,
    max_concurrent_positions: 2,
    max_market_allocation_pct: 35.0,
    max_holding_bars: 72,
  },
  research_costs: {
    position_fee_bps_per_side: 6,
    slippage_bps_per_side: 1,
    impact_bps_per_side: 2,
    holding_cost_bps_per_day: 5,
    model: 'gmx_oracle_conservative',
  },
  validation: {
    min_trades: 18,
    max_drawdown_pct: 10,
    min_walk_forward_positive_pct: 60,
    min_base_return_pct: 0.5,
    min_stress_return_pct: 0,
    min_profit_factor: 1.10,
    min_expectancy_pct: 0.01,
    stress_cost_multiplier: 2.5,
  },
  live_execution: {
    enabled: false,
    signing_enabled: false,
    reason: 'Live execution remains hard-locked until owner review, forward-paper validation, and a dedicated execution wallet are complete.'
  }
};

function iso(){ return new Date().toISOString(); }
function n(v,f=0){ const x=Number(v); return Number.isFinite(x)?x:f; }
function clamp(v,lo,hi){ return Math.max(lo,Math.min(hi,v)); }
function round(v,d=6){ const m=10**d; return Math.round(v*m)/m; }
function readJson(file,fallback){ try{return JSON.parse(fs.readFileSync(file,'utf8'));}catch{return fallback;} }
function writeJsonAtomic(file,value){ fs.mkdirSync(path.dirname(file),{recursive:true}); const tmp=`${file}.tmp-${process.pid}`; fs.writeFileSync(tmp,JSON.stringify(value,null,2),'utf8'); fs.renameSync(tmp,file); }
function deepMerge(base,extra){
  if(!extra || typeof extra!=='object' || Array.isArray(extra)) return structuredClone(base);
  const out=structuredClone(base);
  for(const [k,v] of Object.entries(extra)){
    if(v && typeof v==='object' && !Array.isArray(v) && out[k] && typeof out[k]==='object' && !Array.isArray(out[k])) out[k]=deepMerge(out[k],v);
    else out[k]=v;
  }
  return out;
}
function normalizeConfig(raw){
  const cfg=deepMerge(DEFAULT_CONFIG,raw||{});
  cfg.schema_version=3;
  cfg.chain_id=42161;
  cfg.venue='GMX';
  cfg.timeframe=VALID_PERIODS.has(String(cfg.timeframe))?String(cfg.timeframe):'1h';
  const historyFloor=({'1m':10000,'5m':8000,'15m':5000,'30m':4000,'1h':3000,'2h':2200,'4h':1500,'1d':800})[cfg.timeframe]||3000;
  cfg.history_limit=Math.round(clamp(Math.max(n(cfg.history_limit,historyFloor),historyFloor),300,10000));
  cfg.poll_seconds=Math.round(clamp(n(cfg.poll_seconds,60),30,900));
  cfg.paper=cfg.paper||{};cfg.paper.entry_cooldown_bars=Math.round(clamp(n(cfg.paper.entry_cooldown_bars,0),0,50));
  cfg.research_exploration=cfg.research_exploration||{};cfg.research_exploration.entry_cooldown_bars=Math.round(clamp(n(cfg.research_exploration.entry_cooldown_bars,cfg.paper.entry_cooldown_bars),0,50));
  cfg.starting_equity=clamp(n(cfg.starting_equity,10000),100,10000000);
  cfg.market_settings=cfg.market_settings||{};
  for(const sym of SUPPORTED_RESEARCH_MARKETS){
    const row=cfg.market_settings[sym]||{};
    cfg.market_settings[sym]={enabled:row.enabled!==false,auto_trade_enabled:row.auto_trade_enabled!==false,paper_strategy:['scalp_trend','trend_momentum','mean_reversion','donchian_breakout','bollinger_reversion','pullback_trend','atr_breakout','rsi_reclaim'].includes(row.paper_strategy)?row.paper_strategy:'trend_momentum'};
  }
  for(const key of Object.keys(cfg.market_settings)) if(!SUPPORTED_RESEARCH_MARKETS.includes(key)) delete cfg.market_settings[key];
  cfg.risk.max_risk_per_trade_pct=clamp(n(cfg.risk.max_risk_per_trade_pct,.5),.05,5);
  cfg.risk.max_notional_leverage=clamp(n(cfg.risk.max_notional_leverage,1.5),.1,5);
  cfg.risk.max_position_usd=clamp(n(cfg.risk.max_position_usd,0),0,1000000);
  cfg.risk.stop_loss_pct=clamp(n(cfg.risk.stop_loss_pct,1.5),.25,15);
  cfg.risk.take_profit_pct=clamp(n(cfg.risk.take_profit_pct,3),.25,40);
  cfg.risk.max_daily_loss_pct=clamp(n(cfg.risk.max_daily_loss_pct,2),.25,20);
  cfg.risk.max_drawdown_pct=clamp(n(cfg.risk.max_drawdown_pct,8),.5,40);
  cfg.risk.max_concurrent_positions=Math.round(clamp(n(cfg.risk.max_concurrent_positions,2),1,5));
  cfg.risk.max_market_allocation_pct=clamp(n(cfg.risk.max_market_allocation_pct,35),5,100);
  cfg.risk.max_holding_bars=Math.round(clamp(n(cfg.risk.max_holding_bars,72),6,1000));
  const rawSlip=n(raw?.research_costs?.slippage_bps_per_side,DEFAULT_CONFIG.research_costs.slippage_bps_per_side);
  const rawImpact=n(raw?.research_costs?.impact_bps_per_side,DEFAULT_CONFIG.research_costs.impact_bps_per_side);
  const legacyCostModel=rawSlip===5&&rawImpact===20&&!raw?.research_costs?.model;
  cfg.research_costs.position_fee_bps_per_side=clamp(n(cfg.research_costs.position_fee_bps_per_side,6),0,100);
  cfg.research_costs.slippage_bps_per_side=clamp(legacyCostModel?1:n(cfg.research_costs.slippage_bps_per_side,1),0,300);
  cfg.research_costs.impact_bps_per_side=clamp(legacyCostModel?2:n(cfg.research_costs.impact_bps_per_side,2),0,1000);
  cfg.research_costs.holding_cost_bps_per_day=clamp(n(cfg.research_costs.holding_cost_bps_per_day,5),0,300);
  cfg.research_costs.model='gmx_oracle_conservative';
  cfg.validation.min_trades=Math.round(clamp(n(cfg.validation.min_trades,12),1,500));
  cfg.validation.max_drawdown_pct=clamp(n(cfg.validation.max_drawdown_pct,12),1,60);
  cfg.validation.min_walk_forward_positive_pct=clamp(n(cfg.validation.min_walk_forward_positive_pct,50),0,100);
  cfg.validation.min_base_return_pct=clamp(n(cfg.validation.min_base_return_pct,0),-100,500);
  cfg.validation.min_stress_return_pct=clamp(n(cfg.validation.min_stress_return_pct,0),-100,500);
  cfg.validation.min_profit_factor=clamp(n(cfg.validation.min_profit_factor,1.10),0,10);
  cfg.validation.min_expectancy_pct=clamp(n(cfg.validation.min_expectancy_pct,.01),-20,20);
  cfg.validation.stress_cost_multiplier=clamp(n(cfg.validation.stress_cost_multiplier,2.5),1,10);
  cfg.multi_source=cfg.multi_source||{};
  cfg.multi_source.enabled=cfg.multi_source.enabled!==false;
  cfg.multi_source.refresh_seconds=Math.round(clamp(n(cfg.multi_source.refresh_seconds,60),30,900));
  cfg.multi_source.max_price_dispersion_bps=clamp(n(cfg.multi_source.max_price_dispersion_bps,40),5,500);
  cfg.multi_source.orderbook_levels=Math.round(clamp(n(cfg.multi_source.orderbook_levels,25),5,100));
  cfg.multi_source.trade_sample=Math.round(clamp(n(cfg.multi_source.trade_sample,100),20,1000));
  cfg.multi_source.sources=cfg.multi_source.sources||{};
  for(const name of ['gmx','kraken','coinbase'])cfg.multi_source.sources[name]=cfg.multi_source.sources[name]!==false;
  cfg.paper.enabled=cfg.paper.enabled!==false;
  cfg.paper.auto_trading_enabled=cfg.paper.auto_trading_enabled!==false;
  cfg.paper.emergency_stop=!!cfg.paper.emergency_stop;
  cfg.research_exploration=cfg.research_exploration||{};
  cfg.research_exploration.enabled=cfg.research_exploration.enabled!==false;
  cfg.research_exploration.continuous_market_research_enabled=cfg.research_exploration.continuous_market_research_enabled!==false&&cfg.research_exploration.enabled!==false;
  cfg.research_exploration.paper_lab_enabled=cfg.research_exploration.paper_lab_enabled!==false;
  cfg.research_exploration.fallback_near_miss=cfg.research_exploration.fallback_near_miss!==false;
  cfg.research_exploration.fallback_max_stress_loss_pct=clamp(n(cfg.research_exploration.fallback_max_stress_loss_pct,.75),0,5);
  cfg.research_exploration.fallback_min_profit_factor=clamp(n(cfg.research_exploration.fallback_min_profit_factor,.85),0,5);
  cfg.research_exploration.fallback_min_win_rate_pct=clamp(n(cfg.research_exploration.fallback_min_win_rate_pct,30),0,100);
  cfg.research_exploration.risk_per_trade_pct=clamp(n(cfg.research_exploration.risk_per_trade_pct,.10),.02,.50);
  cfg.research_exploration.max_concurrent_positions=Math.round(clamp(n(cfg.research_exploration.max_concurrent_positions,3),1,5));
  cfg.research_exploration.refresh_seconds=Math.round(clamp(n(cfg.research_exploration.refresh_seconds,300),120,1800));
  cfg.research_exploration.candidate_pool_size=Math.round(clamp(n(cfg.research_exploration.candidate_pool_size,32),2,32));
  cfg.research_exploration.trades_per_candidate=Math.round(clamp(n(cfg.research_exploration.trades_per_candidate,6),2,50));
  cfg.research_exploration.rotation_candles=Math.round(clamp(n(cfg.research_exploration.rotation_candles,90),15,1440));
  cfg.research_exploration.loser_rotation_trades=Math.round(clamp(n(cfg.research_exploration.loser_rotation_trades,4),2,20));
  cfg.research_exploration.max_epoch_drawdown_pct=clamp(n(cfg.research_exploration.max_epoch_drawdown_pct,10),3,40);
  cfg.research_exploration.max_epoch_trades=Math.round(clamp(n(cfg.research_exploration.max_epoch_trades,500),50,5000));
  cfg.research_exploration.eligible_only=cfg.research_exploration.eligible_only!==false;
  cfg.research_exploration.tournament_enabled=cfg.research_exploration.tournament_enabled!==false;
  cfg.research_exploration.tournament_slots=Math.round(clamp(n(cfg.research_exploration.tournament_slots,8),4,16));
  cfg.research_exploration.tournament_slot_equity=clamp(n(cfg.research_exploration.tournament_slot_equity,1250),100,100000);
  cfg.research_exploration.tournament_risk_per_trade_pct=clamp(n(cfg.research_exploration.tournament_risk_per_trade_pct,.25),.02,1);
  cfg.research_exploration.tournament_max_stress_loss_pct=clamp(n(cfg.research_exploration.tournament_max_stress_loss_pct,25),1,100);
  cfg.research_exploration.tournament_min_profit_factor=clamp(n(cfg.research_exploration.tournament_min_profit_factor,.20),0,5);
  cfg.research_exploration.tournament_max_drawdown_pct=clamp(n(cfg.research_exploration.tournament_max_drawdown_pct,30),5,80);
  cfg.live_execution={enabled:false,signing_enabled:false,reason:DEFAULT_CONFIG.live_execution.reason};
  return cfg;
}
function loadConfig(){ const cfg=normalizeConfig(readJson(CONFIG_FILE,DEFAULT_CONFIG)); writeJsonAtomic(CONFIG_FILE,cfg); return cfg; }

export function sma(values,period){ if(!Array.isArray(values)||period<1||values.length<period)return null; let sum=0; for(let i=values.length-period;i<values.length;i++)sum+=values[i]; return sum/period; }
export function emaSeries(values,period){ if(!Array.isArray(values)||!values.length||period<1)return[]; const k=2/(period+1),out=[]; let prev=values[0]; out.push(prev); for(let i=1;i<values.length;i++){prev=values[i]*k+prev*(1-k);out.push(prev);} return out; }
export function rsiSeries(values,period=14){ const out=Array(values.length).fill(null); if(values.length<=period)return out; let gain=0,loss=0; for(let i=1;i<=period;i++){const d=values[i]-values[i-1];if(d>=0)gain+=d;else loss-=d;} gain/=period;loss/=period;out[period]=loss===0?100:100-100/(1+gain/loss); for(let i=period+1;i<values.length;i++){const d=values[i]-values[i-1],g=Math.max(0,d),l=Math.max(0,-d);gain=(gain*(period-1)+g)/period;loss=(loss*(period-1)+l)/period;out[i]=loss===0?100:100-100/(1+gain/loss);} return out; }
export function maxDrawdown(equity){ let peak=-Infinity,worst=0; for(const v of equity){peak=Math.max(peak,v);if(peak>0)worst=Math.max(worst,(peak-v)/peak);} return worst*100; }

export function signalTrendMomentum(candles,index,params={}){
  const fastP=n(params.fast,20),slowP=n(params.slow,50),rsiP=n(params.rsi_period,14);
  if(index<Math.max(60,slowP+5))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close),fast=emaSeries(closes,fastP).at(-1),slow=emaSeries(closes,slowP).at(-1),rsi=rsiSeries(closes,rsiP).at(-1);
  if(fast==null||slow==null||rsi==null)return 0;
  const longMin=n(params.long_rsi_min,52),longMax=n(params.long_rsi_max,74),shortMax=n(params.short_rsi_max,48),shortMin=n(params.short_rsi_min,26);
  if(fast>slow&&rsi>=longMin&&rsi<=longMax)return 1;
  if(fast<slow&&rsi<=shortMax&&rsi>=shortMin)return-1;
  return 0;
}
export function signalMeanReversion(candles,index,params={}){
  const maP=n(params.ma,30),rsiP=n(params.rsi_period,14),dev=n(params.deviation,.025);
  if(index<Math.max(40,maP+5))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close),ma=sma(closes,maP),rsi=rsiSeries(closes,rsiP).at(-1),price=closes.at(-1);
  if(!ma||rsi==null)return 0;
  const deviation=(price-ma)/ma,longRsi=n(params.long_rsi,35),shortRsi=n(params.short_rsi,65);
  if(deviation<-dev&&rsi<longRsi)return 1;
  if(deviation>dev&&rsi>shortRsi)return-1;
  return 0;
}
export function signalScalpTrend(candles,index,params={}){
  const p1=n(params.fast,9),p2=n(params.mid,21),p3=n(params.slow,50),rsiP=n(params.rsi_period,14);
  if(index<Math.max(55,p3+5))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close);
  const e1=emaSeries(closes,p1).at(-1),e2=emaSeries(closes,p2).at(-1),e3=emaSeries(closes,p3).at(-1),rsi=rsiSeries(closes,rsiP).at(-1);
  const c=candles[index],prev=candles[index-1];
  if([e1,e2,e3,rsi].some(v=>v==null)||!prev)return 0;
  const longMin=n(params.long_rsi_min,52),longMax=n(params.long_rsi_max,72),shortMax=n(params.short_rsi_max,48),shortMin=n(params.short_rsi_min,28);
  if(e1>e2&&e2>e3&&rsi>=longMin&&rsi<=longMax&&c.close>prev.close)return 1;
  if(e1<e2&&e2<e3&&rsi<=shortMax&&rsi>=shortMin&&c.close<prev.close)return -1;
  return 0;
}


export function signalDonchianBreakout(candles,index,params={}){
  const lookback=Math.round(n(params.lookback,30)),fastP=Math.round(n(params.fast,20)),slowP=Math.round(n(params.slow,50));
  if(index<Math.max(lookback+2,slowP+5))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close),fast=emaSeries(closes,fastP).at(-1),slow=emaSeries(closes,slowP).at(-1);
  let hi=-Infinity,lo=Infinity;
  for(let i=index-lookback;i<index;i++){hi=Math.max(hi,candles[i].high);lo=Math.min(lo,candles[i].low);}
  const px=candles[index].close;
  if(fast>slow&&px>hi)return 1;
  if(fast<slow&&px<lo)return -1;
  return 0;
}
export function signalBollingerReversion(candles,index,params={}){
  const period=Math.round(n(params.period,30)),mult=n(params.mult,2.0),rsiP=Math.round(n(params.rsi_period,14));
  if(index<Math.max(period+5,rsiP+5))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close),window=closes.slice(-period),mean=window.reduce((a,b)=>a+b,0)/window.length;
  const variance=window.reduce((a,b)=>a+(b-mean)**2,0)/window.length,std=Math.sqrt(Math.max(0,variance)),px=closes.at(-1),rsi=rsiSeries(closes,rsiP).at(-1);
  if(rsi==null||std<=0)return 0;
  if(px<mean-mult*std&&rsi<=n(params.long_rsi,35))return 1;
  if(px>mean+mult*std&&rsi>=n(params.short_rsi,65))return -1;
  return 0;
}
export function signalPullbackTrend(candles,index,params={}){
  const fastP=Math.round(n(params.fast,20)),slowP=Math.round(n(params.slow,50)),rsiP=Math.round(n(params.rsi_period,14));
  if(index<Math.max(slowP+5,rsiP+5))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close),fast=emaSeries(closes,fastP).at(-1),slow=emaSeries(closes,slowP).at(-1),rsi=rsiSeries(closes,rsiP).at(-1),px=closes.at(-1);
  if([fast,slow,rsi].some(v=>v==null))return 0;
  if(fast>slow&&px>slow&&rsi>=n(params.long_rsi_min,40)&&rsi<=n(params.long_rsi_max,55))return 1;
  if(fast<slow&&px<slow&&rsi>=n(params.short_rsi_min,45)&&rsi<=n(params.short_rsi_max,60))return -1;
  return 0;
}


export function signalAtrBreakout(candles,index,params={}){
  const look=Math.round(n(params.lookback,20)),atrP=Math.round(n(params.atr,14)),mult=n(params.mult,.35),fastP=Math.round(n(params.fast,12)),slowP=Math.round(n(params.slow,36));
  if(index<Math.max(look+3,atrP+3,slowP+5))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close),fast=emaSeries(closes,fastP).at(-1),slow=emaSeries(closes,slowP).at(-1);
  let trSum=0;
  for(let i=index-atrP+1;i<=index;i++){const prev=i>0?candles[i-1].close:candles[i].open;trSum+=Math.max(candles[i].high-candles[i].low,Math.abs(candles[i].high-prev),Math.abs(candles[i].low-prev));}
  const atr=trSum/atrP;let hi=-Infinity,lo=Infinity;
  for(let i=index-look;i<index;i++){hi=Math.max(hi,candles[i].high);lo=Math.min(lo,candles[i].low);}
  const px=candles[index].close;
  if(fast>slow&&px>hi+atr*mult)return 1;
  if(fast<slow&&px<lo-atr*mult)return -1;
  return 0;
}
export function signalRsiReclaim(candles,index,params={}){
  const fastP=Math.round(n(params.fast,12)),slowP=Math.round(n(params.slow,36)),rsiP=Math.round(n(params.rsi_period,14)),longLevel=n(params.long_level,52),shortLevel=n(params.short_level,48);
  if(index<Math.max(slowP+5,rsiP+3))return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close),fast=emaSeries(closes,fastP).at(-1),slow=emaSeries(closes,slowP).at(-1),rsi=rsiSeries(closes,rsiP);
  const cur=rsi.at(-1),prev=rsi.at(-2);if(cur==null||prev==null)return 0;
  if(fast>slow&&prev<longLevel&&cur>=longLevel)return 1;
  if(fast<slow&&prev>shortLevel&&cur<=shortLevel)return -1;
  return 0;
}

export const STRATEGY_CANDIDATES = [
  {id:'trend_momentum_8_24',family:'trend_momentum',params:{fast:8,slow:24,long_rsi_min:52,long_rsi_max:72,short_rsi_max:48,short_rsi_min:28}},
  {id:'trend_momentum_12_36',family:'trend_momentum',params:{fast:12,slow:36,long_rsi_min:53,long_rsi_max:72,short_rsi_max:47,short_rsi_min:28}},
  {id:'trend_momentum_20_50',family:'trend_momentum',params:{fast:20,slow:50,long_rsi_min:52,long_rsi_max:74,short_rsi_max:48,short_rsi_min:26}},
  {id:'trend_momentum_30_80',family:'trend_momentum',params:{fast:30,slow:80,long_rsi_min:54,long_rsi_max:70,short_rsi_max:46,short_rsi_min:30}},

  {id:'scalp_trend_5_13_34',family:'scalp_trend',params:{fast:5,mid:13,slow:34,long_rsi_min:53,long_rsi_max:69,short_rsi_max:47,short_rsi_min:31}},
  {id:'scalp_trend_8_18_40',family:'scalp_trend',params:{fast:8,mid:18,slow:40,long_rsi_min:51,long_rsi_max:70,short_rsi_max:49,short_rsi_min:30}},
  {id:'scalp_trend_9_21_50',family:'scalp_trend',params:{fast:9,mid:21,slow:50,long_rsi_min:52,long_rsi_max:72,short_rsi_max:48,short_rsi_min:28}},
  {id:'scalp_trend_12_26_55',family:'scalp_trend',params:{fast:12,mid:26,slow:55,long_rsi_min:55,long_rsi_max:70,short_rsi_max:45,short_rsi_min:30}},

  {id:'mean_reversion_15',family:'mean_reversion',params:{ma:15,deviation:.014,long_rsi:30,short_rsi:70}},
  {id:'mean_reversion_20',family:'mean_reversion',params:{ma:20,deviation:.018,long_rsi:32,short_rsi:68}},
  {id:'mean_reversion_30',family:'mean_reversion',params:{ma:30,deviation:.025,long_rsi:35,short_rsi:65}},
  {id:'mean_reversion_50',family:'mean_reversion',params:{ma:50,deviation:.035,long_rsi:38,short_rsi:62}},

  {id:'donchian_breakout_15',family:'donchian_breakout',params:{lookback:15,fast:12,slow:36}},
  {id:'donchian_breakout_20',family:'donchian_breakout',params:{lookback:20,fast:20,slow:50}},
  {id:'donchian_breakout_40',family:'donchian_breakout',params:{lookback:40,fast:20,slow:50}},
  {id:'donchian_breakout_60',family:'donchian_breakout',params:{lookback:60,fast:30,slow:80}},

  {id:'bollinger_reversion_20_18',family:'bollinger_reversion',params:{period:20,mult:1.8,long_rsi:34,short_rsi:66}},
  {id:'bollinger_reversion_20_22',family:'bollinger_reversion',params:{period:20,mult:2.2,long_rsi:32,short_rsi:68}},
  {id:'bollinger_reversion_30_20',family:'bollinger_reversion',params:{period:30,mult:2.0,long_rsi:35,short_rsi:65}},
  {id:'bollinger_reversion_40_24',family:'bollinger_reversion',params:{period:40,mult:2.4,long_rsi:38,short_rsi:62}},

  {id:'pullback_trend_8_24',family:'pullback_trend',params:{fast:8,slow:24,long_rsi_min:40,long_rsi_max:54,short_rsi_min:46,short_rsi_max:60}},
  {id:'pullback_trend_12_36',family:'pullback_trend',params:{fast:12,slow:36,long_rsi_min:42,long_rsi_max:55,short_rsi_min:45,short_rsi_max:58}},
  {id:'pullback_trend_20_50',family:'pullback_trend',params:{fast:20,slow:50,long_rsi_min:40,long_rsi_max:55,short_rsi_min:45,short_rsi_max:60}},
  {id:'pullback_trend_30_80',family:'pullback_trend',params:{fast:30,slow:80,long_rsi_min:43,long_rsi_max:56,short_rsi_min:44,short_rsi_max:57}},

  {id:'atr_breakout_12',family:'atr_breakout',params:{lookback:12,atr:14,mult:.15,fast:8,slow:24}},
  {id:'atr_breakout_20',family:'atr_breakout',params:{lookback:20,atr:14,mult:.25,fast:12,slow:36}},
  {id:'atr_breakout_32',family:'atr_breakout',params:{lookback:32,atr:20,mult:.35,fast:20,slow:50}},
  {id:'atr_breakout_55',family:'atr_breakout',params:{lookback:55,atr:20,mult:.50,fast:30,slow:80}},

  {id:'rsi_reclaim_8_24',family:'rsi_reclaim',params:{fast:8,slow:24,long_level:51,short_level:49}},
  {id:'rsi_reclaim_12_36',family:'rsi_reclaim',params:{fast:12,slow:36,long_level:52,short_level:48}},
  {id:'rsi_reclaim_20_50',family:'rsi_reclaim',params:{fast:20,slow:50,long_level:54,short_level:46}},
  {id:'rsi_reclaim_30_80',family:'rsi_reclaim',params:{fast:30,slow:80,long_level:55,short_level:45}},
];
function resolveCandidate(name){
  const id=String(name||'');
  return STRATEGY_CANDIDATES.find(x=>x.id===id)
    || STRATEGY_CANDIDATES.find(x=>x.family===id)
    || STRATEGY_CANDIDATES.find(x=>x.id==='trend_momentum_20_50');
}
function inferredPeriodSeconds(candles){
  if(!Array.isArray(candles)||candles.length<2)return 300;
  const rows=candles.slice(-30),d=[];
  for(let i=1;i<rows.length;i++){const x=n(rows[i].timestamp)-n(rows[i-1].timestamp);if(x>0)d.push(x);}
  d.sort((a,b)=>a-b);return d.length?d[Math.floor(d.length/2)]:300;
}
function scaledCandidateParams(candidate,candles){
  const p={...(candidate?.params||{})},sec=inferredPeriodSeconds(candles);
  if(candidate?.family==='mean_reversion'){
    const factor=sec<=60?.18:sec<=300?.35:sec<=900?.60:sec<=1800?.80:sec<=3600?1:sec<=7200?1.10:sec<=14400?1.25:1.6;
    p.deviation=Math.max(.0015,n(p.deviation,.02)*factor);
  }
  if(candidate?.family==='bollinger_reversion'){
    const factor=sec<=60?.82:sec<=300?.90:sec<=900?.95:1;
    p.mult=Math.max(1.35,n(p.mult,2)*factor);
  }
  return p;
}
function strategySignal(name,candles,index){
  const c=resolveCandidate(name),p=scaledCandidateParams(c,candles);
  if(c.family==='scalp_trend')return signalScalpTrend(candles,index,p);
  if(c.family==='mean_reversion')return signalMeanReversion(candles,index,p);
  if(c.family==='donchian_breakout')return signalDonchianBreakout(candles,index,p);
  if(c.family==='bollinger_reversion')return signalBollingerReversion(candles,index,p);
  if(c.family==='pullback_trend')return signalPullbackTrend(candles,index,p);
  if(c.family==='atr_breakout')return signalAtrBreakout(candles,index,p);
  if(c.family==='rsi_reclaim')return signalRsiReclaim(candles,index,p);
  return signalTrendMomentum(candles,index,p);
}
function smaSeries(values,period){
  const out=Array(values.length).fill(null);if(period<1)return out;let sum=0;
  for(let i=0;i<values.length;i++){sum+=values[i];if(i>=period)sum-=values[i-period];if(i>=period-1)out[i]=sum/period;}return out;
}
function rollingStdSeries(values,period){
  const out=Array(values.length).fill(null);if(period<2)return out;let sum=0,sumSq=0;
  for(let i=0;i<values.length;i++){
    const v=values[i];sum+=v;sumSq+=v*v;
    if(i>=period){const old=values[i-period];sum-=old;sumSq-=old*old;}
    if(i>=period-1){const mean=sum/period;out[i]=Math.sqrt(Math.max(0,sumSq/period-mean*mean));}
  }
  return out;
}
function strategySignalSeries(name,candles){
  const c=resolveCandidate(name),p=scaledCandidateParams(c,candles),closes=candles.map(x=>x.close),out=Array(candles.length).fill(0);
  const rsiP=Math.round(n(p.rsi_period,14)),rsi=rsiSeries(closes,rsiP);
  if(c.family==='trend_momentum'){
    const fast=emaSeries(closes,n(p.fast,20)),slow=emaSeries(closes,n(p.slow,50));
    for(let i=Math.max(60,n(p.slow,50)+5);i<candles.length;i++){
      if(fast[i]>slow[i]&&rsi[i]>=n(p.long_rsi_min,52)&&rsi[i]<=n(p.long_rsi_max,74))out[i]=1;
      else if(fast[i]<slow[i]&&rsi[i]<=n(p.short_rsi_max,48)&&rsi[i]>=n(p.short_rsi_min,26))out[i]=-1;
    }
  }else if(c.family==='scalp_trend'){
    const e1=emaSeries(closes,n(p.fast,9)),e2=emaSeries(closes,n(p.mid,21)),e3=emaSeries(closes,n(p.slow,50));
    for(let i=Math.max(55,n(p.slow,50)+5);i<candles.length;i++){
      if(e1[i]>e2[i]&&e2[i]>e3[i]&&rsi[i]>=n(p.long_rsi_min,52)&&rsi[i]<=n(p.long_rsi_max,72)&&closes[i]>closes[i-1])out[i]=1;
      else if(e1[i]<e2[i]&&e2[i]<e3[i]&&rsi[i]<=n(p.short_rsi_max,48)&&rsi[i]>=n(p.short_rsi_min,28)&&closes[i]<closes[i-1])out[i]=-1;
    }
  }else if(c.family==='mean_reversion'){
    const ma=smaSeries(closes,Math.round(n(p.ma,30)));
    for(let i=Math.max(40,n(p.ma,30)+5);i<candles.length;i++){
      if(!ma[i]||rsi[i]==null)continue;const dev=(closes[i]-ma[i])/ma[i];
      if(dev<-n(p.deviation,.025)&&rsi[i]<n(p.long_rsi,35))out[i]=1;
      else if(dev>n(p.deviation,.025)&&rsi[i]>n(p.short_rsi,65))out[i]=-1;
    }
  }else if(c.family==='donchian_breakout'){
    const fast=emaSeries(closes,n(p.fast,20)),slow=emaSeries(closes,n(p.slow,50)),look=Math.round(n(p.lookback,30));
    for(let i=Math.max(look+2,n(p.slow,50)+5);i<candles.length;i++){
      let hi=-Infinity,lo=Infinity;for(let j=i-look;j<i;j++){hi=Math.max(hi,candles[j].high);lo=Math.min(lo,candles[j].low);}
      if(fast[i]>slow[i]&&closes[i]>hi)out[i]=1;else if(fast[i]<slow[i]&&closes[i]<lo)out[i]=-1;
    }
  }else if(c.family==='bollinger_reversion'){
    const period=Math.round(n(p.period,30)),ma=smaSeries(closes,period),std=rollingStdSeries(closes,period);
    for(let i=Math.max(period+5,rsiP+5);i<candles.length;i++){
      if(ma[i]==null||std[i]==null||rsi[i]==null||std[i]<=0)continue;
      if(closes[i]<ma[i]-n(p.mult,2)*std[i]&&rsi[i]<=n(p.long_rsi,35))out[i]=1;
      else if(closes[i]>ma[i]+n(p.mult,2)*std[i]&&rsi[i]>=n(p.short_rsi,65))out[i]=-1;
    }
  }else if(c.family==='pullback_trend'){
    const fast=emaSeries(closes,n(p.fast,20)),slow=emaSeries(closes,n(p.slow,50));
    for(let i=Math.max(n(p.slow,50)+5,rsiP+5);i<candles.length;i++){
      if(fast[i]>slow[i]&&closes[i]>slow[i]&&rsi[i]>=n(p.long_rsi_min,40)&&rsi[i]<=n(p.long_rsi_max,55))out[i]=1;
      else if(fast[i]<slow[i]&&closes[i]<slow[i]&&rsi[i]>=n(p.short_rsi_min,45)&&rsi[i]<=n(p.short_rsi_max,60))out[i]=-1;
    }
  }else if(c.family==='atr_breakout'){
    const fast=emaSeries(closes,n(p.fast,12)),slow=emaSeries(closes,n(p.slow,36)),look=Math.round(n(p.lookback,20)),atrP=Math.round(n(p.atr,14)),mult=n(p.mult,.25);
    for(let i=Math.max(look+3,atrP+3,n(p.slow,36)+5);i<candles.length;i++){
      let tr=0,hi=-Infinity,lo=Infinity;
      for(let j=i-atrP+1;j<=i;j++){const prev=j>0?candles[j-1].close:candles[j].open;tr+=Math.max(candles[j].high-candles[j].low,Math.abs(candles[j].high-prev),Math.abs(candles[j].low-prev));}
      for(let j=i-look;j<i;j++){hi=Math.max(hi,candles[j].high);lo=Math.min(lo,candles[j].low);}
      const atr=tr/atrP;if(fast[i]>slow[i]&&closes[i]>hi+atr*mult)out[i]=1;else if(fast[i]<slow[i]&&closes[i]<lo-atr*mult)out[i]=-1;
    }
  }else if(c.family==='rsi_reclaim'){
    const fast=emaSeries(closes,n(p.fast,12)),slow=emaSeries(closes,n(p.slow,36)),longLevel=n(p.long_level,52),shortLevel=n(p.short_level,48);
    for(let i=Math.max(n(p.slow,36)+5,rsiP+3);i<candles.length;i++){
      if(rsi[i]==null||rsi[i-1]==null)continue;
      if(fast[i]>slow[i]&&rsi[i-1]<longLevel&&rsi[i]>=longLevel)out[i]=1;
      else if(fast[i]<slow[i]&&rsi[i-1]>shortLevel&&rsi[i]<=shortLevel)out[i]=-1;
    }
  }
  return out;
}
function shouldSignalExit(direction,signal){return signal===-direction;}

function normalizeCandles(raw){ const rows=Array.isArray(raw)?raw:raw?.candles; if(!Array.isArray(rows))return[]; const out=rows.map(c=>Array.isArray(c)?{timestamp:n(c[0]),open:n(c[1]),high:n(c[2]),low:n(c[3]),close:n(c[4])}:{timestamp:n(c.timestamp),open:n(c.open),high:n(c.high),low:n(c.low),close:n(c.close)}).filter(c=>c.timestamp>0&&c.open>0&&c.high>0&&c.low>0&&c.close>0); out.sort((a,b)=>a.timestamp-b.timestamp); return out; }
const GMX_ORACLE_BASES={42161:'https://arbitrum-api.gmxinfra.io'};
async function fetchJsonUrl(url,label){ const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),15000);try{const r=await fetch(url,{headers:{accept:'application/json','user-agent':`MylesQuant/${VERSION}`},signal:controller.signal});const text=await r.text();if(!r.ok)throw new Error(`${label}: HTTP ${r.status} ${r.statusText} - ${text.replace(/\s+/g,' ').slice(0,400)}`);return JSON.parse(text);}finally{clearTimeout(timer);} }
async function fetchGmxCandles(chainId,symbol,timeframe,limit){ const requested=String(timeframe),derived=requested==='30m'?{base:'15m',bucket:1800}:requested==='2h'?{base:'1h',bucket:7200}:null;if(derived){const baseLimit=Math.min(10000,Math.max(160,Math.trunc(n(limit,1000))*2+4));const fine=await fetchGmxCandles(chainId,symbol,derived.base,baseLimit);const candles=aggregateCandles(fine,derived.bucket).slice(-Math.max(1,Math.trunc(n(limit,1000))));if(candles.length<Math.min(80,Number(limit)))throw new Error(`GMX derived only ${candles.length} usable ${requested} candles for ${symbol}`);return candles;} const base=GMX_ORACLE_BASES[Number(chainId)]; if(!base)throw new Error(`Unsupported chain ${chainId}`); const tokenSymbol=String(symbol).split('/')[0].toUpperCase();const url=new URL(`${base}/prices/candles`);url.searchParams.set('tokenSymbol',tokenSymbol);url.searchParams.set('period',requested);url.searchParams.set('limit',String(Math.max(1,Math.min(10000,Math.trunc(n(limit,1000))))));const raw=await fetchJsonUrl(url,`GMX ${tokenSymbol}/${requested}`);const candles=normalizeCandles(raw);if(candles.length<Math.min(80,Number(limit)))throw new Error(`GMX returned only ${candles.length} usable ${requested} candles for ${tokenSymbol}`);return candles; }
async function fetchLatestPrice(chainId,symbol){ const c=await fetchGmxCandles(chainId,symbol,'1m',2);const last=c.at(-1);return {price:last.close,timestamp:last.timestamp}; }

const KRAKEN_SPOT_PAIRS={'BTC/USD':'XBTUSD','ETH/USD':'ETHUSD','SOL/USD':'SOLUSD','XRP/USD':'XRPUSD'};
const COINBASE_PRODUCTS={'BTC/USD':'BTC-USD','ETH/USD':'ETH-USD','SOL/USD':'SOL-USD','XRP/USD':'XRP-USD'};
function sumBookSide(rows,levels=25){return (Array.isArray(rows)?rows.slice(0,levels):[]).reduce((a,x)=>a+n(Array.isArray(x)?x[1]:x?.qty),0);}
function bookImbalance(bids,asks,levels=25){const b=sumBookSide(bids,levels),a=sumBookSide(asks,levels),t=a+b;return t>0?(b-a)/t:0;}
function medianValue(values){const a=values.filter(x=>Number.isFinite(x)&&x>0).sort((x,y)=>x-y);if(!a.length)return null;const m=Math.floor(a.length/2);return a.length%2?a[m]:(a[m-1]+a[m])/2;}
function consensusFromSources(sources){
  const px=Object.values(sources||{}).map(x=>n(x?.price,NaN)).filter(Number.isFinite),median=medianValue(px);
  if(!median)return{price:null,source_count:0,dispersion_bps:null,confidence:'none'};
  const lo=Math.min(...px),hi=Math.max(...px),disp=(hi-lo)/median*10000;
  return{price:round(median,8),source_count:px.length,dispersion_bps:round(disp,2),confidence:px.length>=3&&disp<=20?'high':px.length>=2&&disp<=50?'medium':'low'};
}
function tradeFlowFromKraken(raw){
  const result=raw?.result;if(!result||typeof result!=='object')return 0;
  const key=Object.keys(result).find(k=>k!=='last'),rows=key?result[key]:[];let buy=0,sell=0;
  for(const t of Array.isArray(rows)?rows:[]){const size=n(t?.[1]),side=String(t?.[3]||'').toLowerCase();if(side==='b')buy+=size;else if(side==='s')sell+=size;}
  return buy+sell>0?(buy-sell)/(buy+sell):0;
}
function tradeFlowFromCoinbase(rows){
  let buy=0,sell=0;
  for(const t of Array.isArray(rows)?rows:[]){const size=n(t?.size),maker=String(t?.side||'').toLowerCase();if(maker==='sell')buy+=size;else if(maker==='buy')sell+=size;}
  return buy+sell>0?(buy-sell)/(buy+sell):0;
}
async function fetchKrakenSnapshot(symbol,config){
  const pair=KRAKEN_SPOT_PAIRS[symbol];if(!pair)return{available:false,reason:'unsupported_pair'};
  const levels=n(config.multi_source?.orderbook_levels,25),sample=n(config.multi_source?.trade_sample,100);
  const [tickerR,depthR,tradesR]=await Promise.allSettled([
    fetchJsonUrl(`https://api.kraken.com/0/public/Ticker?pair=${encodeURIComponent(pair)}`,`Kraken ticker ${pair}`),
    fetchJsonUrl(`https://api.kraken.com/0/public/Depth?pair=${encodeURIComponent(pair)}&count=${levels}`,`Kraken depth ${pair}`),
    fetchJsonUrl(`https://api.kraken.com/0/public/Trades?pair=${encodeURIComponent(pair)}`,`Kraken trades ${pair}`)
  ]);
  if(tickerR.status!=='fulfilled')return{available:false,reason:String(tickerR.reason?.message||tickerR.reason)};
  const tr=tickerR.value?.result||{},tk=tr[Object.keys(tr)[0]]||{},price=n(tk?.c?.[0],NaN);
  const dr=depthR.status==='fulfilled'?(depthR.value?.result||{}):{},book=dr[Object.keys(dr)[0]]||{};
  const flow=tradesR.status==='fulfilled'?tradeFlowFromKraken(tradesR.value):0;
  return{available:Number.isFinite(price),price:round(price,8),orderbook_imbalance:round(bookImbalance(book.bids,book.asks,levels),4),trade_imbalance:round(flow,4),sample_size:sample,source:'Kraken Spot'};
}
async function fetchCoinbaseSnapshot(symbol,config){
  const product=COINBASE_PRODUCTS[symbol];if(!product)return{available:false,reason:'unsupported_pair'};
  const levels=n(config.multi_source?.orderbook_levels,25),sample=Math.min(100,n(config.multi_source?.trade_sample,100));
  const base=`https://api.exchange.coinbase.com/products/${encodeURIComponent(product)}`;
  const [tickerR,bookR,tradesR]=await Promise.allSettled([
    fetchJsonUrl(`${base}/ticker`,`Coinbase ticker ${product}`),
    fetchJsonUrl(`${base}/book?level=1`,`Coinbase book ${product}`),
    fetchJsonUrl(`${base}/trades?limit=${sample}`,`Coinbase trades ${product}`)
  ]);
  if(tickerR.status!=='fulfilled')return{available:false,reason:String(tickerR.reason?.message||tickerR.reason)};
  const price=n(tickerR.value?.price,NaN),book=bookR.status==='fulfilled'?bookR.value:{},flow=tradesR.status==='fulfilled'?tradeFlowFromCoinbase(tradesR.value):0;
  return{available:Number.isFinite(price),price:round(price,8),bid:n(tickerR.value?.bid,null),ask:n(tickerR.value?.ask,null),orderbook_imbalance:round(bookImbalance(book?.bids,book?.asks,levels),4),trade_imbalance:round(flow,4),sample_size:sample,source:'Coinbase Exchange'};
}
function sourceFlowScore(sources){
  const vals=[];
  for(const row of Object.values(sources||{})){if(!row?.available)continue;for(const k of ['orderbook_imbalance','trade_imbalance']){const v=Number(row?.[k]);if(Number.isFinite(v))vals.push(clamp(v,-1,1));}}
  return vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:0;
}
async function refreshMultiSourceIntelligence(config,enabled,latest){
  const refresh=Math.max(30,n(config.multi_source?.refresh_seconds,60)),prior=readJson(MULTI_SOURCE_FILE,null),priorTs=prior?.generated_at?Date.parse(prior.generated_at):0;
  if(prior&&Date.now()-priorTs<refresh*1000&&n(prior.market_count,0)===enabled.length)return prior;
  const markets={},errors={};
  await Promise.all(enabled.map(async symbol=>{
    const sources={};
    if(config.multi_source?.sources?.gmx!==false&&latest[symbol])sources.gmx={available:true,price:round(n(latest[symbol].price),8),timestamp:latest[symbol].timestamp,source:'GMX Oracle'};
    const jobs=[];
    if(config.multi_source?.sources?.kraken!==false)jobs.push(fetchKrakenSnapshot(symbol,config).then(x=>sources.kraken=x).catch(e=>sources.kraken={available:false,reason:String(e?.message||e)}));
    if(config.multi_source?.sources?.coinbase!==false)jobs.push(fetchCoinbaseSnapshot(symbol,config).then(x=>sources.coinbase=x).catch(e=>sources.coinbase={available:false,reason:String(e?.message||e)}));
    await Promise.all(jobs);
    const consensus=consensusFromSources(sources),flow=sourceFlowScore(sources),maxDisp=n(config.multi_source?.max_price_dispersion_bps,40);
    markets[symbol]={sources,consensus,cross_venue_flow:round(flow,4),price_agreement:consensus.dispersion_bps==null?'unknown':consensus.dispersion_bps<=maxDisp?'aligned':'divergent'};
    const usable=Object.values(sources).filter(x=>x?.available).length;if(usable<1)errors[symbol]='no usable public market source';
  }));
  const health={};
  for(const name of ['gmx','kraken','coinbase'])health[name]={ok_markets:Object.values(markets).filter(m=>m.sources?.[name]?.available).length,total_markets:enabled.length};
  const out={generated_at:iso(),refresh_seconds:refresh,markets,health,errors,market_count:Object.keys(markets).length,error_count:Object.keys(errors).length};
  writeJsonAtomic(MULTI_SOURCE_FILE,out);return out;
}
function classifyRegime(row,intel){
  const m15=row?.m15||{},h4=row?.h4||{},shortTrend=m15.trend||'flat',longTrend=h4.trend||'flat',vol=n(m15.realized_vol_pct,0),flow=n(intel?.cross_venue_flow,0);
  let regime='range';
  if(shortTrend===longTrend&&shortTrend!=='flat')regime=vol>=1.2?'high_vol_trend':'trend';
  else if(vol>=1.5)regime='high_vol_chop';
  else if(shortTrend!==longTrend)regime='transition';
  const bias=(shortTrend==='up'?1:shortTrend==='down'?-1:0)+(longTrend==='up'?1:longTrend==='down'?-1:0)+(flow>.12?1:flow<-.12?-1:0);
  return{regime,bias:bias>=2?'long':bias<=-2?'short':'neutral',flow:round(flow,3),volatility:round(vol,3),trend_alignment:shortTrend===longTrend&&shortTrend!=='flat',short_trend:shortTrend,long_trend:longTrend};
}
function familyRegimeFit(family,regime){
  const table={
    trend:{trend_momentum:1,scalp_trend:.9,pullback_trend:1,rsi_reclaim:.9,donchian_breakout:.7,atr_breakout:.7,mean_reversion:.15,bollinger_reversion:.2},
    high_vol_trend:{atr_breakout:1,donchian_breakout:1,trend_momentum:.9,pullback_trend:.8,rsi_reclaim:.8,scalp_trend:.7,mean_reversion:.1,bollinger_reversion:.15},
    range:{mean_reversion:1,bollinger_reversion:1,rsi_reclaim:.55,scalp_trend:.35,pullback_trend:.25,trend_momentum:.2,atr_breakout:.15,donchian_breakout:.15},
    high_vol_chop:{bollinger_reversion:.75,mean_reversion:.65,atr_breakout:.5,rsi_reclaim:.45,donchian_breakout:.35,scalp_trend:.3,trend_momentum:.2,pullback_trend:.2},
    transition:{rsi_reclaim:.9,pullback_trend:.8,atr_breakout:.7,donchian_breakout:.65,trend_momentum:.55,scalp_trend:.55,mean_reversion:.45,bollinger_reversion:.45}
  };return n(table[regime]?.[family],.4);
}
function buildResearchPipeline(marketResearch,multiSource,results){
  const markets={},hypotheses=[];
  for(const [symbol,row] of Object.entries(marketResearch?.markets||{})){
    const intel=multiSource?.markets?.[symbol]||{},reg=classifyRegime(row,intel),disp=n(intel?.consensus?.dispersion_bps,999),sourceCount=n(intel?.consensus?.source_count,0);
    const opportunity=clamp(35+(reg.trend_alignment?18:0)+Math.min(20,Math.abs(reg.flow)*40)+(sourceCount>=3?12:sourceCount===2?6:0)-(disp>50?20:disp>25?8:0),0,100);
    markets[symbol]={...reg,opportunity_score:round(opportunity,1),consensus_price:intel?.consensus?.price??null,dispersion_bps:intel?.consensus?.dispersion_bps??null,source_count:sourceCount,price_agreement:intel?.price_agreement||'unknown'};
    const families=[...new Set((results||[]).filter(r=>r.symbol===symbol).map(r=>r.family))];
    for(const family of families){
      const fit=familyRegimeFit(family,reg.regime),ranked=(results||[]).filter(r=>r.symbol===symbol&&r.family===family).sort((a,b)=>candidateScore(b)-candidateScore(a));
      const best=ranked[0];if(!best)continue;
      const score=clamp(opportunity*.45+fit*40+clamp(n(best.stress?.return_pct,-10)+5,0,10)*1.5,0,100);
      hypotheses.push({symbol,family,regime:reg.regime,bias:reg.bias,fit:round(fit,2),score:round(score,1),strategy:best.strategy,stress_return_pct:best.stress.return_pct,profit_factor:best.base.profit_factor,win_rate:best.base.win_rate,thesis:`${family.replaceAll('_',' ')} tested for ${reg.regime.replaceAll('_',' ')} conditions with ${reg.bias} context and ${sourceCount}-source price confirmation.`});
    }
  }
  hypotheses.sort((a,b)=>b.score-a.score);
  return{generated_at:iso(),process:['multi_source_data','regime_detection','opportunity_scan','hypothesis_ranking','stressed_backtest','walk_forward','paper_lab','validation'],markets,hypotheses:hypotheses.slice(0,10),top_hypotheses:hypotheses.slice(0,5)};
}

function costs(config,mult=1){ return {fee:n(config.research_costs.position_fee_bps_per_side,6)/10000*mult,slip:n(config.research_costs.slippage_bps_per_side,5)/10000*mult,impact:n(config.research_costs.impact_bps_per_side,20)/10000*mult,holding:n(config.research_costs.holding_cost_bps_per_day,5)/10000*mult}; }
function entryFill(mark,direction,cost){ return mark*(1+direction*cost.slip); }
function exitFill(mark,direction,cost){ return mark*(1-direction*(cost.slip+cost.impact)); }
function positionSize(equity,config,entry){ const riskPct=n(config.risk.max_risk_per_trade_pct,.5)/100,stopPct=n(config.risk.stop_loss_pct,1.5)/100,lev=n(config.risk.max_notional_leverage,1.5),alloc=n(config.risk.max_market_allocation_pct,35)/100,maxUsd=n(config.risk.max_position_usd,0); const riskBudget=equity*riskPct;const byRisk=riskBudget/Math.max(.0001,stopPct);const dollarCap=maxUsd>0?maxUsd:Infinity;const notional=Math.min(equity*lev,equity*alloc,byRisk,dollarCap);return {notional,units:notional/entry,risk_budget:riskBudget}; }
function stopTarget(entry,direction,config){const s=n(config.risk.stop_loss_pct,1.5)/100,t=n(config.risk.take_profit_pct,3)/100;return{stop:entry*(1-direction*s),target:entry*(1+direction*t)};}
function intrabarExit(position,candle){ if(position.direction>0){const stopHit=candle.low<=position.stop,targetHit=candle.high>=position.target;if(stopHit)return{reason:targetHit?'stop_and_target_same_candle_conservative_stop':'stop_loss',raw:position.stop};if(targetHit)return{reason:'take_profit',raw:position.target};}else{const stopHit=candle.high>=position.stop,targetHit=candle.low<=position.target;if(stopHit)return{reason:targetHit?'stop_and_target_same_candle_conservative_stop':'stop_loss',raw:position.stop};if(targetHit)return{reason:'take_profit',raw:position.target};}return null; }
function manualMarkExit(position,mark){
  if(!Number.isFinite(mark)||mark<=0)return null;
  if(position.direction>0){
    if(mark<=position.stop)return{reason:'stop_loss',raw:mark};
    if(mark>=position.target)return{reason:'take_profit',raw:mark};
  }else{
    if(mark>=position.stop)return{reason:'stop_loss',raw:mark};
    if(mark<=position.target)return{reason:'take_profit',raw:mark};
  }
  return null;
}
function holdingCost(position,exitTs,cost){const days=Math.max(0,(exitTs-position.opened_ts)/86400);return position.notional*cost.holding*days;}
function closeCalc(position,rawExit,exitTs,cost){const exit=exitFill(rawExit,position.direction,cost),gross=position.direction*position.units*(exit-position.entry),exitFee=Math.abs(position.units*exit)*cost.fee,hold=holdingCost(position,exitTs,cost),net=gross-position.entry_fee-exitFee-hold;return{exit,gross,exit_fee:exitFee,holding_cost:hold,net};}

export function backtest(candles,strategyName,config,{costMultiplier=1}={}){
  const start=n(config.starting_equity,10000),cost=costs(config,costMultiplier);let cash=start,position=null,wins=0,losses=0,lastEntryIndex=-1e9;const trades=[],curve=[];
  const signals=strategySignalSeries(strategyName,candles),maxHold=Math.round(n(config.risk.max_holding_bars,72));
  for(let i=60;i<candles.length;i++){
    const c=candles[i],signal=n(signals[i],0);let exitedThisCandle=false;
    if(position){
      let ex=intrabarExit(position,c);
      if(!ex&&shouldSignalExit(position.direction,signal))ex={reason:'opposite_signal_exit',raw:c.close};
      if(!ex&&i-position.opened_index>=maxHold)ex={reason:'max_holding_bars',raw:c.close};
      if(ex){
        const calc=closeCalc(position,ex.raw,c.timestamp,cost);cash+=calc.gross-calc.exit_fee-calc.holding_cost;
        const pnl=calc.net,ret=pnl/Math.max(1,position.notional)*100;
        trades.push({entry_time:new Date(position.opened_ts*1000).toISOString(),exit_time:new Date(c.timestamp*1000).toISOString(),side:position.direction>0?'long':'short',entry:round(position.entry,4),exit:round(calc.exit,4),pnl:round(pnl,2),return_pct:round(ret,3),reason:ex.reason});
        if(pnl>0)wins++;else losses++;position=null;exitedThisCandle=true;
      }
    }
    if(!position&&!exitedThisCandle&&signal!==0&&(i-lastEntryIndex)>=n(config.paper?.entry_cooldown_bars,0)){
      const entry=entryFill(c.close,signal,cost),sz=positionSize(cash,config,entry),st=stopTarget(entry,signal,config),entryFee=Math.abs(sz.notional)*cost.fee;
      cash-=entryFee;position={direction:signal,entry,units:sz.units,notional:sz.notional,entry_fee:entryFee,stop:st.stop,target:st.target,opened_ts:c.timestamp,opened_index:i};lastEntryIndex=i;
    }
    const unreal=position?position.direction*position.units*(c.close-position.entry):0;curve.push({timestamp:c.timestamp,equity:round(cash+unreal,2)});
  }
  if(position&&candles.length){
    const c=candles.at(-1),calc=closeCalc(position,c.close,c.timestamp,cost);cash+=calc.gross-calc.exit_fee-calc.holding_cost;
    const pnl=calc.net,ret=pnl/Math.max(1,position.notional)*100;
    trades.push({entry_time:new Date(position.opened_ts*1000).toISOString(),exit_time:new Date(c.timestamp*1000).toISOString(),side:position.direction>0?'long':'short',entry:round(position.entry,4),exit:round(calc.exit,4),pnl:round(pnl,2),return_pct:round(ret,3),reason:'end_of_test'});if(pnl>0)wins++;else losses++;curve.push({timestamp:c.timestamp,equity:round(cash,2)});
  }
  const grossWins=trades.filter(t=>t.pnl>0).reduce((a,t)=>a+t.pnl,0),grossLosses=Math.abs(trades.filter(t=>t.pnl<0).reduce((a,t)=>a+t.pnl,0));
  const profitFactor=grossLosses>0?grossWins/grossLosses:(grossWins>0?99:0);
  const expectancyPct=trades.length?trades.reduce((a,t)=>a+n(t.return_pct),0)/trades.length:0;
  const candidate=resolveCandidate(strategyName);
  return{strategy:candidate.id,family:candidate.family,params:candidate.params,starting_equity:start,ending_equity:round(cash,2),pnl:round(cash-start,2),return_pct:round((cash/start-1)*100,3),win_rate:trades.length?round(wins/trades.length*100,2):0,trades:trades.length,max_drawdown:round(maxDrawdown(curve.map(x=>x.equity)),3),profit_factor:round(profitFactor,3),expectancy_pct:round(expectancyPct,4),equity_curve:curve,recent_trades:trades.slice(-30),cost_multiplier:costMultiplier};
}
export function walkForward(candles,strategyName,config){
  const candidate=resolveCandidate(strategyName);
  if(candles.length<2400)return{strategy:candidate.id,family:candidate.family,params:candidate.params,status:'insufficient_history',windows:[]};
  const windows=[],train=1200,test=600,step=600;
  for(let start=0;start+train+test<=candles.length;start+=step){
    const seg=candles.slice(Math.max(0,start+train-120),start+train+test),r=backtest(seg,strategyName,config);
    windows.push({start:new Date(candles[start+train].timestamp*1000).toISOString(),end:new Date(candles[start+train+test-1].timestamp*1000).toISOString(),return_pct:r.return_pct,win_rate:r.win_rate,max_drawdown:r.max_drawdown,trades:r.trades,profit_factor:r.profit_factor,expectancy_pct:r.expectancy_pct});
  }
  return{strategy:candidate.id,family:candidate.family,params:candidate.params,status:'complete',windows,positive_windows:windows.filter(w=>w.return_pct>0).length,total_windows:windows.length,median_return_pct:round([...windows].sort((a,b)=>a.return_pct-b.return_pct)[Math.floor(windows.length/2)]?.return_pct||0,3)};
}
function validationFor(base,stress,wf,config){
  const v=config.validation,total=Math.max(1,wf.total_windows||0),positivePct=(wf.positive_windows||0)/total*100;
  const checks={
    min_trades:base.trades>=n(v.min_trades,18),
    base_return:base.return_pct>=n(v.min_base_return_pct,.5),
    stress_return:stress.return_pct>=n(v.min_stress_return_pct,0),
    profit_factor:base.profit_factor>=n(v.min_profit_factor,1.10),
    expectancy:base.expectancy_pct>=n(v.min_expectancy_pct,.01),
    max_drawdown:base.max_drawdown<=n(v.max_drawdown_pct,10),
    walk_forward_positive_pct:wf.status==='complete'&&positivePct>=n(v.min_walk_forward_positive_pct,60)
  };
  return{pass:Object.values(checks).every(Boolean),checks,walk_forward_positive_pct:round(positivePct,1)};
}
function researchEligible(r){
  const total=Math.max(1,n(r?.walk_forward?.total_windows,0)),positivePct=n(r?.walk_forward?.positive_windows,0)/total*100;
  return n(r?.base?.trades,0)>=8
    && n(r?.base?.return_pct,-999)>0
    && n(r?.base?.profit_factor,0)>=1
    && n(r?.stress?.return_pct,-999)>-1
    && positivePct>=33;
}
function researchFallbackEligible(r,config){
  if(config?.research_exploration?.fallback_near_miss===false)return false;
  const maxLoss=n(config?.research_exploration?.fallback_max_stress_loss_pct,.75);
  return n(r?.base?.trades,0)>=8
    && n(r?.stress?.return_pct,-999)>=-maxLoss
    && n(r?.base?.profit_factor,0)>=n(config?.research_exploration?.fallback_min_profit_factor,.85)
    && n(r?.base?.win_rate,0)>=n(config?.research_exploration?.fallback_min_win_rate_pct,30)
    && n(r?.base?.max_drawdown,999)<=Math.max(15,n(config?.validation?.max_drawdown_pct,10)*1.5);
}
function researchForwardEligible(r,config){return researchEligible(r)||researchFallbackEligible(r,config);}


function tournamentCandidateRows(results,candlesBySymbol,config){
  const maxLoss=n(config.research_exploration?.tournament_max_stress_loss_pct,25),minPf=n(config.research_exploration?.tournament_min_profit_factor,.20),maxDd=n(config.research_exploration?.tournament_max_drawdown_pct,30);
  const rows=(results||[]).filter(r=>n(r?.base?.trades,0)>=3&&n(r?.stress?.return_pct,-999)>=-maxLoss&&n(r?.base?.profit_factor,0)>=minPf&&n(r?.base?.max_drawdown,999)<=maxDd).map(r=>{
    const candles=candlesBySymbol?.[r.symbol]||[],idx=candles.length-2,signal=idx>=0?strategySignal(r.strategy,candles,idx):0;
    const experimentScore=candidateScore(r)+n(r.context_score,0)*.2+(signal!==0?35:0)+(r.validation?.pass?100:0)+(researchEligible(r)?45:0);
    return{...r,current_signal:signal,experiment_score:experimentScore};
  }).sort((a,b)=>n(b.experiment_score)-n(a.experiment_score));
  const target=Math.max(4,n(config.research_exploration?.tournament_slots,8)),picked=[],familyCount={},symbolCount={};
  for(const r of rows){
    if(picked.length>=target)break;
    if(n(familyCount[r.family])>=1||n(symbolCount[r.symbol])>=2)continue;
    picked.push(r);familyCount[r.family]=n(familyCount[r.family])+1;symbolCount[r.symbol]=n(symbolCount[r.symbol])+1;
  }
  for(const r of rows){
    if(picked.length>=target)break;
    if(picked.some(x=>x.symbol===r.symbol&&x.strategy===r.strategy)||n(symbolCount[r.symbol])>=3)continue;
    picked.push(r);familyCount[r.family]=n(familyCount[r.family])+1;symbolCount[r.symbol]=n(symbolCount[r.symbol])+1;
  }
  return picked;
}
function createTournamentState(config){return{version:1,created_at:iso(),last_cycle_at:iso(),slots:{},recent_trades:[]};}
function ensureTournamentState(state,config){if(!state||state.version!==1)return createTournamentState(config);state.slots=state.slots||{};state.recent_trades=Array.isArray(state.recent_trades)?state.recent_trades:[];return state;}
function tournamentSlot(key,row,config){const e=n(config.research_exploration?.tournament_slot_equity,1250),ts=Math.floor(Date.now()/1000);return{key,symbol:row.symbol,strategy:row.strategy,family:row.family,created_at:iso(),starting_equity:e,cash:e,realized_pnl:0,position:null,wins:0,losses:0,trades:[],equity_curve:[{timestamp:ts,equity:round(e,2)}],last_candle_ts:0,last_entry_ts:0,last_decision:{at:iso(),signal:'flat',reason:'initialized'},retired:false};}
function tournamentSlotEquity(slot,latest){let eq=n(slot.cash,slot.starting_equity);if(slot.position){const p=slot.position,mark=n(latest[p.symbol]?.price,p.mark||p.entry);p.mark=mark;p.unrealized_pnl=round(p.direction*p.units*(mark-p.entry),2);eq+=p.unrealized_pnl;}return eq;}
function tournamentPositionSize(slotEq,config,entry){const riskPct=n(config.research_exploration?.tournament_risk_per_trade_pct,.25)/100,stopPct=n(config.risk.stop_loss_pct,1.5)/100,riskBudget=slotEq*riskPct,notional=Math.min(slotEq*.35,riskBudget/Math.max(.0001,stopPct)),leverage=clamp(n(config.risk.max_notional_leverage,1.5),1,5),margin=notional/Math.max(1,leverage);return{notional,units:notional/entry,leverage,margin};}
function closeTournamentPosition(slot,rawExit,ts,cost,reason,state){const p=slot.position;if(!p)return;const calc=closeCalc(p,rawExit,ts,cost);slot.cash+=calc.gross-calc.exit_fee-calc.holding_cost;slot.realized_pnl+=calc.net;const tr={book_key:slot.key,symbol:p.symbol,side:p.direction>0?'long':'short',strategy:p.strategy,entry:round(p.entry,4),exit:round(calc.exit,4),pnl:round(calc.net,2),notional:round(n(p.notional),2),margin_usd:round(n(p.margin_usd,p.notional/Math.max(1,n(p.leverage,1))),2),leverage:round(n(p.leverage,1),2),opened_at:new Date(p.opened_ts*1000).toISOString(),closed_at:new Date(ts*1000).toISOString(),reason,source:'research_tournament'};slot.trades.push(tr);state.recent_trades.push(tr);if(calc.net>0)slot.wins++;else slot.losses++;slot.position=null;}
function updateResearchTournament(state,candlesBySymbol,latest,config,results=[]){
  state=ensureTournamentState(state,config);state.last_cycle_at=iso();
  const selected=tournamentCandidateRows(results,candlesBySymbol,config),selectedKeys=new Set(selected.map(r=>`${r.symbol}|${r.strategy}`)),cost=costs(config,1);
  for(const row of selected){const key=`${row.symbol}|${row.strategy}`;if(!state.slots[key])state.slots[key]=tournamentSlot(key,row,config);state.slots[key].retired=false;state.slots[key].family=row.family;}
  for(const [key,slot] of Object.entries(state.slots)){if(!selectedKeys.has(key)&&!slot.position)slot.retired=true;}
  for(const row of selected){
    const key=`${row.symbol}|${row.strategy}`,slot=state.slots[key],candles=candlesBySymbol[row.symbol]||[],idx=candles.length-2,c=candles[idx];if(!c)continue;
    if(n(slot.last_candle_ts)>=n(c.timestamp))continue;
    let exited=false,exitReason=null;
    if(slot.position){const sig=strategySignal(slot.strategy,candles,idx);let ex=intrabarExit(slot.position,c);if(!ex&&shouldSignalExit(slot.position.direction,sig))ex={reason:'opposite_signal_exit',raw:c.close};if(!ex&&((c.timestamp-n(slot.position.opened_ts))/periodSeconds(config.timeframe))>=n(config.risk.max_holding_bars,72))ex={reason:'max_holding_bars',raw:c.close};if(ex){closeTournamentPosition(slot,ex.raw,latest[row.symbol]?.timestamp||c.timestamp,cost,ex.reason,state);exited=true;exitReason=ex.reason;}}
    const signal=strategySignal(row.strategy,candles,idx),cool=n(config.research_exploration?.entry_cooldown_bars,0),barsSince=(c.timestamp-n(slot.last_entry_ts,0))/periodSeconds(config.timeframe),ready=!slot.last_entry_ts||barsSince>=cool;
    if(!slot.position&&!exited&&signal!==0&&ready){const eq=tournamentSlotEquity(slot,latest),entry=entryFill(c.close,signal,cost),sz=tournamentPositionSize(eq,config,entry),st=stopTarget(entry,signal,config),entryFee=sz.notional*cost.fee;slot.cash-=entryFee;slot.position={symbol:row.symbol,strategy:row.strategy,direction:signal,entry:round(entry,6),units:sz.units,notional:round(sz.notional,2),margin_usd:round(sz.margin,2),leverage:round(sz.leverage,2),entry_fee:entryFee,stop:round(st.stop,6),target:round(st.target,6),opened_ts:c.timestamp,mark:c.close,unrealized_pnl:0};slot.last_entry_ts=c.timestamp;slot.last_decision={at:new Date(c.timestamp*1000).toISOString(),signal:researchSignalName(signal),reason:signal>0?'opened_long':'opened_short'};}
    else slot.last_decision={at:new Date(c.timestamp*1000).toISOString(),signal:researchSignalName(signal),reason:slot.position?'position_open':exited?(exitReason||'exited_this_candle'):signal===0?'waiting_for_strategy_signal':!ready?'entry_cooldown':'waiting'};
    slot.last_candle_ts=c.timestamp;const eq=tournamentSlotEquity(slot,latest);slot.equity_curve.push({timestamp:c.timestamp,equity:round(eq,2)});slot.equity_curve=slot.equity_curve.slice(-1200);slot.trades=slot.trades.slice(-300);
  }
  const heartbeatTs=Math.floor(Date.now()/1000);
  for(const row of selected){
    const key=`${row.symbol}|${row.strategy}`,slot=state.slots[key];if(!slot)continue;
    const eq=tournamentSlotEquity(slot,latest),curve=Array.isArray(slot.equity_curve)?slot.equity_curve:(slot.equity_curve=[]),last=curve.at(-1);
    if(last&&n(last.timestamp)===heartbeatTs)last.equity=round(eq,2);else curve.push({timestamp:heartbeatTs,equity:round(eq,2)});
    slot.equity_curve=curve.slice(-7200);
  }
  state.recent_trades=state.recent_trades.slice(-500);return state;
}
function tournamentAggregateCurve(state,selected,config){
  const rows=(selected||[]).map(row=>{const key=`${row.symbol}|${row.strategy}`,slot=state.slots?.[key];return slot?{slot,start:n(slot.starting_equity,n(config.research_exploration?.tournament_slot_equity,1250)),curve:Array.isArray(slot.equity_curve)?slot.equity_curve:[]}:null;}).filter(Boolean);
  if(!rows.length)return[];
  const stamps=[...new Set(rows.flatMap(x=>x.curve.map(p=>n(p.timestamp,0)).filter(Boolean)))].sort((a,b)=>a-b).slice(-1800);
  const ptr=rows.map(()=>0),last=rows.map(x=>x.start);
  return stamps.map(ts=>{for(let i=0;i<rows.length;i++){const curve=rows[i].curve;while(ptr[i]<curve.length&&n(curve[ptr[i]].timestamp,0)<=ts){last[i]=n(curve[ptr[i]].equity,last[i]);ptr[i]++;}}return{timestamp:ts,equity:round(last.reduce((a,b)=>a+b,0),2)};});
}
function tournamentTelemetry(state,latest,config,results,candlesBySymbol){state=ensureTournamentState(state,config);const selected=tournamentCandidateRows(results,candlesBySymbol,config),selectedKeys=new Set(selected.map(r=>`${r.symbol}|${r.strategy}`));const books=[];for(const row of selected){const key=`${row.symbol}|${row.strategy}`,slot=state.slots[key]||tournamentSlot(key,row,config),eq=tournamentSlotEquity(slot,latest),start=n(slot.starting_equity,1250),tr=slot.trades||[];books.push({key,symbol:row.symbol,strategy:row.strategy,family:row.family,regime:row.regime||null,hypothesis:row.hypothesis||null,signal:researchSignalName(row.current_signal||0),backtest_pnl:round(n(row.base?.pnl),2),stress_pnl:round(n(row.stress?.pnl),2),backtest_return_pct:round(n(row.base?.return_pct),3),stress_return_pct:round(n(row.stress?.return_pct),3),profit_factor:round(n(row.base?.profit_factor),3),win_rate:round(n(row.base?.win_rate),2),paper_equity:round(eq,2),paper_pnl:round(eq-start,2),paper_realized_pnl:round(n(slot.realized_pnl),2),paper_unrealized_pnl:round(n(slot.position?.unrealized_pnl),2),paper_trades:tr.length,paper_win_rate:tr.length?round(n(slot.wins)/tr.length*100,2):0,sim_leverage:round(clamp(n(config.risk.max_notional_leverage,1.5),1,5),2),open_position:slot.position?{side:slot.position.direction>0?'long':'short',entry:slot.position.entry,mark:slot.position.mark,notional:slot.position.notional,margin_usd:slot.position.margin_usd??round(n(slot.position.notional)/Math.max(1,n(slot.position.leverage,1)),2),leverage:slot.position.leverage??round(clamp(n(config.risk.max_notional_leverage,1.5),1,5),2),unrealized_pnl:slot.position.unrealized_pnl}:null,last_decision:slot.last_decision||null,experiment_score:round(n(row.experiment_score),2)});}
  const aggregateStart=books.reduce((a,b)=>a+n(config.research_exploration?.tournament_slot_equity,1250),0),aggregateEquity=books.reduce((a,b)=>a+n(b.paper_equity),0),closed=books.reduce((a,b)=>a+n(b.paper_trades),0),wins=books.reduce((a,b)=>a+Math.round(n(b.paper_win_rate)*n(b.paper_trades)/100),0),equityCurve=tournamentAggregateCurve(state,selected,config);
  return{enabled:config.research_exploration?.tournament_enabled!==false,mode:'PARALLEL RESEARCH TOURNAMENT',slot_count:books.length,starting_equity:round(aggregateStart,2),equity:round(aggregateEquity,2),pnl:round(aggregateEquity-aggregateStart,2),trades:closed,win_rate:closed?round(wins/closed*100,2):0,open_positions:books.filter(b=>b.open_position).length,equity_curve:equityCurve,last_point_at:equityCurve.length?equityCurve.at(-1).timestamp:null,books,recent_trades:(state.recent_trades||[]).slice(-80),last_cycle_at:state.last_cycle_at||null,note:'Independent simulated experiment books. They are allowed to lose; their purpose is to create forward evidence in dollars. Tournament results never bypass strict validation or enable live trading.'};}

function createPaperState(config){const e=n(config.starting_equity,10000),ts=Math.floor(Date.now()/1000);return{version:3,created_at:iso(),starting_equity:e,cash:e,realized_pnl:0,positions:{},wins:0,losses:0,trades:[],equity_curve:[{timestamp:ts,equity:round(e,2)}],day_key:new Date().toISOString().slice(0,10),day_start_equity:e,peak_equity:e,halted:false,halt_reason:null,last_candle_ts:{},last_entry_ts:{}};}
function stateEquity(state,latest){let eq=n(state.cash,0);for(const [symbol,p] of Object.entries(state.positions||{})){const mark=n(latest[symbol]?.price,p.mark||p.entry);p.mark=mark;p.unrealized_pnl=round(p.direction*p.units*(mark-p.entry),2);eq+=p.unrealized_pnl;}return eq;}
function closePaperPosition(state,symbol,rawExit,ts,cost,reason){const p=state.positions[symbol];if(!p)return;const calc=closeCalc(p,rawExit,ts,cost);state.cash+=calc.gross-calc.exit_fee-calc.holding_cost;state.realized_pnl+=calc.net;state.trades.push({symbol,side:p.direction>0?'long':'short',entry:round(p.entry,4),exit:round(calc.exit,4),pnl:round(calc.net,2),opened_at:new Date(p.opened_ts*1000).toISOString(),closed_at:new Date(ts*1000).toISOString(),reason,strategy:p.strategy||null,source:p.source||'auto'});if(calc.net>0)state.wins++;else state.losses++;delete state.positions[symbol];}
function poorForwardPerformance(state,eq){const start=Math.max(1,n(state.starting_equity,10000)),trades=state.trades||[],auto=trades.filter(t=>(t.source||'auto')==='auto'),wins=auto.filter(t=>n(t.pnl,0)>0).length,winRate=auto.length?wins/auto.length*100:0;return ((eq-start)/start*100<=-2)||(auto.length>=12&&winRate<35);}
function candidateScore(r){
  const eligible=researchEligible(r),pf=Math.min(4,n(r?.base?.profit_factor,0)),expect=n(r?.base?.expectancy_pct,0);
  const score=n(r?.stress?.return_pct)*4+n(r?.base?.return_pct)*2+n(r?.validation?.walk_forward_positive_pct)*.12+pf*3+expect*12-n(r?.base?.max_drawdown)*.8+Math.min(50,n(r?.base?.trades))*.03+n(r?.context_score,0)*.08;
  return eligible?score:score-100;
}
function adaptiveStrategy(symbol,configured,results,enabled=true){const fallback=resolveCandidate(configured).id;if(!enabled)return fallback;const passing=results.filter(r=>r.symbol===symbol&&r.validation?.pass===true).sort((a,b)=>candidateScore(b)-candidateScore(a));return passing[0]?.strategy||fallback;}
function bestResearchCandidate(symbol,results){return results.filter(r=>r.symbol===symbol&&n(r?.base?.trades)>=3).sort((a,b)=>candidateScore(b)-candidateScore(a))[0]||null;}

function volatilityPct(candles,lookback=96){
  const rows=(candles||[]).slice(-lookback);
  if(rows.length<3)return 0;
  const rets=[];
  for(let i=1;i<rows.length;i++)rets.push(Math.log(rows[i].close/rows[i-1].close));
  const mean=rets.reduce((a,b)=>a+b,0)/rets.length;
  const variance=rets.reduce((a,b)=>a+(b-mean)**2,0)/rets.length;
  return Math.sqrt(variance)*Math.sqrt(rets.length)*100;
}

function aggregateCandles(candles,bucketSeconds){
  const rows=[...(candles||[])].sort((a,b)=>a.timestamp-b.timestamp);
  const groups=new Map();
  for(const c of rows){
    const bucket=Math.floor(n(c.timestamp)/bucketSeconds)*bucketSeconds;
    const prev=groups.get(bucket);
    if(!prev){
      groups.set(bucket,{timestamp:bucket,open:n(c.open),high:n(c.high),low:n(c.low),close:n(c.close)});
    }else{
      prev.high=Math.max(prev.high,n(c.high));
      prev.low=Math.min(prev.low,n(c.low));
      prev.close=n(c.close);
    }
  }
  return [...groups.values()].sort((a,b)=>a.timestamp-b.timestamp);
}
async function fetchResearchFrame(chainId,symbol,primaryPeriod,primaryLimit,fallbackPeriod,fallbackLimit,bucketSeconds){
  try{
    const direct=await fetchGmxCandles(chainId,symbol,primaryPeriod,primaryLimit);
    return {candles:direct,source:`direct_${primaryPeriod}`,error:null};
  }catch(primaryError){
    try{
      const fine=await fetchGmxCandles(chainId,symbol,fallbackPeriod,fallbackLimit);
      const derived=aggregateCandles(fine,bucketSeconds);
      if(derived.length<60)throw new Error(`derived only ${derived.length} ${primaryPeriod} candles from ${fallbackPeriod}`);
      return {candles:derived,source:`derived_${primaryPeriod}_from_${fallbackPeriod}`,error:String(primaryError?.message||primaryError)};
    }catch(fallbackError){
      throw new Error(
        `${primaryPeriod} direct failed: ${String(primaryError?.message||primaryError)} | `+
        `${fallbackPeriod} fallback failed: ${String(fallbackError?.message||fallbackError)}`
      );
    }
  }
}

function timeframeContext(candles){
  if(!Array.isArray(candles)||candles.length<60)return null;
  const closes=candles.map(c=>c.close),last=closes.at(-1),e20=emaSeries(closes,20).at(-1),e50=emaSeries(closes,50).at(-1),rsi=rsiSeries(closes,14).at(-1);
  const prior=closes[Math.max(0,closes.length-25)];
  return {
    price:round(last,8),
    return_approx_pct:round((last/prior-1)*100,3),
    rsi14:round(n(rsi),2),
    realized_vol_pct:round(volatilityPct(candles),3),
    trend:e20>e50?'up':e20<e50?'down':'flat',
    ema20:round(n(e20),8),
    ema50:round(n(e50),8),
    last_candle_ts:candles.at(-1).timestamp,
  };
}
async function refreshMarketResearch(config,enabled){
  const refresh=Math.max(120,n(config.research_exploration?.refresh_seconds,300));
  const prior=readJson(MARKET_RESEARCH_FILE,null);
  const priorTs=prior?.generated_at?Date.parse(prior.generated_at):0;
  if(prior&&Date.now()-priorTs<refresh*1000&&n(prior.market_count,0)===enabled.length&&n(prior.error_count,0)===0)return prior;

  const markets={},errors={};
  for(const symbol of enabled){
    const symbolErrors=[];
    let shortFrame=null,longFrame=null;

    try{
      shortFrame=await fetchResearchFrame(
        config.chain_id,symbol,
        '15m',500,
        '5m',1500,
        15*60
      );
      if(shortFrame.error)symbolErrors.push(`15m fallback used: ${shortFrame.error}`);
    }catch(e){
      symbolErrors.push(`short horizon unavailable: ${String(e?.message||e)}`);
    }

    try{
      longFrame=await fetchResearchFrame(
        config.chain_id,symbol,
        '4h',250,
        '1h',1000,
        4*60*60
      );
      if(longFrame.error)symbolErrors.push(`4h fallback used: ${longFrame.error}`);
    }catch(e){
      symbolErrors.push(`long horizon unavailable: ${String(e?.message||e)}`);
    }

    if(shortFrame?.candles?.length>=60&&longFrame?.candles?.length>=60){
      markets[symbol]={
        m15:timeframeContext(shortFrame.candles),
        h4:timeframeContext(longFrame.candles),
        sources:{m15:shortFrame.source,h4:longFrame.source},
        notes:symbolErrors,
      };
    }else{
      errors[symbol]=symbolErrors.join(' | ')||'insufficient usable multi-timeframe candle history';
    }
  }

  const out={
    generated_at:iso(),
    source:'GMX Oracle multi-timeframe candles with local fallback aggregation',
    refresh_seconds:refresh,
    markets,
    errors,
    market_count:Object.keys(markets).length,
    error_count:Object.keys(errors).length
  };
  writeJsonAtomic(MARKET_RESEARCH_FILE,out);
  return out;
}
function createResearchState(config,legacySummary=null){
  const e=n(config.starting_equity,10000),ts=Math.floor(Date.now()/1000);
  return{
    version:3,created_at:iso(),starting_equity:e,cash:e,realized_pnl:0,positions:{},wins:0,losses:0,trades:[],
    equity_curve:[{timestamp:ts,equity:round(e,2)}],last_candle_ts:{},last_entry_ts:{},last_decision:{},last_cycle_at:iso(),epoch:1,epoch_started_at:iso(),
    candidate_cursor:{},current_candidate:{},candidate_candles:{},rotation_trade_count:{},rotation_due:{},candidate_stats:{},paused:false,
    archives:legacySummary?[legacySummary]:[],lifetime:{trades:n(legacySummary?.trades,0),pnl:n(legacySummary?.pnl,0),wins:n(legacySummary?.wins,0),losses:n(legacySummary?.losses,0)}
  };
}
function researchPositionSize(equity,config,entry){
  const riskPct=n(config.research_exploration?.risk_per_trade_pct,.10)/100,stopPct=n(config.risk.stop_loss_pct,1.5)/100,maxUsd=n(config.risk.max_position_usd,0);
  const riskBudget=equity*riskPct,byRisk=riskBudget/Math.max(.0001,stopPct),dollarCap=maxUsd>0?maxUsd:Infinity,notional=Math.min(equity*.5,equity*.10,byRisk,dollarCap);
  return{notional,units:notional/entry,risk_budget:riskBudget};
}
function researchEquity(state,latest){
  let eq=n(state.cash,0);
  for(const [symbol,p] of Object.entries(state.positions||{})){
    const mark=n(latest[symbol]?.price,p.mark||p.entry);
    p.mark=mark;p.unrealized_pnl=round(p.direction*p.units*(mark-p.entry),2);eq+=p.unrealized_pnl;
  }
  return eq;
}
function ensureResearchV3(state,config){
  if(!state||state.version!==3)return createResearchState(config);
  state.positions=state.positions||{};state.last_candle_ts=state.last_candle_ts||{};state.last_entry_ts=state.last_entry_ts||{};state.candidate_cursor=state.candidate_cursor||{};state.current_candidate=state.current_candidate||{};
  state.candidate_candles=state.candidate_candles||{};state.rotation_trade_count=state.rotation_trade_count||{};state.rotation_due=state.rotation_due||{};
  state.candidate_stats=state.candidate_stats||{};state.last_decision=state.last_decision||{};state.last_cycle_at=state.last_cycle_at||null;state.paused=!!state.paused;state.archives=Array.isArray(state.archives)?state.archives:[];
  state.lifetime=state.lifetime||{trades:0,pnl:0,wins:0,losses:0};state.epoch=Math.max(1,Math.trunc(n(state.epoch,1)));state.epoch_started_at=state.epoch_started_at||iso();
  return state;
}
function researchCandidatePool(symbol,results,config){
  const size=n(config.research_exploration?.candidate_pool_size,24);
  const rows=results.filter(r=>r.symbol===symbol&&n(r?.base?.trades)>=3);
  const eligible=rows.filter(researchEligible).sort((a,b)=>candidateScore(b)-candidateScore(a));
  if(config.research_exploration?.eligible_only!==false){
    if(eligible.length)return eligible.slice(0,size);
    return rows.filter(r=>researchFallbackEligible(r,config)).sort((a,b)=>candidateScore(b)-candidateScore(a)).slice(0,size);
  }
  return rows.sort((a,b)=>candidateScore(b)-candidateScore(a)).slice(0,size);
}
function pickNextResearchCandidate(symbol,results,state,config,excludeStrategy=null){
  let pool=researchCandidatePool(symbol,results,config);if(!pool.length)return{candidate:null,pool:[]};
  if(excludeStrategy&&pool.length>1){const filtered=pool.filter(r=>r.strategy!==excludeStrategy);if(filtered.length)pool=filtered;}
  const ranked=[...pool].sort((a,b)=>{
    const sa=state.candidate_stats?.[`${symbol}|${a.strategy}`]||{},sb=state.candidate_stats?.[`${symbol}|${b.strategy}`]||{};
    return n(sa.trades)-n(sb.trades)||candidateScore(b)-candidateScore(a);
  });
  return{candidate:ranked[0]||null,pool:researchCandidatePool(symbol,results,config)};
}
function researchCandidateFor(symbol,results,state,config){
  const pool=researchCandidatePool(symbol,results,config);if(!pool.length)return{candidate:null,pool:[]};
  state.current_candidate=state.current_candidate||{};
  const current=pool.find(r=>r.strategy===state.current_candidate[symbol]);
  if(current)return{candidate:current,pool};
  const picked=pickNextResearchCandidate(symbol,results,state,config);
  if(picked.candidate)state.current_candidate[symbol]=picked.candidate.strategy;
  return{candidate:picked.candidate,pool};
}
function advanceResearchCandidate(state,symbol,results,config,reason,ts){
  state.current_candidate=state.current_candidate||{};
  const old=state.current_candidate[symbol]||null;
  const picked=pickNextResearchCandidate(symbol,results,state,config,old);
  if(!picked.candidate)return;
  state.current_candidate[symbol]=picked.candidate.strategy;state.candidate_candles[symbol]=0;state.rotation_trade_count[symbol]=0;state.rotation_due[symbol]=false;
  state.last_rotation=state.last_rotation||{};state.last_rotation[symbol]={at:new Date((ts||Math.floor(Date.now()/1000))*1000).toISOString(),reason,from:old,to:picked.candidate.strategy};
}
function closeResearchPosition(state,symbol,rawExit,ts,cost,reason,config){
  const p=state.positions[symbol];if(!p)return;
  const calc=closeCalc(p,rawExit,ts,cost);
  state.cash+=calc.gross-calc.exit_fee-calc.holding_cost;state.realized_pnl+=calc.net;
  state.trades.push({symbol,side:p.direction>0?'long':'short',entry:round(p.entry,4),exit:round(calc.exit,4),pnl:round(calc.net,2),opened_at:new Date(p.opened_ts*1000).toISOString(),closed_at:new Date(ts*1000).toISOString(),reason,strategy:p.strategy,source:'research_shadow'});
  if(calc.net>0)state.wins++;else state.losses++;
  const key=`${symbol}|${p.strategy}`,stats=state.candidate_stats[key]||{symbol,strategy:p.strategy,trades:0,wins:0,losses:0,pnl:0};
  stats.trades++;stats.pnl=round(n(stats.pnl)+calc.net,2);if(calc.net>0)stats.wins++;else stats.losses++;stats.win_rate=round(stats.wins/Math.max(1,stats.trades)*100,2);stats.last_closed_at=new Date(ts*1000).toISOString();state.candidate_stats[key]=stats;
  state.lifetime.trades=n(state.lifetime.trades)+1;state.lifetime.pnl=round(n(state.lifetime.pnl)+calc.net,2);if(calc.net>0)state.lifetime.wins=n(state.lifetime.wins)+1;else state.lifetime.losses=n(state.lifetime.losses)+1;
  state.rotation_trade_count[symbol]=n(state.rotation_trade_count[symbol])+1;
  const loserMin=n(config.research_exploration?.loser_rotation_trades,4);
  if(stats.trades>=loserMin&&n(stats.wins,0)===0&&n(stats.pnl,0)<0)state.rotation_due[symbol]=true;
  if(state.rotation_trade_count[symbol]>=n(config.research_exploration?.trades_per_candidate,6))state.rotation_due[symbol]=true;
  delete state.positions[symbol];
}
function maybeRollResearchEpoch(state,latest,config){
  let eq=researchEquity(state,latest),start=Math.max(1,n(state.starting_equity,config.starting_equity)),dd=Math.max(0,(start-eq)/start*100);
  const maxDd=n(config.research_exploration?.max_epoch_drawdown_pct,10),maxTrades=n(config.research_exploration?.max_epoch_trades,500);
  if(dd<maxDd&&(state.trades||[]).length<maxTrades)return state;
  const cost=costs(config,1),guardReason=dd>=maxDd?'research_drawdown_guard':'research_trade_budget';
  for(const symbol of Object.keys(state.positions||{})){
    const p=state.positions[symbol],raw=n(latest[symbol]?.price,p?.mark||p?.entry),ts=n(latest[symbol]?.timestamp,Math.floor(Date.now()/1000));
    if(raw>0)closeResearchPosition(state,symbol,raw,ts,cost,guardReason,config);
  }
  eq=researchEquity(state,latest);dd=Math.max(0,(start-eq)/start*100);
  const summary={epoch:state.epoch,started_at:state.epoch_started_at,closed_at:iso(),ending_equity:round(eq,2),pnl:round(eq-start,2),drawdown_pct:round(dd,3),trades:(state.trades||[]).length,wins:n(state.wins),losses:n(state.losses),reason:guardReason};
  const preserved={current:{...(state.current_candidate||{})},stats:{...(state.candidate_stats||{})},archives:[...(state.archives||[]),summary].slice(-20),lifetime:{...(state.lifetime||{})},epoch:n(state.epoch,1)+1};
  const next=createResearchState(config);next.epoch=preserved.epoch;next.epoch_started_at=iso();next.current_candidate=preserved.current;next.candidate_stats=preserved.stats;next.archives=preserved.archives;next.lifetime=preserved.lifetime;
  return next;
}

function researchSignalName(v){return v>0?'long':v<0?'short':'flat';}
function recordResearchDecision(state,symbol,candidate,signal,candle,reason,extra={}){
  state.last_decision=state.last_decision||{};
  state.last_decision[symbol]={
    at:new Date((candle?.timestamp||Math.floor(Date.now()/1000))*1000).toISOString(),
    candle_ts:candle?.timestamp||null,
    strategy:candidate?.strategy||null,
    signal:researchSignalName(signal||0),
    reason,
    ...extra
  };
}
function researchDataWindow(candlesBySymbol){
  let start=Infinity,end=0,count=0;
  for(const rows of Object.values(candlesBySymbol||{})){
    if(!Array.isArray(rows)||!rows.length)continue;
    const a=n(rows[0]?.timestamp,0),b=n(rows.at(-1)?.timestamp,0);
    if(a>0)start=Math.min(start,a);if(b>0)end=Math.max(end,b);count+=rows.length;
  }
  return{
    start_at:Number.isFinite(start)?new Date(start*1000).toISOString():null,
    end_at:end?new Date(end*1000).toISOString():null,
    candles_loaded:count
  };
}
function forwardTestDetails(results,candlesBySymbol,config){
  return (results||[]).filter(r=>researchForwardEligible(r,config)).sort((a,b)=>candidateScore(b)-candidateScore(a)).slice(0,12).map(r=>{
    const candles=candlesBySymbol?.[r.symbol]||[],idx=candles.length-2,c=candles[idx],raw=c?strategySignal(r.strategy,candles,idx):0;
    return{
      symbol:r.symbol,strategy:r.strategy,family:r.family,
      signal:researchSignalName(raw),candle_ts:c?.timestamp||null,
      base_return_pct:round(n(r?.base?.return_pct),3),stress_return_pct:round(n(r?.stress?.return_pct),3),
      profit_factor:round(n(r?.base?.profit_factor),3),win_rate:round(n(r?.base?.win_rate),2),
      trades:n(r?.base?.trades),max_drawdown:round(n(r?.base?.max_drawdown),3),
      strict_positive:researchEligible(r),validation_pass:r?.validation?.pass===true,context_score:round(n(r?.context_score),1),regime:r?.regime||null,hypothesis:r?.hypothesis||null
    };
  });
}

function updateResearchPaper(state,candlesBySymbol,latest,config,results=[]){
  if(config.research_exploration?.paper_lab_enabled===false)return state;
  state=ensureResearchV3(state,config);state.paused=false;state.last_cycle_at=iso();
  const continuousResearch=config.research_exploration?.continuous_market_research_enabled!==false;
  const cost=costs(config,1),enabled=Object.entries(config.market_settings).filter(([,v])=>v.enabled).map(([s])=>s);
  const newestTs=Math.max(...enabled.map(sym=>candlesBySymbol[sym]?.at(-1)?.timestamp||0),0);
  for(const symbol of enabled){
    const candles=candlesBySymbol[symbol],idx=(candles?.length||0)-2,c=candles?.[idx];
    if(!c)continue;
    if(state.last_candle_ts[symbol]>=c.timestamp){
      const existing=state.positions?.[symbol];
      const current=results.find(r=>r.symbol===symbol&&r.strategy===state.current_candidate?.[symbol])||null;
      const sig=current?strategySignal(current.strategy,candles,idx):0;
      recordResearchDecision(state,symbol,current,sig,c,existing?'position_open':'waiting_next_closed_candle',{position_open:!!existing});
      continue;
    }
    let {candidate,pool}=researchCandidateFor(symbol,results,state,config);
    if(!candidate){
      recordResearchDecision(state,symbol,null,0,c,'no_forward_candidate');
      state.last_candle_ts[symbol]=c.timestamp;continue;
    }
    state.current_candidate[symbol]=candidate.strategy;
    if(continuousResearch){
      state.candidate_candles[symbol]=n(state.candidate_candles[symbol])+1;
      if(state.candidate_candles[symbol]>=n(config.research_exploration?.rotation_candles,90))state.rotation_due[symbol]=true;
    }
    let p=state.positions[symbol],exited=false,exitReason=null;
    if(p){
      const activeSignal=strategySignal(p.strategy,candles,idx);
      let ex=intrabarExit(p,c);
      if(!ex&&continuousResearch&&state.rotation_due[symbol])ex={reason:'research_candidate_rotation',raw:c.close};
      if(!ex&&shouldSignalExit(p.direction,activeSignal))ex={reason:'research_opposite_signal_exit',raw:c.close};
      if(!ex&&((c.timestamp-n(p.opened_ts))/periodSeconds(config.timeframe))>=n(config.risk.max_holding_bars,72))ex={reason:'research_max_holding_bars',raw:c.close};
      if(ex){closeResearchPosition(state,symbol,ex.raw,latest[symbol]?.timestamp||c.timestamp,cost,ex.reason,config);exited=true;exitReason=ex.reason;p=null;}
    }
    if(continuousResearch&&!state.positions[symbol]&&state.rotation_due[symbol]){
      advanceResearchCandidate(state,symbol,results,config,'rotation_budget',c.timestamp);
      ({candidate,pool}=researchCandidateFor(symbol,results,state,config));
    }
    const signal=candidate?strategySignal(candidate.strategy,candles,idx):0;
    const eq=researchEquity(state,latest),openCount=Object.keys(state.positions).length,entryCooldown=n(config.research_exploration?.entry_cooldown_bars,config.paper?.entry_cooldown_bars||0),barsSinceEntry=(c.timestamp-n(state.last_entry_ts[symbol],0))/periodSeconds(config.timeframe),entryReady=!state.last_entry_ts[symbol]||barsSinceEntry>=entryCooldown;
    const maxOpen=n(config.research_exploration?.max_concurrent_positions,3);
    if(candidate&&entryReady&&!state.positions[symbol]&&!exited&&signal!==0&&openCount<maxOpen){
      const entry=entryFill(c.close,signal,cost),sz=researchPositionSize(eq,config,entry),st=stopTarget(entry,signal,config),entryFee=sz.notional*cost.fee;
      state.cash-=entryFee;
      state.positions[symbol]={symbol,direction:signal,side:signal>0?'long':'short',entry:round(entry,6),units:sz.units,notional:round(sz.notional,2),entry_fee:entryFee,stop:round(st.stop,6),target:round(st.target,6),opened_ts:c.timestamp,mark:c.close,unrealized_pnl:0,strategy:candidate.strategy,source:'research_shadow'};state.last_entry_ts[symbol]=c.timestamp;
      recordResearchDecision(state,symbol,candidate,signal,c,signal>0?'opened_long':'opened_short',{notional:round(sz.notional,2),pool_size:pool.length});
    }else{
      let reason='waiting_for_strategy_signal';
      if(state.positions[symbol])reason='position_open';
      else if(exited)reason=exitReason||'exited_this_candle';
      else if(!entryReady)reason='entry_cooldown';
      else if(signal===0)reason='waiting_for_strategy_signal';
      else if(openCount>=maxOpen)reason='max_positions_reached';
      recordResearchDecision(state,symbol,candidate,signal,c,reason,{pool_size:pool.length,entry_ready:entryReady,open_positions:openCount});
    }
    state.last_candle_ts[symbol]=c.timestamp;
  }
  const eq=researchEquity(state,latest);
  state.equity_curve.push({timestamp:Math.floor(Date.now()/1000),equity:round(eq,2)});
  state.equity_curve=state.equity_curve.slice(-2400);state.trades=state.trades.slice(-1500);
  return maybeRollResearchEpoch(state,latest,config);
}
function pauseResearchPaper(state,latest,config){
  state=ensureResearchV3(state,config);state.paused=true;state.last_cycle_at=iso();
  const cost=costs(config,1);
  for(const symbol of Object.keys(state.positions||{})){
    const p=state.positions[symbol],raw=n(latest[symbol]?.price,p?.mark||p?.entry),ts=n(latest[symbol]?.timestamp,Math.floor(Date.now()/1000));
    if(raw>0)closeResearchPosition(state,symbol,raw,ts,cost,'owner_paper_lab_pause',config);
  }
  const eq=researchEquity(state,latest),ts=Math.max(...Object.values(latest||{}).map(x=>n(x?.timestamp,0)),Math.floor(Date.now()/1000));
  state.equity_curve.push({timestamp:ts,equity:round(eq,2)});state.equity_curve=state.equity_curve.slice(-2400);
  return state;
}
function researchPaperTelemetry(state,latest,config){
  const eq=researchEquity(state,latest),start=Math.max(1,n(state.starting_equity,10000)),trades=state.trades||[],wins=state.wins||0;
  const curve=(state.equity_curve||[]).slice(-2400);
  const currentCandidates={};
  for(const symbol of new Set([...Object.keys(state.current_candidate||{}),...Object.keys(state.last_rotation||{})]))currentCandidates[symbol]={strategy:state.current_candidate?.[symbol]||null,last_rotation:state.last_rotation?.[symbol]||null};
  const stats=Object.values(state.candidate_stats||{}).sort((a,b)=>n(b.pnl)-n(a.pnl)).slice(0,30);
  return{
    mode:'SIMULATED RESEARCH SHADOW',enabled:config?.research_exploration?.paper_lab_enabled!==false&&!state.paused,exploration_mode:'rotating_challenger_forward_tests',active_epoch:n(state.epoch,1),epoch_started_at:state.epoch_started_at||state.created_at,
    starting_equity:round(start,2),equity:round(eq,2),pnl:round(eq-start,2),pnl_pct:round((eq/start-1)*100,3),trades:trades.length,win_rate:trades.length?round(wins/trades.length*100,2):0,
    max_drawdown:round(maxDrawdown(curve.map(x=>n(x.equity))),3),equity_curve:curve,last_point_at:curve.length?curve.at(-1).timestamp:null,
    open_positions:Object.values(state.positions||{}).map(p=>({symbol:p.symbol,side:p.side,strategy:p.strategy,entry:p.entry,mark:p.mark,unrealized_pnl:p.unrealized_pnl,source:'research_shadow'})),
    recent_trades:trades.slice(-50),candidate_forward_stats:stats,current_candidate_rotation:currentCandidates,last_decisions:state.last_decision||{},last_cycle_at:state.last_cycle_at||null,archived_epochs:(state.archives||[]).slice(-10),lifetime:state.lifetime||{},
    note:'Research-only simulated challenger book. It prefers positive near-misses; if none exist, the owner-enabled paper lab may forward-test the closest controlled near-miss inside tiny simulated risk. Validation remains separate and live orders remain impossible.'
  };
}

function validatedPromotionSignature(results){
  const bySymbol=new Map();
  for(const r of results||[]){
    if(r?.validation?.pass!==true)continue;
    const prev=bySymbol.get(r.symbol);
    if(!prev||candidateScore(r)>candidateScore(prev))bySymbol.set(r.symbol,r);
  }
  return [...bySymbol.entries()]
    .sort((a,b)=>a[0].localeCompare(b[0]))
    .map(([symbol,r])=>`${symbol}:${r.strategy}`)
    .join('|');
}
function archiveFailedMainPaper(state,signature){
  fs.mkdirSync(PAPER_ARCHIVE_DIR,{recursive:true});
  const stamp=iso().replaceAll(':','-').replaceAll('.','-');
  const file=path.join(PAPER_ARCHIVE_DIR,`quant_paper_failed_${stamp}.json`);
  writeJsonAtomic(file,{
    ...state,
    archived_at:iso(),
    archive_reason:'new_validation_passing_promotion_available',
    next_promotion_signature:signature
  });
  return file;
}
function maybeAutoRecoverMainPaper(state,config,results=[]){
  const signature=validatedPromotionSignature(results);
  if(!signature)return{state,restarted:false,reason:'no_validation_passing_strategy'};
  if(config.paper.emergency_stop||config.paper.auto_trading_enabled===false)return{state,restarted:false,reason:'owner_gate'};
  if(!state.halted){
    if(!state.promotion_signature)state.promotion_signature=signature;
    state.observed_promotion_signature=signature;
    return{state,restarted:false,reason:null};
  }
  if(state.halt_reason!=='poor_forward_performance')return{state,restarted:false,reason:state.halt_reason||'risk_halt'};
  if(state.promotion_signature&&state.promotion_signature===signature){
    return{state,restarted:false,reason:'same_failed_promotion_set'};
  }
  const archive=archiveFailedMainPaper(state,signature);
  const next=createPaperState(config);
  next.promotion_signature=signature;
  next.observed_promotion_signature=signature;
  next.last_auto_recovery={at:iso(),reason:'new_validation_passing_promotion_available',archive};
  return{state:next,restarted:true,reason:null};
}

function updatePaper(state,candlesBySymbol,latest,config,results=[]){
  const cost=costs(config,1);state.positions=state.positions||{};state.last_candle_ts=state.last_candle_ts||{};state.last_entry_ts=state.last_entry_ts||{};
  const validated=new Map(results.map(r=>[`${r.symbol}|${r.strategy}`,r.validation?.pass===true]));
  const enabled=Object.entries(config.market_settings).filter(([,v])=>v.enabled).map(([sym])=>sym);
  const newestTs=Math.max(...enabled.map(sym=>candlesBySymbol[sym]?.at(-1)?.timestamp||0),0);
  const dayKey=new Date(newestTs*1000||Date.now()).toISOString().slice(0,10);
  let eq=stateEquity(state,latest);
  if(dayKey!==state.day_key){state.day_key=dayKey;state.day_start_equity=eq;if(state.halt_reason!=='poor_forward_performance'&&state.halt_reason!=='owner_emergency_stop'){state.halted=false;state.halt_reason=null;}}
  const dailyLoss=(state.day_start_equity-eq)/Math.max(1,state.day_start_equity)*100;
  const dd=(state.peak_equity-eq)/Math.max(1,state.peak_equity)*100;
  if(config.paper.emergency_stop){state.halted=true;state.halt_reason='owner_emergency_stop';}
  else if(state.halt_reason==='poor_forward_performance'||poorForwardPerformance(state,eq)){state.halted=true;state.halt_reason='poor_forward_performance';}
  else if(dailyLoss>=n(config.risk.max_daily_loss_pct,2)){state.halted=true;state.halt_reason='daily_loss_limit';}
  else if(dd>=n(config.risk.max_drawdown_pct,8)){state.halted=true;state.halt_reason='max_drawdown_limit';}
  if(state.halted){for(const symbol of Object.keys(state.positions)){const c=candlesBySymbol[symbol]?.at(-2),mark=n(latest[symbol]?.price,c?.close);if(mark&&c)closePaperPosition(state,symbol,mark,latest[symbol]?.timestamp||Math.floor(Date.now()/1000),cost,state.halt_reason);}}
  for(const symbol of enabled){
    const candles=candlesBySymbol[symbol],signalIndex=(candles?.length||0)-2,c=candles?.[signalIndex];if(!c||state.last_candle_ts[symbol]>=c.timestamp)continue;
    const marketCfg=config.market_settings[symbol]||{};
    const configuredStrategy=marketCfg.paper_strategy||'trend_momentum';
    const strategy=adaptiveStrategy(symbol,configuredStrategy,results,config.paper.adaptive_strategy_selection!==false);
    const signal=strategySignal(strategy,candles,signalIndex);
    const p=state.positions[symbol];let exitedThisCandle=false;
    if(p){
      // Manual positions must never replay the whole strategy candle after entry.
      // Their stop/target checks use the fresh GMX market mark only.
      let ex=p.source==='manual'?manualMarkExit(p,n(latest[symbol]?.price,c.close)):intrabarExit(p,c);
      if(!ex&&p.source!=='manual'&&shouldSignalExit(p.direction,signal))ex={reason:'opposite_signal_exit',raw:c.close};
      if(!ex&&p.source!=='manual'&&((c.timestamp-n(p.opened_ts))/periodSeconds(config.timeframe))>=n(config.risk.max_holding_bars,72))ex={reason:'max_holding_bars',raw:c.close};
      if(ex){closePaperPosition(state,symbol,ex.raw,latest[symbol]?.timestamp||c.timestamp,cost,ex.reason);exitedThisCandle=true;}
    }
    eq=stateEquity(state,latest);
    const openCount=Object.keys(state.positions).length;
    const autoAllowed=config.paper.auto_trading_enabled!==false&&marketCfg.auto_trade_enabled!==false&&validated.get(`${symbol}|${strategy}`)===true;
    const entryCooldown=n(config.paper?.entry_cooldown_bars,0),barsSinceEntry=(c.timestamp-n(state.last_entry_ts[symbol],0))/periodSeconds(config.timeframe),entryReady=!state.last_entry_ts[symbol]||barsSinceEntry>=entryCooldown;
    if(autoAllowed&&entryReady&&!state.positions[symbol]&&!exitedThisCandle&&!state.halted&&signal!==0&&openCount<n(config.risk.max_concurrent_positions,2)){
      const entry=entryFill(c.close,signal,cost),sz=positionSize(eq,config,entry),st=stopTarget(entry,signal,config),entryFee=sz.notional*cost.fee;
      state.cash-=entryFee;
      state.positions[symbol]={symbol,direction:signal,side:signal>0?'long':'short',entry:round(entry,6),units:sz.units,notional:round(sz.notional,2),margin_usd:round(sz.notional/Math.max(.1,n(config.risk.max_notional_leverage,1.5)),2),leverage:n(config.risk.max_notional_leverage,1.5),entry_fee:entryFee,stop:round(st.stop,6),target:round(st.target,6),opened_ts:c.timestamp,mark:c.close,unrealized_pnl:0,strategy,source:'auto'};state.last_entry_ts[symbol]=c.timestamp;
    }
    state.last_candle_ts[symbol]=c.timestamp;
  }
  eq=stateEquity(state,latest);state.peak_equity=Math.max(state.peak_equity,eq);state.equity_curve.push({timestamp:newestTs||Math.floor(Date.now()/1000),equity:round(eq,2)});state.equity_curve=state.equity_curve.slice(-2000);state.trades=state.trades.slice(-500);return state;
}

async function manualPaperAction(payload){
  const config=loadConfig();
  const action=String(payload?.action||'').trim().toLowerCase();
  const symbol=String(payload?.symbol||'').toUpperCase();
  const allowed=SUPPORTED_RESEARCH_MARKETS.includes(symbol);
  let state=readJson(STATE_FILE,null);if(!state||state.version!==3)state=createPaperState(config);state.positions=state.positions||{};
  const enabled=Object.entries(config.market_settings).filter(([,v])=>v.enabled).map(([sym])=>sym);
  const latest={};for(const sym of new Set([...enabled,...Object.keys(state.positions),...(allowed?[symbol]:[])])){try{latest[sym]=await fetchLatestPrice(config.chain_id,sym);}catch{}}
  const cost=costs(config,1);
  const nowTs=Math.max(1,...Object.values(latest).map(x=>x?.timestamp||0),Math.floor(Date.now()/1000));
  if(action==='close_all'){
    for(const sym of Object.keys(state.positions)){const px=latest[sym]?.price||state.positions[sym].mark;if(px)closePaperPosition(state,sym,px,nowTs,cost,'manual_close_all');}
  }else if(action==='close'){
    if(!allowed)throw new Error('Unsupported market');
    const p=state.positions[symbol];if(!p)throw new Error(`No open paper position for ${symbol}`);
    const px=latest[symbol]?.price||p.mark;if(!px)throw new Error(`No current GMX mark for ${symbol}`);
    closePaperPosition(state,symbol,px,latest[symbol]?.timestamp||nowTs,cost,'manual_close');
  }else if(action==='open'){
    if(!allowed)throw new Error('Unsupported market');
    if(config.paper.emergency_stop||state.halted)throw new Error(`Paper trading is halted${state.halt_reason?`: ${state.halt_reason}`:''}`);
    if(state.positions[symbol])throw new Error(`${symbol} already has an open paper position. Close that position before opening another ${symbol} trade.`);
    // The configured simultaneous-position cap governs Auto Bot entries.
    // Owner manual paper trades may use the remaining supported markets, while
    // still obeying per-trade risk and per-market allocation limits.
    if(Object.keys(state.positions).length>=SUPPORTED_RESEARCH_MARKETS.length)throw new Error('All supported markets already have open paper positions');
    const side=String(payload?.side||'').toLowerCase();if(!['long','short'].includes(side))throw new Error('Side must be long or short');
    const direction=side==='long'?1:-1;
    const mark=n(latest[symbol]?.price,0);if(mark<=0)throw new Error(`No current GMX mark for ${symbol}`);
    const equity=stateEquity(state,latest);
    const leverage=clamp(n(payload?.leverage,1),1,n(config.risk.max_notional_leverage,1.5));
    const stopPct=clamp(n(payload?.stop_loss_pct,config.risk.stop_loss_pct),.25,15);
    const takePct=clamp(n(payload?.take_profit_pct,config.risk.take_profit_pct),.25,40);
    const margin=clamp(n(payload?.margin_usd,0),1,Math.max(1,equity));
    const requestedNotional=margin*leverage;
    const riskBudget=equity*n(config.risk.max_risk_per_trade_pct,.5)/100;
    const maxByRisk=riskBudget/Math.max(.0001,stopPct/100);
    const maxByAllocation=equity*n(config.risk.max_market_allocation_pct,35)/100;
    const configuredDollarCap=n(config.risk.max_position_usd,0),maxDollarCap=configuredDollarCap>0?configuredDollarCap:Infinity;
    const maxNotional=Math.min(equity*n(config.risk.max_notional_leverage,1.5),maxByRisk,maxByAllocation,maxDollarCap);
    if(requestedNotional>maxNotional+0.01){const maxMargin=maxNotional/leverage;throw new Error(`Trade exceeds paper risk limits. At ${leverage.toFixed(2)}x and ${stopPct.toFixed(2)}% stop, max margin is about $${maxMargin.toFixed(2)}.`);}
    const entry=entryFill(mark,direction,cost),notional=requestedNotional,units=notional/entry,entryFee=notional*cost.fee;
    const stop=entry*(1-direction*stopPct/100),target=entry*(1+direction*takePct/100);
    state.cash-=entryFee;
    const requestedSource=String(payload?.source||'manual').toLowerCase()==='copy'?'copy':'manual';
    const requestedStrategy=requestedSource==='copy'?String(payload?.strategy||'copy:verified-gmx-trader').slice(0,240):'manual';
    state.positions[symbol]={symbol,direction,side,entry:round(entry,6),units,notional:round(notional,2),margin_usd:round(margin,2),leverage:round(leverage,2),entry_fee:entryFee,stop:round(stop,6),target:round(target,6),opened_ts:latest[symbol]?.timestamp||nowTs,mark,unrealized_pnl:0,strategy:requestedStrategy,source:requestedSource};
  }else throw new Error('Unknown manual paper action');
  const eq=stateEquity(state,latest);state.peak_equity=Math.max(state.peak_equity||eq,eq);state.equity_curve=state.equity_curve||[];state.equity_curve.push({timestamp:nowTs,equity:round(eq,2)});state.equity_curve=state.equity_curve.slice(-2000);writeJsonAtomic(STATE_FILE,state);
  // Refresh telemetry without letting the Auto Bot or the current strategy
  // candle mutate the just-submitted manual order in the same request.
  const status=await cycle({backtestOnly:true});
  return {ok:true,action,symbol:symbol||null,equity:status.equity,positions:status.positions};
}

function mathSelfTest(){
  const cfg=normalizeConfig(DEFAULT_CONFIG),cost={fee:0,slip:0,impact:0,holding:0};
  const p={direction:1,entry:100,units:10,notional:1000,entry_fee:0,opened_ts:0,stop:98.5,target:103};
  const c=closeCalc(p,102,3600,cost),both=intrabarExit(p,{low:98,high:104}),size=positionSize(10000,cfg,100),manualRisk=(1000*2*.015);
  const manualHold=manualMarkExit({...p,source:'manual'},100),manualStop=manualMarkExit({...p,source:'manual'},98.4);
  const families=new Set(STRATEGY_CANDIDATES.map(x=>x.family));
  const legacy=normalizeConfig({...DEFAULT_CONFIG,research_costs:{position_fee_bps_per_side:6,slippage_bps_per_side:5,impact_bps_per_side:20,holding_cost_bps_per_day:5}});
  const synthetic1m=Array.from({length:80},(_,i)=>({timestamp:1700000000+i*60,open:100,high:100.2,low:99.8,close:100}));
  const mr=resolveCandidate('mean_reversion_15'),scaled=scaledCandidateParams(mr,synthetic1m);
  const near={base:{trades:20,return_pct:-.05,profit_factor:1.2,win_rate:50,max_drawdown:3},stress:{return_pct:-.2},walk_forward:{total_windows:6,positive_windows:1}};
  const tourRows=[{symbol:'BTC/USD',strategy:'mean_reversion_15',family:'mean_reversion',base:{trades:20,return_pct:-1,pnl:-10,profit_factor:.9,win_rate:45,max_drawdown:5},stress:{return_pct:-2,pnl:-20},walk_forward:{total_windows:6,positive_windows:2},validation:{pass:false,walk_forward_positive_pct:33},context_score:50},{symbol:'ETH/USD',strategy:'atr_breakout_14_15',family:'atr_breakout',base:{trades:20,return_pct:.5,pnl:5,profit_factor:1.2,win_rate:50,max_drawdown:4},stress:{return_pct:-.5,pnl:-5},walk_forward:{total_windows:6,positive_windows:3},validation:{pass:false,walk_forward_positive_pct:50},context_score:70}];
  const checks={
    long_pnl_exact:Math.abs(c.net-20)<1e-9,
    conservative_same_candle_stop:both?.reason==='stop_and_target_same_candle_conservative_stop',
    zero_signal_does_not_force_exit:shouldSignalExit(1,0)===false,
    opposite_signal_does_exit:shouldSignalExit(1,-1)===true,
    expanded_candidate_universe:STRATEGY_CANDIDATES.length===32,
    eight_strategy_families:['scalp_trend','trend_momentum','mean_reversion','donchian_breakout','bollinger_reversion','pullback_trend','atr_breakout','rsi_reclaim'].every(x=>families.has(x)),
    manual_does_not_replay_old_candle:manualHold===null,
    manual_mark_stop:manualStop?.reason==='stop_loss',
    risk_size_respects_leverage:size.notional<=15000.0001,
    risk_size_respects_allocation:size.notional<=3500.0001,
    manual_risk_math:Math.abs(manualRisk-30)<1e-9,
    extended_timeframes:VALID_PERIODS.has('30m')&&VALID_PERIODS.has('2h')&&periodSeconds('30m')===1800&&periodSeconds('2h')===7200,
    max_position_cap:positionSize(10000,normalizeConfig({...DEFAULT_CONFIG,risk:{...DEFAULT_CONFIG.risk,max_position_usd:250}}),100).notional<=250.0001,
    entry_cooldown_normalized:normalizeConfig({...DEFAULT_CONFIG,paper:{...DEFAULT_CONFIG.paper,entry_cooldown_bars:4}}).paper.entry_cooldown_bars===4,
    gmx_cost_migration:legacy.research_costs.slippage_bps_per_side===1&&legacy.research_costs.impact_bps_per_side===2,
    entry_impact_not_double_charged:Math.abs(entryFill(100,1,{slip:.001,impact:.002})-100.1)<1e-9,
    low_tf_mean_reversion_scaled:scaled.deviation<mr.params.deviation&&scaled.deviation>=.0015,
    fallback_near_miss_forward_test:researchFallbackEligible(near,cfg)===true,
    tournament_parallel_books:tournamentCandidateRows(tourRows,{'BTC/USD':synthetic1m,'ETH/USD':synthetic1m},cfg).length===2,
    tournament_live_hard_separate:cfg.research_exploration.tournament_enabled===true&&cfg.live_execution.enabled===false,
    tournament_aggregate_curve:(()=>{const st={version:1,slots:{'BTC/USD|a':{starting_equity:100,equity_curve:[{timestamp:1,equity:100},{timestamp:2,equity:102}]},'ETH/USD|b':{starting_equity:100,equity_curve:[{timestamp:1,equity:100},{timestamp:2,equity:99}]}},recent_trades:[]},sel=[{symbol:'BTC/USD',strategy:'a'},{symbol:'ETH/USD',strategy:'b'}],curve=tournamentAggregateCurve(st,sel,cfg);return curve.length===2&&curve.at(-1).equity===201;})(),
    tournament_trade_display_details:(()=>{const z=tournamentPositionSize(1250,normalizeConfig({...DEFAULT_CONFIG,risk:{...DEFAULT_CONFIG.risk,max_notional_leverage:5}}),100);return z.notional>0&&z.leverage===5&&Math.abs(z.margin-z.notional/5)<1e-9;})(),
    paper_lab_default_on:cfg.research_exploration.paper_lab_enabled===true,
    continuous_research_default_on:cfg.research_exploration.continuous_market_research_enabled===true,
    research_and_bot_controls_independent:(()=>{const z=normalizeConfig({...DEFAULT_CONFIG,paper:{...DEFAULT_CONFIG.paper,auto_trading_enabled:true},research_exploration:{...DEFAULT_CONFIG.research_exploration,continuous_market_research_enabled:false,paper_lab_enabled:true}});return z.research_exploration.continuous_market_research_enabled===false&&paperTradingEnabled(z)===true;})(),
    paper_bot_gate_combines_main_and_lab:(()=>{const z=normalizeConfig({...DEFAULT_CONFIG,research_exploration:{...DEFAULT_CONFIG.research_exploration,paper_lab_enabled:false}});return paperTradingEnabled(z)===false;})(),
    history_floor_1m:normalizeConfig({...DEFAULT_CONFIG,timeframe:'1m',history_limit:5000}).history_limit===10000,
    paper_lab_signal_labels:researchSignalName(1)==='long'&&researchSignalName(-1)==='short'&&researchSignalName(0)==='flat',
    paper_lab_data_window:researchDataWindow({A:[{timestamp:100},{timestamp:200}],B:[{timestamp:150},{timestamp:250}]}).end_at===new Date(250000).toISOString(),
    multi_source_consensus:consensusFromSources({a:{price:100},b:{price:100.1},c:{price:99.9}}).source_count===3&&consensusFromSources({a:{price:100},b:{price:100.1},c:{price:99.9}}).confidence==='high',
    regime_classification:classifyRegime({m15:{trend:'up',realized_vol_pct:.8},h4:{trend:'up'}},{cross_venue_flow:.2}).regime==='trend',
    hypothesis_fit:familyRegimeFit('mean_reversion','range')>familyRegimeFit('trend_momentum','range'),
    live_hard_locked:cfg.live_execution.enabled===false&&cfg.live_execution.signing_enabled===false,
    valid_stop_target:p.stop<p.entry&&p.target>p.entry
  };
  return{pass:Object.values(checks).every(Boolean),checks};
}

function liveSignals(config,candlesBySymbol,results=[]){const validated=new Map(results.map(r=>[`${r.symbol}|${r.strategy}`,!!r.validation?.pass]));const rows=[];for(const [symbol,row] of Object.entries(config.market_settings||{})){if(row?.enabled===false||row?.auto_trade_enabled===false)continue;const candles=candlesBySymbol[symbol];if(!Array.isArray(candles)||candles.length<61)continue;const strategy=row.paper_strategy||'trend_momentum',idx=candles.length-2,raw=strategySignal(strategy,candles,idx);rows.push({symbol,strategy,signal:raw>0?'long':raw<0?'short':'flat',candle_ts:candles[idx].timestamp,timeframe:config.timeframe,validation_pass:validated.get(`${symbol}|${strategy}`)===true});}return rows;}


function researchSummary(status){
  const rows=Array.isArray(status?.backtests)?status.backtests:[];
  const ranked=[...rows].sort((a,b)=>
    (n(b?.status==='PASS'?2:b?.status==='SHADOW_ELIGIBLE'?1:0)-n(a?.status==='PASS'?2:a?.status==='SHADOW_ELIGIBLE'?1:0)) ||
    (n(b?.stress_return_pct)-n(a?.stress_return_pct)) ||
    (n(b?.profit_factor)-n(a?.profit_factor)) ||
    (n(b?.return_pct)-n(a?.return_pct)) ||
    (n(b?.walk_forward_positive_pct)-n(a?.walk_forward_positive_pct))
  );
  const viable=ranked.filter(r=>r.status==='PASS'||r.status==='SHADOW_ELIGIBLE');
  return {
    generated_at:status?.generated_at||iso(),
    engine_version:status?.engine?.version||VERSION,
    candidate_pass_count:n(status?.validation?.candidate_pass_count,0),
    candidate_total:n(status?.validation?.candidate_total,rows.length),
    research_eligible_count:n(status?.research_lab?.eligible_shadow_candidates,viable.length),
    paper_pnl:n(status?.total_pnl,0),
    paper_win_rate:n(status?.win_rate,0),
    paper_drawdown:n(status?.max_drawdown,0),
    halted:!!status?.risk?.halted,
    halt_reason:status?.risk?.halt_reason||null,
    research_shadow_trades:n(status?.research_paper?.trades,0),
    research_shadow_pnl:n(status?.research_paper?.pnl,0),
    market_research_at:status?.market_research?.generated_at||null,
    multi_source_at:status?.market_intelligence?.generated_at||null,
    research_pipeline:status?.research_pipeline||null,
    family_progress:status?.strategy_family_progress||{},
    top_candidates:viable.slice(0,8),
    least_bad_rejected:viable.length?[]:ranked.slice(0,5),
  };
}
function recordResearchHistory(status){
  const snap=researchSummary(status);
  let history=readJson(RESEARCH_HISTORY_FILE,[]);
  if(!Array.isArray(history))history=[];
  const last=history.at(-1);
  const lastTs=last?.generated_at?Date.parse(last.generated_at):0;
  const changed=!last
    || n(last.candidate_pass_count,-1)!==n(snap.candidate_pass_count,-1)
    || !!last.halted!==!!snap.halted
    || String(last.halt_reason||'')!==String(snap.halt_reason||'')
    || (Date.now()-lastTs)>=5*60*1000;
  if(changed){
    history.push(snap);
    history=history.slice(-300);
    writeJsonAtomic(RESEARCH_HISTORY_FILE,history);
  }
}


function strategyFamilyProgress(strategyRows){
  const out={};
  for(const family of ['scalp_trend','trend_momentum','mean_reversion','donchian_breakout','bollinger_reversion','pullback_trend','atr_breakout','rsi_reclaim']){
    const rows=(strategyRows||[]).filter(r=>r.family===family);
    if(!rows.length){out[family]={family,candidate_count:0,pass_count:0};continue;}
    const ranked=[...rows].sort((a,b)=>n(b.score)-n(a.score));
    const best=ranked[0];
    out[family]={
      family,
      candidate_count:rows.length,
      pass_count:rows.filter(r=>r.validation_pass).length,
      best_candidate:best.name,
      best_market:best.symbol,
      best_score:round(n(best.score),3),
      best_return_pct:round(n(best.return_pct),3),
      best_stress_return_pct:round(n(best.stress_return_pct),3),
      best_win_rate:round(n(best.win_rate),2),
      best_drawdown:round(n(best.max_drawdown),3),
      best_trades:n(best.trades,0),
      walk_forward_positive_windows:n(best.walk_forward_positive_windows,0),
      walk_forward_total_windows:n(best.walk_forward_total_windows,0),
    };
  }
  return out;
}

function paperTradingEnabled(config){
  return config?.paper?.auto_trading_enabled!==false&&config?.research_exploration?.paper_lab_enabled!==false;
}

function marketMovementRows(candlesBySymbol,latest){
  return Object.entries(latest||{}).map(([symbol,x])=>{
    const candles=Array.isArray(candlesBySymbol?.[symbol])?candlesBySymbol[symbol]:[];
    const closed=candles.length>1?candles.at(-2):candles.at(-1);
    const prior=candles.length>2?candles.at(-3):closed;
    const mark=n(x?.price,closed?.close),previous=n(prior?.close,mark);
    return{
      symbol,
      price:round(mark,8),
      previous_close:round(previous,8),
      change_pct:previous?round((mark/previous-1)*100,4):0,
      candle_timestamp:closed?.timestamp||null,
      timestamp:x?.timestamp||closed?.timestamp||Math.floor(Date.now()/1000),
      source:'GMX execution oracle'
    };
  });
}

function activityFeed(status){
  const rows=[];
  const push=(at,kind,title,detail,value=null)=>{if(at)rows.push({at,kind,title,detail,value});};
  for(const signal of status?.signals||[]){
    const at=signal.candle_ts?new Date(signal.candle_ts*1000).toISOString():status.generated_at;
    push(at,'signal',`${signal.symbol} ${String(signal.signal||'flat').toUpperCase()}`,`${String(signal.strategy||'strategy').replaceAll('_',' ')} · ${signal.validation_pass?'validated':'not validated'}`);
  }
  for(const [symbol,decision] of Object.entries(status?.research_paper?.last_decisions||{})){
    push(decision?.at||status.generated_at,'decision',`${symbol} · ${String(decision?.signal||'flat').toUpperCase()}`,String(decision?.reason||'waiting').replaceAll('_',' '));
  }
  for(const position of status?.research_paper?.open_positions||[]){
    push(status.generated_at,'position',`${position.symbol} ${String(position.side||'').toUpperCase()} open`,`${String(position.strategy||'strategy').replaceAll('_',' ')} · mark ${position.mark}`,round(n(position.unrealized_pnl),2));
  }
  for(const trade of [...(status?.recent_trades||[]),...(status?.research_paper?.recent_trades||[]),...(status?.research_tournament?.recent_trades||[])].slice(-30)){
    push(trade?.closed_at||status.generated_at,'trade',`${trade.symbol} ${String(trade.side||'').toUpperCase()} closed`,String(trade.reason||trade.source||'simulated result').replaceAll('_',' '),round(n(trade.pnl),2));
  }
  const seen=new Set();
  return rows.sort((a,b)=>Date.parse(b.at)-Date.parse(a.at)).filter(row=>{const key=`${row.at}|${row.kind}|${row.title}|${row.detail}`;if(seen.has(key))return false;seen.add(key);return true;}).slice(0,40);
}

function decorateRuntimeTelemetry(status,config,candlesBySymbol,latest,runtime){
  status.markets=marketMovementRows(candlesBySymbol,latest);
  const researchEnabled=config.research_exploration?.continuous_market_research_enabled!==false;
  const botEnabled=paperTradingEnabled(config);
  status.controls={
    continuous_market_research:{enabled:researchEnabled,status:researchEnabled?'running':'paused',last_refresh_at:status.market_research?.generated_at||status.generated_at},
    paper_trading_bot:{enabled:botEnabled,status:botEnabled?'running':'paused',main_open_positions:(status.positions||[]).length,research_open_positions:(status.research_paper?.open_positions||[]).length}
  };
  status.runtime_activity={
    cycle_number:n(runtime?.cycle_number,0),
    cycle_started_at:runtime?.last_cycle_started_at||null,
    cycle_completed_at:runtime?.last_cycle_completed_at||status.generated_at,
    duration_ms:n(runtime?.last_cycle_duration_ms,0),
    poll_seconds:config.poll_seconds,
    next_cycle_at:runtime?.next_cycle_at||null,
    markets_scanned:status.markets.length,
    candidate_tests:n(status.research_lab?.tested_candidates,0),
    activity_count:0
  };
  status.activity_feed=activityFeed(status);
  status.runtime_activity.activity_count=status.activity_feed.length;
  if(status.research_lab){
    status.research_lab.continuous_market_research_enabled=researchEnabled;
    status.research_lab.paper_trading_bot_enabled=botEnabled;
  }
  if(status.configuration?.research_exploration)status.configuration.research_exploration.continuous_market_research_enabled=researchEnabled;
  return status;
}

function telemetry(config,candlesBySymbol,latest,results,paper,errors,marketResearch=null,researchState=null,multiSource=null,researchPipeline=null,tournamentState=null){const eq=stateEquity(paper,latest),start=n(paper.starting_equity,config.starting_equity),pnl=eq-start,allTrades=paper.trades||[],wins=paper.wins||0,positions=Object.values(paper.positions||{}).map(p=>({symbol:p.symbol,side:p.side,size_usd:p.notional,margin_usd:p.margin_usd??null,leverage:p.leverage??null,entry_price:p.entry,mark_price:p.mark,unrealized_pnl:p.unrealized_pnl,stop_loss:p.stop,take_profit:p.target,strategy:p.strategy,source:p.source||'auto',status:'SIMULATED PAPER'}));const strategyRows=results.map(r=>({name:r.strategy,family:r.family,params:r.base?.params||resolveCandidate(r.strategy).params,status:r.validation.pass?'validated_candidate':researchEligible(r)?'shadow_eligible':'rejected_research',symbol:r.symbol,timeframe:config.timeframe,score:round(candidateScore(r),3),return_pct:r.base.return_pct,stress_return_pct:r.stress.return_pct,backtest_pnl:r.base.pnl,stress_pnl:r.stress.pnl,ending_equity:r.base.ending_equity,stress_ending_equity:r.stress.ending_equity,win_rate:r.base.win_rate,max_drawdown:r.base.max_drawdown,trades:r.base.trades,profit_factor:r.base.profit_factor,expectancy_pct:r.base.expectancy_pct,walk_forward_positive_windows:r.walk_forward.positive_windows??0,walk_forward_total_windows:r.walk_forward.total_windows??0,validation_pass:r.validation.pass,research_eligible:researchEligible(r),forward_test_eligible:researchForwardEligible(r,config),context_score:round(n(r.context_score),1),regime:r.regime||null,hypothesis:r.hypothesis||null,validation_checks:r.validation.checks}));const passCount=strategyRows.filter(r=>r.validation_pass).length;const familyProgress=strategyFamilyProgress(strategyRows);const researchHistory=readJson(RESEARCH_HISTORY_FILE,[]);const signals=liveSignals(config,candlesBySymbol,results);const configuredAuto=config.paper.auto_trading_enabled!==false;const effectiveAuto=configuredAuto&&passCount>0&&!paper.halted;const autoBlockedReason=!configuredAuto?'owner_disabled':paper.halted?(paper.halt_reason||'risk_halt'):passCount<=0?'no_validation_passing_strategy':null;const drawdownSeries=[start,...(paper.equity_curve||[]).map(x=>x.equity)],selectedStrategies=Object.fromEntries(Object.entries(config.market_settings||{}).filter(([,row])=>row?.enabled!==false).map(([symbol,row])=>[symbol,adaptiveStrategy(symbol,row.paper_strategy||'trend_momentum',results,config.paper.adaptive_strategy_selection!==false)]));return{schema_version:3,generated_at:iso(),signals,engine:{name:'Myles Quant',version:VERSION,status:'running',venue:config.venue,chain_id:config.chain_id,data_source:'GMX execution oracle + Kraken Spot + Coinbase Exchange public market intelligence',market_data_ok:Object.keys(errors||{}).length===0,market_error_count:Object.keys(errors||{}).length,auto_entry_gate:'validated_main_plus_owner_paper_lab'},learning:{self_learning:false,adaptive_validation_selection:config.paper.adaptive_strategy_selection!==false,mode:'multi-source regime-aware research engine + stressed backtests + rolling walk-forward validation',selected_strategies:selectedStrategies,note:`This is a deterministic research engine, not machine learning. Quant combines GMX execution-oracle data with public Kraken and Coinbase market snapshots, classifies market regime, ranks market/strategy hypotheses, evaluates 32 parameterized candidates across eight families on ${config.timeframe} history, then applies stressed execution costs, profit-factor/expectancy gates and rolling walk-forward validation. Paper Lab gathers tiny-risk forward evidence, while a parallel research tournament runs independent simulated strategy books so winners and losers accumulate dollar P&L; live execution remains disabled.`},account_type:'SIMULATED PAPER',mode:'paper',execution_locked:true,live_execution:config.live_execution,balance:round(eq,2),equity:round(eq,2),starting_equity:round(start,2),total_pnl:round(pnl,2),pnl_pct:round(pnl/Math.max(1,start)*100,3),win_rate:allTrades.length?round(wins/allTrades.length*100,2):0,max_drawdown:round(maxDrawdown(drawdownSeries),3),positions,equity_curve:paper.equity_curve||[],markets:Object.entries(latest).map(([symbol,x])=>({symbol,price:round(x.price,8),timestamp:x.timestamp,source:'GMX 1m candle'})),market_errors:errors,market_research:marketResearch,market_intelligence:multiSource,research_pipeline:researchPipeline,research_paper:researchState?researchPaperTelemetry(researchState,latest,config):null,research_tournament:tournamentState?tournamentTelemetry(tournamentState,latest,config,results,candlesBySymbol):null,research_lab:{tested_candidates:strategyRows.length,last_backtest_at:iso(),data_window:researchDataWindow(candlesBySymbol),poll_seconds:config.poll_seconds,forward_test_details:forwardTestDetails(results,candlesBySymbol,config),eligible_shadow_candidates:strategyRows.filter(r=>r.research_eligible).length,forward_test_candidates:strategyRows.filter(r=>r.forward_test_eligible).length,fallback_forward_candidates:strategyRows.filter(r=>r.forward_test_eligible&&!r.research_eligible&&!r.validation_pass).length,rejected_candidates:strategyRows.filter(r=>!r.forward_test_eligible&&!r.validation_pass).length,validated_candidates:passCount,paper_lab_enabled:config.research_exploration?.paper_lab_enabled!==false,timeframe:config.timeframe,history_limit:config.history_limit,candidate_families:[...new Set(strategyRows.map(r=>r.family))],method:`multi-source regime-aware ${config.timeframe} research + GMX execution model + stressed costs + rolling walk-forward + profit-factor/expectancy gates`},strategy_family_progress:familyProgress,research_history:Array.isArray(researchHistory)?researchHistory.slice(-180):[],strategies:strategyRows,backtests:results.map(r=>({strategy:r.strategy,family:r.family,score:round(candidateScore(r),3),market:r.symbol,period:`${candlesBySymbol[r.symbol]?.length||0} × ${config.timeframe}`,return_pct:r.base.return_pct,stress_return_pct:r.stress.return_pct,backtest_pnl:r.base.pnl,stress_pnl:r.stress.pnl,ending_equity:r.base.ending_equity,stress_ending_equity:r.stress.ending_equity,win_rate:r.base.win_rate,max_drawdown:r.base.max_drawdown,trades:r.base.trades,profit_factor:r.base.profit_factor,expectancy_pct:r.base.expectancy_pct,status:r.validation.pass?'PASS':researchEligible(r)?'SHADOW_ELIGIBLE':'REJECTED',context_score:round(n(r.context_score),1),regime:r.regime||null,walk_forward_positive_pct:r.validation.walk_forward_positive_pct})),recent_trades:allTrades.slice(-30),risk:{...config.risk,halted:!!paper.halted,halt_reason:paper.halt_reason,emergency_stop:!!config.paper.emergency_stop},assumptions:{...config.research_costs,stress_cost_multiplier:config.validation.stress_cost_multiplier,note:'Conservative GMX-oracle paper model: position fee on open/close, small oracle movement allowance, and one close-side impact allowance. GMX actual price impact can be positive or negative and funding/borrowing vary with market state.'},paper_control:{configured_auto_enabled:configuredAuto,effective_auto_enabled:effectiveAuto,blocked_reason:autoBlockedReason,promotion_signature:paper.promotion_signature||null,observed_promotion_signature:paper.observed_promotion_signature||null,last_auto_recovery:paper.last_auto_recovery||null},configuration:{timeframe:config.timeframe,history_limit:config.history_limit,poll_seconds:config.poll_seconds,multi_source:config.multi_source,market_settings:config.market_settings,paper:{...config.paper,effective_auto_trading_enabled:effectiveAuto,auto_blocked_reason:autoBlockedReason},risk:{max_position_usd:config.risk.max_position_usd,max_notional_leverage:config.risk.max_notional_leverage,max_risk_per_trade_pct:config.risk.max_risk_per_trade_pct},research_exploration:{paper_lab_enabled:config.research_exploration.paper_lab_enabled!==false,entry_cooldown_bars:config.research_exploration.entry_cooldown_bars,fallback_near_miss:config.research_exploration.fallback_near_miss!==false,tournament_enabled:config.research_exploration.tournament_enabled!==false,tournament_slots:config.research_exploration.tournament_slots,tournament_slot_equity:config.research_exploration.tournament_slot_equity}},validation:{math:mathSelfTest(),candidate_pass_count:passCount,candidate_total:strategyRows.length,live_ready:false,live_ready_reasons:['GMX live adapter is installed separately and remains owner-gated','Owner wallet one-click authorization and explicit ARM are required','Live Auto Bot is disabled until separately armed by the owner']}};}

async function cycle({backtestOnly=false,persist=true}={}){
  const cycleStartedMs=Date.now();
  const priorRuntime=readJson(RUNTIME_STATE_FILE,{version:1,cycle_number:0});
  const runtimeState={...priorRuntime,version:1,cycle_number:n(priorRuntime?.cycle_number,0)+1,last_cycle_started_at:new Date(cycleStartedMs).toISOString()};
  const config=loadConfig(),candlesBySymbol={},latest={},errors={};
  const continuousResearch=config.research_exploration?.continuous_market_research_enabled!==false;
  const enabled=Object.entries(config.market_settings).filter(([,v])=>v.enabled).map(([s])=>s);
  await Promise.all(enabled.map(async symbol=>{
    try{
      candlesBySymbol[symbol]=await fetchGmxCandles(config.chain_id,symbol,config.timeframe,config.history_limit);
      latest[symbol]=await fetchLatestPrice(config.chain_id,symbol);
    }catch(e){errors[symbol]=String(e?.message||e);}
  }));
  const cachedResearch=readJson(MARKET_RESEARCH_FILE,null);
  const marketResearch=continuousResearch?await refreshMarketResearch(config,enabled):{...(cachedResearch||{generated_at:null,markets:{},errors:{},market_count:0,error_count:0}),paused:true,pause_reason:'owner_disabled_continuous_market_research'};
  const cachedMultiSource=readJson(MULTI_SOURCE_FILE,null);
  const multiSource=continuousResearch&&config.multi_source?.enabled!==false?await refreshMultiSourceIntelligence(config,enabled,latest):{...(cachedMultiSource||{generated_at:null,markets:{},health:{},errors:{},market_count:0,error_count:0}),paused:true,pause_reason:'owner_disabled_continuous_market_research'};
  const preliminaryPipeline=buildResearchPipeline(marketResearch,multiSource,[]);
  const results=[];
  for(const symbol of enabled){
    const candles=candlesBySymbol[symbol];if(!candles)continue;
    const reg=preliminaryPipeline.markets?.[symbol]||{};
    for(const candidate of STRATEGY_CANDIDATES){
      if(config.strategies[candidate.family]?.enabled===false)continue;
      const base=backtest(candles,candidate.id,config);
      const stress=backtest(candles,candidate.id,config,{costMultiplier:n(config.validation.stress_cost_multiplier,2.5)});
      const wf=walkForward(candles,candidate.id,config);
      const val=validationFor(base,stress,wf,config);
      const fit=familyRegimeFit(candidate.family,reg.regime||'range'),contextScore=clamp(n(reg.opportunity_score,35)*.6+fit*40,0,100);
      results.push({symbol,strategy:candidate.id,family:candidate.family,base,stress,walk_forward:wf,validation:val,context_score:round(contextScore,1),regime:reg.regime||null,hypothesis:`${candidate.family.replaceAll('_',' ')} for ${String(reg.regime||'unknown').replaceAll('_',' ')} conditions`});
    }
  }
  const researchPipeline=buildResearchPipeline(marketResearch,multiSource,results);
  let paper=readJson(STATE_FILE,null);if(!paper||paper.version!==3)paper=createPaperState(config);
  const paperRecovery=maybeAutoRecoverMainPaper(paper,config,results);paper=paperRecovery.state;
  let researchState=readJson(RESEARCH_STATE_FILE,null);if(!researchState||researchState.version!==3)researchState=createResearchState(config);
  let tournamentState=readJson(TOURNAMENT_STATE_FILE,null);if(!tournamentState||tournamentState.version!==1)tournamentState=createTournamentState(config);
  if(!backtestOnly&&config.paper.enabled)paper=updatePaper(paper,candlesBySymbol,latest,config,results);
  if(!backtestOnly){researchState=config.research_exploration?.paper_lab_enabled!==false?updateResearchPaper(researchState,candlesBySymbol,latest,config,results):pauseResearchPaper(researchState,latest,config);}
  if(!backtestOnly&&continuousResearch&&config.research_exploration?.tournament_enabled!==false)tournamentState=updateResearchTournament(tournamentState,candlesBySymbol,latest,config,results);
  runtimeState.last_cycle_completed_at=iso();
  runtimeState.last_cycle_duration_ms=Date.now()-cycleStartedMs;
  runtimeState.next_cycle_at=new Date(Date.now()+config.poll_seconds*1000).toISOString();
  const status=decorateRuntimeTelemetry(telemetry(config,candlesBySymbol,latest,results,paper,errors,marketResearch,researchState,multiSource,researchPipeline,tournamentState),config,candlesBySymbol,latest,runtimeState);
  if(persist){
    writeJsonAtomic(STATE_FILE,paper);
    writeJsonAtomic(RESEARCH_STATE_FILE,researchState);
    writeJsonAtomic(TOURNAMENT_STATE_FILE,tournamentState);
    writeJsonAtomic(RUNTIME_STATE_FILE,runtimeState);
    writeJsonAtomic(STATUS_FILE,status);
    if(continuousResearch)recordResearchHistory(status);
  }
  return status;
}
async function main(){
  const rawArgs=process.argv.slice(2),args=new Set(rawArgs);
  if(args.has('--print-default-config')){console.log(JSON.stringify(DEFAULT_CONFIG,null,2));return;}
  if(args.has('--self-test')){const r={...mathSelfTest(),version:VERSION};console.log(JSON.stringify(r,null,2));process.exit(r.pass?0:1);}
  const manualIndex=rawArgs.indexOf('--manual-order');
  if(manualIndex>=0){
    try{const payload=JSON.parse(rawArgs[manualIndex+1]||'{}');const result=await manualPaperAction(payload);console.log(JSON.stringify(result));return;}
    catch(err){console.error(JSON.stringify({ok:false,error:String(err?.message||err)}));process.exit(2);}
  }
  const researchIndex=rawArgs.indexOf('--research-report');
  if(researchIndex>=0){
    try{
      const target=path.resolve(rawArgs[researchIndex+1]||path.join(process.cwd(),'quant_research_report.json'));
      const status=await cycle({backtestOnly:true,persist:false});
      const report={
        generated_at:status.generated_at,
        engine:status.engine,
        data_source:status.engine?.data_source,
        market_errors:status.market_errors,
        validation:status.validation,
        backtests:status.backtests,
        strategies:status.strategies,
        assumptions:status.assumptions,
        research_summary:researchSummary(status),
        research_lab:status.research_lab,
        market_research:status.market_research,
        market_intelligence:status.market_intelligence,
        research_pipeline:status.research_pipeline,
        research_paper:status.research_paper,
        research_tournament:status.research_tournament,
      };
      fs.mkdirSync(path.dirname(target),{recursive:true});
      fs.writeFileSync(target,JSON.stringify(report,null,2),'utf8');
      console.log(JSON.stringify({ok:true,report_path:target,passes:status.validation?.candidate_pass_count,total:status.validation?.candidate_total,generated_at:status.generated_at}));
      return;
    }catch(err){console.error(JSON.stringify({ok:false,error:String(err?.stack||err)}));process.exit(3);}
  }
  const once=args.has('--once')||args.has('--backtest-only');
  do{try{const status=await cycle({backtestOnly:args.has('--backtest-only'),persist:!args.has('--backtest-only')});console.log(JSON.stringify({ok:true,generated_at:status.generated_at,equity:status.equity,pnl:status.total_pnl,positions:status.positions.length,backtests:status.backtests.length,markets:status.markets.map(m=>m.symbol),errors:status.market_errors}));}catch(err){const failure={schema_version:3,generated_at:iso(),engine:{name:'Myles Quant',version:VERSION,status:'error'},mode:'paper',execution_locked:true,error:String(err?.stack||err)};writeJsonAtomic(STATUS_FILE,failure);console.error(failure.error);if(once)process.exit(1);}if(once)break;const cfg=loadConfig();await new Promise(r=>setTimeout(r,cfg.poll_seconds*1000));}while(true);
}
if(import.meta.url===`file://${process.argv[1]?.replaceAll('\\','/')}`||path.resolve(process.argv[1]||'')===path.resolve(fileURLToPath(import.meta.url))){main();}
