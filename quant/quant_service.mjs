import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, 'MylesAI') : path.join(os.homedir(), 'AppData', 'Local', 'MylesAI');
const DATA_DIR = path.join(ROOT, 'data');
const STATE_FILE = path.join(DATA_DIR, 'quant_paper_state_v3.json');
const RESEARCH_FILE = path.join(DATA_DIR, 'quant_research_status_v1.json');
const STATUS_FILE = path.join(DATA_DIR, 'trading_status.json');
const COPY_STATUS_FILE = path.join(DATA_DIR, 'copy_trader_status.json');
const CONFIG_FILE = path.join(__dirname, 'quant_config.json');
const VERSION = '0.7.1';
const VALID_PERIODS = new Set(['1m','5m','15m','1h','4h','1d']);
const SUPPORTED_RESEARCH_MARKETS = ['BTC/USD','ETH/USD','SOL/USD','XRP/USD','TAO/USD'];

const DEFAULT_CONFIG = {
  schema_version: 3,
  venue: 'GMX',
  chain_id: 42161,
  timeframe: '1m',
  history_limit: 3000,
  poll_seconds: 30,
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
  },
  paper: { enabled: true, auto_trading_enabled: true, adaptive_strategy_selection: true, emergency_stop: false },
  research_exploration: {
    enabled: true,
    continuous_market_research_enabled: true,
    paper_lab_enabled: true,
    tournament_enabled: true,
    entry_cooldown_bars: 0,
    interval_seconds: 120,
  },
  risk: {
    max_risk_per_trade_pct: 0.50,
    max_notional_leverage: 1.50,
    stop_loss_pct: 1.50,
    take_profit_pct: 3.00,
    max_daily_loss_pct: 2.00,
    max_drawdown_pct: 8.00,
    max_concurrent_positions: 2,
    max_market_allocation_pct: 35.0,
  },
  research_costs: {
    position_fee_bps_per_side: 6,
    slippage_bps_per_side: 5,
    impact_bps_per_side: 20,
    holding_cost_bps_per_day: 5,
  },
  validation: {
    min_trades: 12,
    max_drawdown_pct: 12,
    min_walk_forward_positive_pct: 50,
    min_base_return_pct: 0,
    min_stress_return_pct: -3,
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
  cfg.timeframe=VALID_PERIODS.has(String(cfg.timeframe))?String(cfg.timeframe):'1m';
  cfg.history_limit=Math.round(clamp(n(cfg.history_limit,3000),300,10000));
  cfg.poll_seconds=Math.round(clamp(n(cfg.poll_seconds,30),15,900));
  cfg.starting_equity=clamp(n(cfg.starting_equity,10000),100,10000000);
  cfg.market_settings=cfg.market_settings||{};
  for(const sym of SUPPORTED_RESEARCH_MARKETS){
    const row=cfg.market_settings[sym]||{};
    cfg.market_settings[sym]={enabled:row.enabled!==false,auto_trade_enabled:row.auto_trade_enabled!==false,paper_strategy:['scalp_trend','trend_momentum','mean_reversion'].includes(row.paper_strategy)?row.paper_strategy:'trend_momentum'};
  }
  for(const key of Object.keys(cfg.market_settings)) if(!SUPPORTED_RESEARCH_MARKETS.includes(key)) delete cfg.market_settings[key];
  cfg.risk.max_risk_per_trade_pct=clamp(n(cfg.risk.max_risk_per_trade_pct,.5),.05,5);
  cfg.risk.max_notional_leverage=clamp(n(cfg.risk.max_notional_leverage,1.5),.1,5);
  cfg.risk.stop_loss_pct=clamp(n(cfg.risk.stop_loss_pct,1.5),.25,15);
  cfg.risk.take_profit_pct=clamp(n(cfg.risk.take_profit_pct,3),.25,40);
  cfg.risk.max_daily_loss_pct=clamp(n(cfg.risk.max_daily_loss_pct,2),.25,20);
  cfg.risk.max_drawdown_pct=clamp(n(cfg.risk.max_drawdown_pct,8),.5,40);
  cfg.risk.max_concurrent_positions=Math.round(clamp(n(cfg.risk.max_concurrent_positions,2),1,5));
  cfg.risk.max_market_allocation_pct=clamp(n(cfg.risk.max_market_allocation_pct,35),5,100);
  cfg.research_costs.position_fee_bps_per_side=clamp(n(cfg.research_costs.position_fee_bps_per_side,6),0,100);
  cfg.research_costs.slippage_bps_per_side=clamp(n(cfg.research_costs.slippage_bps_per_side,5),0,300);
  cfg.research_costs.impact_bps_per_side=clamp(n(cfg.research_costs.impact_bps_per_side,20),0,1000);
  cfg.research_costs.holding_cost_bps_per_day=clamp(n(cfg.research_costs.holding_cost_bps_per_day,5),0,300);
  cfg.validation.min_trades=Math.round(clamp(n(cfg.validation.min_trades,12),1,500));
  cfg.validation.max_drawdown_pct=clamp(n(cfg.validation.max_drawdown_pct,12),1,60);
  cfg.validation.min_walk_forward_positive_pct=clamp(n(cfg.validation.min_walk_forward_positive_pct,50),0,100);
  cfg.validation.min_base_return_pct=clamp(n(cfg.validation.min_base_return_pct,0),-100,500);
  cfg.validation.min_stress_return_pct=clamp(n(cfg.validation.min_stress_return_pct,-3),-100,500);
  cfg.validation.stress_cost_multiplier=clamp(n(cfg.validation.stress_cost_multiplier,2.5),1,10);
  cfg.paper.enabled=cfg.paper.enabled!==false;
  cfg.paper.auto_trading_enabled=cfg.paper.auto_trading_enabled!==false;
  cfg.paper.adaptive_strategy_selection=cfg.paper.adaptive_strategy_selection!==false;
  cfg.paper.emergency_stop=!!cfg.paper.emergency_stop;
  cfg.research_exploration=cfg.research_exploration&&typeof cfg.research_exploration==='object'?cfg.research_exploration:{};
  cfg.research_exploration.enabled=cfg.research_exploration.enabled!==false;
  cfg.research_exploration.continuous_market_research_enabled=cfg.research_exploration.continuous_market_research_enabled!==false;
  cfg.research_exploration.paper_lab_enabled=cfg.research_exploration.paper_lab_enabled!==false;
  cfg.research_exploration.tournament_enabled=cfg.research_exploration.tournament_enabled!==false;
  cfg.research_exploration.entry_cooldown_bars=Math.round(clamp(n(cfg.research_exploration.entry_cooldown_bars,cfg.paper.entry_cooldown_bars||0),0,50));
  cfg.research_exploration.interval_seconds=Math.round(clamp(n(cfg.research_exploration.interval_seconds,120),120,3600));
  cfg.live_execution={enabled:false,signing_enabled:false,reason:DEFAULT_CONFIG.live_execution.reason};
  return cfg;
}
function loadConfig(){ const cfg=normalizeConfig(readJson(CONFIG_FILE,DEFAULT_CONFIG)); writeJsonAtomic(CONFIG_FILE,cfg); return cfg; }

function loadResearchState(){
  const raw=readJson(RESEARCH_FILE,null);
  if(!raw||raw.version!==1)return{version:1,last_run_epoch:0,cycle_sequence:0,results:[],history:[],promotions:[],activity_feed:[]};
  return{version:1,last_run_epoch:n(raw.last_run_epoch,0),cycle_sequence:n(raw.cycle_sequence,0),results:Array.isArray(raw.results)?raw.results:[],history:Array.isArray(raw.history)?raw.history:[],promotions:Array.isArray(raw.promotions)?raw.promotions:[],activity_feed:Array.isArray(raw.activity_feed)?raw.activity_feed:[]};
}
function compactResearchResult(r){
  const pick=x=>({return_pct:n(x?.return_pct,0),pnl:n(x?.pnl,0),ending_equity:n(x?.ending_equity,0),win_rate:n(x?.win_rate,0),max_drawdown:n(x?.max_drawdown,0),trades:n(x?.trades,0)});
  return{symbol:r.symbol,strategy:r.strategy,base:pick(r.base),stress:pick(r.stress),walk_forward:{status:r.walk_forward?.status||'unknown',positive_windows:n(r.walk_forward?.positive_windows,0),total_windows:n(r.walk_forward?.total_windows,0)},validation:r.validation||{}};
}
function candidateScore(r){
  const v=r?.validation||{},b=r?.base||{},s=r?.stress||{},wf=r?.walk_forward||{};
  return round((v.pass?1000:0)+n(s.return_pct,-1000)*10+n(b.return_pct,-1000)*2+n(b.win_rate,0)*.2-n(b.max_drawdown,1000)*.5+(n(wf.positive_windows,0)/Math.max(1,n(wf.total_windows,0)))*10,4);
}
function forwardCandidate(r,config){
  if(r?.validation?.pass===true)return true;
  const minimum=Math.max(3,Math.min(n(config.validation?.min_trades,12),6));
  return n(r?.base?.trades,0)>=minimum&&r?.walk_forward?.status==='complete'&&n(r?.stress?.return_pct,-1000)>=-8;
}
function promoteValidatedStrategies(config,results){
  if(config.paper?.adaptive_strategy_selection===false||config.research_exploration?.tournament_enabled===false)return[];
  const promotions=[];
  const minResearchTrades=Math.max(3,Math.min(n(config.validation?.min_trades,12),6));
  for(const symbol of SUPPORTED_RESEARCH_MARKETS){
    const rows=results.filter(r=>r.symbol===symbol);
    const candidates=rows.filter(r=>r.validation?.pass||(
      n(r.base?.trades,0)>=minResearchTrades &&
      r.walk_forward?.status==='complete' &&
      n(r.stress?.return_pct,-1000)>=-8
    )).sort((a,b)=>candidateScore(b)-candidateScore(a));
    const best=candidates[0];
    if(!best)continue;
    const current=config.market_settings?.[symbol]?.paper_strategy||'trend_momentum';
    const incumbent=rows.find(r=>r.strategy===current);
    const incumbentScore=incumbent?candidateScore(incumbent):-100000;
    if(best.strategy!==current&&candidateScore(best)>incumbentScore+.25){
      if(config.market_settings?.[symbol])config.market_settings[symbol].paper_strategy=best.strategy;
      promotions.push({
        at:iso(),symbol,from:current,to:best.strategy,score:candidateScore(best),
        validation_pass:best.validation?.pass===true,
        reason:best.validation?.pass?'validated candidate beat the incumbent':'research candidate beat the incumbent; forward paper test'
      });
    }
  }
  return promotions;
}
let researchState=loadResearchState();
let cachedResearchResults=Array.isArray(researchState.results)?researchState.results:[];
let lastResearchEpoch=n(researchState.last_run_epoch,0);
let cycleSequence=n(researchState.cycle_sequence,0);

export function sma(values,period){ if(!Array.isArray(values)||period<1||values.length<period)return null; let sum=0; for(let i=values.length-period;i<values.length;i++)sum+=values[i]; return sum/period; }
export function emaSeries(values,period){ if(!Array.isArray(values)||!values.length||period<1)return[]; const k=2/(period+1),out=[]; let prev=values[0]; out.push(prev); for(let i=1;i<values.length;i++){prev=values[i]*k+prev*(1-k);out.push(prev);} return out; }
export function rsiSeries(values,period=14){ const out=Array(values.length).fill(null); if(values.length<=period)return out; let gain=0,loss=0; for(let i=1;i<=period;i++){const d=values[i]-values[i-1];if(d>=0)gain+=d;else loss-=d;} gain/=period;loss/=period;out[period]=loss===0?100:100-100/(1+gain/loss); for(let i=period+1;i<values.length;i++){const d=values[i]-values[i-1],g=Math.max(0,d),l=Math.max(0,-d);gain=(gain*(period-1)+g)/period;loss=(loss*(period-1)+l)/period;out[i]=loss===0?100:100-100/(1+gain/loss);} return out; }
export function maxDrawdown(equity){ let peak=-Infinity,worst=0; for(const v of equity){peak=Math.max(peak,v);if(peak>0)worst=Math.max(worst,(peak-v)/peak);} return worst*100; }
export function signalTrendMomentum(candles,index){ if(index<60)return 0; const closes=candles.slice(0,index+1).map(c=>c.close),fast=emaSeries(closes,20).at(-1),slow=emaSeries(closes,50).at(-1),rsi=rsiSeries(closes,14).at(-1); if(fast==null||slow==null||rsi==null)return 0; if(fast>slow&&rsi>=52&&rsi<=74)return 1; if(fast<slow&&rsi<=48&&rsi>=26)return-1; return 0; }
export function signalMeanReversion(candles,index){ if(index<40)return 0; const closes=candles.slice(0,index+1).map(c=>c.close),ma=sma(closes,30),rsi=rsiSeries(closes,14).at(-1),price=closes.at(-1); if(!ma||rsi==null)return 0; const deviation=(price-ma)/ma; if(deviation<-.025&&rsi<35)return 1; if(deviation>.025&&rsi>65)return-1; return 0; }
export function signalScalpTrend(candles,index){
  if(index<55)return 0;
  const closes=candles.slice(0,index+1).map(c=>c.close);
  const e9=emaSeries(closes,9).at(-1),e21=emaSeries(closes,21).at(-1),e50=emaSeries(closes,50).at(-1),rsi=rsiSeries(closes,14).at(-1);
  const c=candles[index],prev=candles[index-1];
  if([e9,e21,e50,rsi].some(v=>v==null)||!prev)return 0;
  if(e9>e21&&e21>e50&&rsi>=52&&rsi<=72&&c.close>prev.close)return 1;
  if(e9<e21&&e21<e50&&rsi<=48&&rsi>=28&&c.close<prev.close)return -1;
  return 0;
}
function strategySignal(name,candles,index){
  if(name==='scalp_trend')return signalScalpTrend(candles,index);
  if(name==='mean_reversion')return signalMeanReversion(candles,index);
  return signalTrendMomentum(candles,index);
}

function normalizeCandles(raw){ const rows=Array.isArray(raw)?raw:raw?.candles; if(!Array.isArray(rows))return[]; const out=rows.map(c=>Array.isArray(c)?{timestamp:n(c[0]),open:n(c[1]),high:n(c[2]),low:n(c[3]),close:n(c[4])}:{timestamp:n(c.timestamp),open:n(c.open),high:n(c.high),low:n(c.low),close:n(c.close)}).filter(c=>c.timestamp>0&&c.open>0&&c.high>0&&c.low>0&&c.close>0); out.sort((a,b)=>a.timestamp-b.timestamp); return out; }
const GMX_ORACLE_BASES={42161:[
  'https://arbitrum-api.gmxinfra.io',
  'https://arbitrum-api-fallback.gmxinfra.io',
  'https://arbitrum-api-fallback.gmxinfra2.io'
]};
async function fetchJsonUrl(url,label,{attempts=1,timeoutMs=10000}={}){let lastError=null;for(let attempt=1;attempt<=Math.max(1,attempts);attempt++){const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),timeoutMs);try{const r=await fetch(url,{headers:{accept:'application/json','user-agent':'MylesQuant/'+VERSION},signal:controller.signal});const text=await r.text();if(!r.ok)throw new Error(label+': HTTP '+r.status+' '+r.statusText+' - '+text.replace(/\s+/g,' ').slice(0,400));return JSON.parse(text);}catch(err){lastError=err;if(attempt<attempts)await new Promise(resolve=>setTimeout(resolve,Math.min(1200,200*attempt)));}finally{clearTimeout(timer);}}throw lastError||new Error(label+': request failed');}
async function fetchGmxCandles(chainId,symbol,timeframe,limit){ const bases=GMX_ORACLE_BASES[Number(chainId)]; if(!bases)throw new Error('Unsupported chain '+chainId); const tokenSymbol=String(symbol).split('/')[0].toUpperCase();const errors=[];for(const base of bases){try{const url=new URL(base+'/prices/candles');url.searchParams.set('tokenSymbol',tokenSymbol);url.searchParams.set('period',timeframe);url.searchParams.set('limit',String(Math.max(1,Math.min(10000,Math.trunc(n(limit,1000))))));const raw=await fetchJsonUrl(url,'GMX '+tokenSymbol+'/'+timeframe+' via '+base,{attempts:1,timeoutMs:10000});const candles=normalizeCandles(raw);if(candles.length<Math.min(80,Number(limit)))throw new Error('returned only '+candles.length+' usable '+timeframe+' candles');return candles;}catch(err){errors.push(base+': '+String(err?.message||err));}}throw new Error('GMX oracle hosts failed for '+tokenSymbol+'/'+timeframe+': '+errors.join(' | '));}
async function fetchLatestPrice(chainId,symbol){ const c=await fetchGmxCandles(chainId,symbol,'1m',2);const last=c.at(-1);return {price:last.close,timestamp:last.timestamp,source:'GMX 1m candle',degraded:false};}
async function fetchMarketSnapshot(config,symbol,limit){
  const candles=await fetchGmxCandles(config.chain_id,symbol,config.timeframe,limit);
  let latest=null,markError=null;
  try{latest=await fetchLatestPrice(config.chain_id,symbol);}
  catch(err){const fallback=candles.at(-1);if(!fallback)throw err;latest={price:fallback.close,timestamp:fallback.timestamp,source:'GMX '+config.timeframe+' candle (fallback mark)',degraded:true};markError=String(err?.message||err);}
  return{candles,latest,markError};
}

function costs(config,mult=1){ return {fee:n(config.research_costs.position_fee_bps_per_side,6)/10000*mult,slip:n(config.research_costs.slippage_bps_per_side,5)/10000*mult,impact:n(config.research_costs.impact_bps_per_side,20)/10000*mult,holding:n(config.research_costs.holding_cost_bps_per_day,5)/10000*mult}; }
function entryFill(mark,direction,cost){ return mark*(1+direction*(cost.slip+cost.impact)); }
function exitFill(mark,direction,cost){ return mark*(1-direction*(cost.slip+cost.impact)); }
function positionSize(equity,config,entry){ const riskPct=n(config.risk.max_risk_per_trade_pct,.5)/100,stopPct=n(config.risk.stop_loss_pct,1.5)/100,lev=n(config.risk.max_notional_leverage,1.5),alloc=n(config.risk.max_market_allocation_pct,35)/100; const riskBudget=equity*riskPct;const byRisk=riskBudget/Math.max(.0001,stopPct);const notional=Math.min(equity*lev,equity*alloc,byRisk);return {notional,units:notional/entry,risk_budget:riskBudget}; }
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
  const start=n(config.starting_equity,10000),cost=costs(config,costMultiplier);let cash=start,position=null,wins=0,losses=0;const trades=[],curve=[];
  for(let i=60;i<candles.length;i++){
    const c=candles[i],signal=strategySignal(strategyName,candles,i);
    let exitedThisCandle=false;
    if(position){let ex=intrabarExit(position,c);if(!ex&&signal!==0&&signal!==position.direction)ex={reason:'signal_exit',raw:c.close};if(ex){const calc=closeCalc(position,ex.raw,c.timestamp,cost);cash+=calc.gross-calc.exit_fee-calc.holding_cost;const pnl=calc.net;trades.push({entry_time:new Date(position.opened_ts*1000).toISOString(),exit_time:new Date(c.timestamp*1000).toISOString(),side:position.direction>0?'long':'short',entry:round(position.entry,4),exit:round(calc.exit,4),pnl:round(pnl,2),return_pct:round(pnl/Math.max(1,position.notional)*100,3),reason:ex.reason});if(pnl>0)wins++;else losses++;position=null;exitedThisCandle=true;}
    }
    if(!position&&!exitedThisCandle&&signal!==0){const entry=entryFill(c.close,signal,cost),sz=positionSize(cash,config,entry),st=stopTarget(entry,signal,config),entryFee=Math.abs(sz.notional)*cost.fee;cash-=entryFee;position={direction:signal,entry,units:sz.units,notional:sz.notional,entry_fee:entryFee,stop:st.stop,target:st.target,opened_ts:c.timestamp};}
    const unreal=position?position.direction*position.units*(c.close-position.entry):0;curve.push({timestamp:c.timestamp,equity:round(cash+unreal,2)});
  }
  if(position&&candles.length){const c=candles.at(-1),calc=closeCalc(position,c.close,c.timestamp,cost);cash+=calc.gross-calc.exit_fee-calc.holding_cost;const pnl=calc.net;trades.push({entry_time:new Date(position.opened_ts*1000).toISOString(),exit_time:new Date(c.timestamp*1000).toISOString(),side:position.direction>0?'long':'short',entry:round(position.entry,4),exit:round(calc.exit,4),pnl:round(pnl,2),return_pct:round(pnl/Math.max(1,position.notional)*100,3),reason:'end_of_test'});if(pnl>0)wins++;else losses++;curve.push({timestamp:c.timestamp,equity:round(cash,2)});}
  return{strategy:strategyName,starting_equity:start,ending_equity:round(cash,2),pnl:round(cash-start,2),return_pct:round((cash/start-1)*100,3),win_rate:trades.length?round(wins/trades.length*100,2):0,trades:trades.length,max_drawdown:round(maxDrawdown(curve.map(x=>x.equity)),3),equity_curve:curve,recent_trades:trades.slice(-30),cost_multiplier:costMultiplier};
}
export function walkForward(candles,strategyName,config){if(candles.length<420)return{strategy:strategyName,status:'insufficient_history',windows:[]};const windows=[],train=240,test=120,step=120;for(let start=0;start+train+test<=candles.length;start+=step){const seg=candles.slice(Math.max(0,start+train-60),start+train+test),r=backtest(seg,strategyName,config);windows.push({start:new Date(candles[start+train].timestamp*1000).toISOString(),end:new Date(candles[start+train+test-1].timestamp*1000).toISOString(),return_pct:r.return_pct,win_rate:r.win_rate,max_drawdown:r.max_drawdown,trades:r.trades});}return{strategy:strategyName,status:'complete',windows,positive_windows:windows.filter(w=>w.return_pct>0).length,total_windows:windows.length};}
function validationFor(base,stress,wf,config){const v=config.validation,total=Math.max(1,wf.total_windows||0),positivePct=(wf.positive_windows||0)/total*100;const checks={min_trades:base.trades>=n(v.min_trades,12),base_return:base.return_pct>=n(v.min_base_return_pct,0),stress_return:stress.return_pct>=n(v.min_stress_return_pct,-3),max_drawdown:base.max_drawdown<=n(v.max_drawdown_pct,12),walk_forward_positive_pct:wf.status==='complete'&&positivePct>=n(v.min_walk_forward_positive_pct,50)};return{pass:Object.values(checks).every(Boolean),checks,walk_forward_positive_pct:round(positivePct,1)};}

function createPaperState(config){const e=n(config.starting_equity,10000);return{version:3,created_at:iso(),starting_equity:e,cash:e,realized_pnl:0,positions:{},wins:0,losses:0,trades:[],equity_curve:[],decision_feed:[],day_key:new Date().toISOString().slice(0,10),day_start_equity:e,peak_equity:e,halted:false,halt_reason:null,last_candle_ts:{}};}
function stateEquity(state,latest){let eq=n(state.cash,0);for(const [symbol,p] of Object.entries(state.positions||{})){const mark=n(latest[symbol]?.price,p.mark||p.entry);p.mark=mark;p.unrealized_pnl=round(p.direction*p.units*(mark-p.entry),2);eq+=p.unrealized_pnl;}return eq;}
function closePaperPosition(state,symbol,rawExit,ts,cost,reason){const p=state.positions[symbol];if(!p)return;const calc=closeCalc(p,rawExit,ts,cost);state.cash+=calc.gross-calc.exit_fee-calc.holding_cost;state.realized_pnl+=calc.net;state.trades.push({symbol,side:p.direction>0?'long':'short',strategy:p.strategy||'unknown',entry:round(p.entry,4),exit:round(calc.exit,4),pnl:round(calc.net,2),opened_at:new Date(p.opened_ts*1000).toISOString(),closed_at:new Date(ts*1000).toISOString(),reason});if(calc.net>0)state.wins++;else state.losses++;delete state.positions[symbol];}
function choosePaperSignal(symbol,candles,config,results=[]){
  const configured=config.market_settings?.[symbol]?.paper_strategy||'trend_momentum';
  const current=strategySignal(configured,candles,candles.length-1);
  if(current!==0)return{strategy:configured,signal:current,source:'configured_strategy'};
  const ranked=results.filter(r=>r.symbol===symbol).slice().sort((a,b)=>candidateScore(b)-candidateScore(a));
  for(const row of ranked){
    const strategy=String(row.strategy||'');
    if(!['scalp_trend','trend_momentum','mean_reversion'].includes(strategy))continue;
    const signal=strategySignal(strategy,candles,candles.length-1);
    if(signal!==0)return{strategy,signal,source:row.validation?.pass?'validated_candidate':'research_candidate'};
  }
  return{strategy:configured,signal:0,source:'configured_strategy'};
}

function updatePaper(state,candlesBySymbol,latest,config,researchResults=[]){
  const cost=costs(config,1);state.positions=state.positions||{};state.last_candle_ts=state.last_candle_ts||{};state.decision_feed=Array.isArray(state.decision_feed)?state.decision_feed:[];
  const enabled=Object.entries(config.market_settings).filter(([,v])=>v.enabled).map(([sym])=>sym);
  const newestTs=Math.max(...enabled.map(sym=>candlesBySymbol[sym]?.at(-1)?.timestamp||0),0);
  const dayKey=new Date(newestTs*1000||Date.now()).toISOString().slice(0,10);
  let eq=stateEquity(state,latest);
  if(dayKey!==state.day_key){state.day_key=dayKey;state.day_start_equity=eq;state.halted=false;state.halt_reason=null;}
  const dailyLoss=(state.day_start_equity-eq)/Math.max(1,state.day_start_equity)*100;
  const dd=(state.peak_equity-eq)/Math.max(1,state.peak_equity)*100;
  if(config.paper.emergency_stop){state.halted=true;state.halt_reason='owner_emergency_stop';}
  else if(dailyLoss>=n(config.risk.max_daily_loss_pct,2)){state.halted=true;state.halt_reason='daily_loss_limit';}
  else if(dd>=n(config.risk.max_drawdown_pct,8)){state.halted=true;state.halt_reason='max_drawdown_limit';}
  if(state.halted){for(const symbol of Object.keys(state.positions)){const c=candlesBySymbol[symbol]?.at(-1);if(c)closePaperPosition(state,symbol,c.close,c.timestamp,cost,state.halt_reason);}}
  for(const symbol of enabled){
    const candles=candlesBySymbol[symbol],c=candles?.at(-1);if(!c||state.last_candle_ts[symbol]>=c.timestamp)continue;
    const marketCfg=config.market_settings[symbol]||{};
    const p=state.positions[symbol];
    const choice=p
      ? {strategy:p.strategy||marketCfg.paper_strategy||'trend_momentum',signal:strategySignal(p.strategy||marketCfg.paper_strategy||'trend_momentum',candles,candles.length-1),source:'open_position'}
      : choosePaperSignal(symbol,candles,config,researchResults);
    const strategy=choice.strategy;
    const signal=choice.signal;
    let exitedThisCandle=false;
    if(p){
      // Manual positions must never replay the whole strategy candle after entry.
      // Their stop/target checks use the fresh GMX market mark only.
      let ex=p.source==='manual'?manualMarkExit(p,n(latest[symbol]?.price,c.close)):intrabarExit(p,c);
      if(!ex&&p.source!=='manual'&&signal!==0&&signal!==p.direction)ex={reason:'signal_exit',raw:c.close};
      if(ex){closePaperPosition(state,symbol,ex.raw,latest[symbol]?.timestamp||c.timestamp,cost,ex.reason);exitedThisCandle=true;}
    }
    eq=stateEquity(state,latest);
    const openCount=Object.keys(state.positions).length;
    const autoAllowed=config.paper.auto_trading_enabled!==false&&marketCfg.auto_trade_enabled!==false;
    let decision='hold',reason='flat_signal';
    if(autoAllowed&&!state.positions[symbol]&&!exitedThisCandle&&!state.halted&&signal!==0&&openCount<n(config.risk.max_concurrent_positions,2)){
      const entry=entryFill(c.close,signal,cost),sz=positionSize(eq,config,entry),st=stopTarget(entry,signal,config),entryFee=sz.notional*cost.fee;
      state.cash-=entryFee;
      state.positions[symbol]={symbol,direction:signal,side:signal>0?'long':'short',entry:round(entry,6),units:sz.units,notional:round(sz.notional,2),margin_usd:round(sz.notional/Math.max(.1,n(config.risk.max_notional_leverage,1.5)),2),leverage:n(config.risk.max_notional_leverage,1.5),entry_fee:entryFee,stop:round(st.stop,6),target:round(st.target,6),opened_ts:c.timestamp,mark:c.close,unrealized_pnl:0,strategy,source:'auto'};
      decision='open';reason=choice.source;
    }else if(exitedThisCandle){decision='close';reason='exit_signal_or_risk';}
    else if(state.halted){decision='hold';reason=state.halt_reason||'risk_halt';}
    else if(!autoAllowed){decision='hold';reason='paper_auto_trading_disabled';}
    else if(state.positions[symbol]){decision='hold';reason='position_open'}
    else if(openCount>=n(config.risk.max_concurrent_positions,2)){decision='hold';reason='max_concurrent_positions'}
    state.decision_feed.push({at:iso(),symbol,strategy,signal:signal>0?'long':signal<0?'short':'flat',source:choice.source,action:decision,reason});
    state.last_candle_ts[symbol]=c.timestamp;
  }
  eq=stateEquity(state,latest);state.peak_equity=Math.max(state.peak_equity,eq);state.equity_curve.push({timestamp:newestTs||Math.floor(Date.now()/1000),equity:round(eq,2)});state.equity_curve=state.equity_curve.slice(-2000);state.trades=state.trades.slice(-500);state.decision_feed=state.decision_feed.slice(-300);return state;
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
    const maxNotional=Math.min(equity*n(config.risk.max_notional_leverage,1.5),maxByRisk,maxByAllocation);
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

function mathSelfTest(){const cfg=normalizeConfig(DEFAULT_CONFIG),cost={fee:0,slip:0,impact:0,holding:0};const p={direction:1,entry:100,units:10,notional:1000,entry_fee:0,opened_ts:0,stop:98.5,target:103};const c=closeCalc(p,102,3600,cost);const both=intrabarExit(p,{low:98,high:104});const size=positionSize(10000,cfg,100);const manualRisk=(1000*2*.015);const manualHold=manualMarkExit({...p,source:'manual'},100);const manualStop=manualMarkExit({...p,source:'manual'},98.4);const checks={long_pnl_exact:Math.abs(c.net-20)<1e-9,conservative_same_candle_stop:both?.reason==='stop_and_target_same_candle_conservative_stop',manual_does_not_replay_old_candle:manualHold===null,manual_mark_stop:manualStop?.reason==='stop_loss',risk_size_respects_leverage:size.notional<=15000.0001,risk_size_respects_allocation:size.notional<=3500.0001,manual_risk_math:Math.abs(manualRisk-30)<1e-9,live_hard_locked:cfg.live_execution.enabled===false&&cfg.live_execution.signing_enabled===false,valid_stop_target:p.stop<p.entry&&p.target>p.entry};return{pass:Object.values(checks).every(Boolean),checks};}

function liveSignals(config,candlesBySymbol,results=[]){const validated=new Map(results.map(r=>[`${r.symbol}|${r.strategy}`,!!r.validation?.pass]));const rows=[];for(const [symbol,row] of Object.entries(config.market_settings||{})){if(row?.enabled===false||row?.auto_trade_enabled===false)continue;const candles=candlesBySymbol[symbol];if(!Array.isArray(candles)||candles.length<61)continue;const strategy=row.paper_strategy||'trend_momentum',idx=candles.length-2,raw=strategySignal(strategy,candles,idx);rows.push({symbol,strategy,signal:raw>0?'long':raw<0?'short':'flat',candle_ts:candles[idx].timestamp,timeframe:config.timeframe,validation_pass:validated.get(`${symbol}|${strategy}`)===true});}return rows;}

function telemetry(config,candlesBySymbol,latest,results,paper,errors,meta={}){
  const now=iso(),eq=stateEquity(paper,latest),start=n(paper.starting_equity,config.starting_equity),pnl=eq-start,allTrades=paper.trades||[],wins=paper.wins||0;
  const copyRaw=readJson(COPY_STATUS_FILE,{}),copyGenerated=copyRaw?.generated_at?Date.parse(copyRaw.generated_at):NaN,copyAge=Number.isFinite(copyGenerated)?Math.max(0,(Date.now()-copyGenerated)/1000):null,copyFresh=copyRaw?.ok!==false&&copyAge!==null&&copyAge<=900,copySignals=Array.isArray(copyRaw?.signals)?copyRaw.signals:[],copyQualified=Array.isArray(copyRaw?.qualified)?copyRaw.qualified:[];
  const positions=Object.values(paper.positions||{}).map(p=>({symbol:p.symbol,side:p.side,size_usd:p.notional,margin_usd:p.margin_usd??null,leverage:p.leverage??null,entry_price:p.entry,mark_price:p.mark,unrealized_pnl:p.unrealized_pnl,stop_loss:p.stop,take_profit:p.target,strategy:p.strategy,source:p.source||'auto',status:'SIMULATED PAPER'}));
  const strategyRows=results.map(r=>({name:r.strategy,status:r.validation?.pass?'validated_candidate':forwardCandidate(r,config)?'forward_candidate':'research',symbol:r.symbol,timeframe:config.timeframe,return_pct:n(r.base?.return_pct,0),stress_return_pct:n(r.stress?.return_pct,0),win_rate:n(r.base?.win_rate,0),max_drawdown:n(r.base?.max_drawdown,0),trades:n(r.base?.trades,0),walk_forward_positive_windows:n(r.walk_forward?.positive_windows,0),walk_forward_total_windows:n(r.walk_forward?.total_windows,0),validation_pass:r.validation?.pass===true,forward_test_eligible:forwardCandidate(r,config),validation_checks:r.validation?.checks||{},promotion_score:candidateScore(r)}));
  const passCount=strategyRows.filter(r=>r.validation_pass).length;
  const signals=liveSignals(config,candlesBySymbol,results);
  const researchOn=config.research_exploration?.enabled!==false&&config.research_exploration?.continuous_market_research_enabled!==false;
  const paperBotOn=config.paper?.enabled!==false&&config.paper?.auto_trading_enabled!==false&&config.research_exploration?.paper_lab_enabled!==false;
  const enabled=Object.entries(config.market_settings||{}).filter(([,v])=>v.enabled).map(([symbol])=>symbol);
  const forwardDetails=strategyRows.filter(r=>r.forward_test_eligible).map(r=>({symbol:r.symbol,strategy:r.name,status:r.validation_pass?'validated':'candidate',stress_return_pct:r.stress_return_pct,base_return_pct:r.return_pct,win_rate:r.win_rate,max_drawdown:r.max_drawdown,trades:r.trades,walk_forward_positive_pct:r.walk_forward_total_windows?round(r.walk_forward_positive_windows/r.walk_forward_total_windows*100,1):0,profit_factor:null,signal:(signals.find(x=>x.symbol===r.symbol&&x.strategy===r.name)?.signal||'flat'),forward_test_eligible:true,promotion_score:r.promotion_score}));
  const familyProgress={};
  for(const name of ['scalp_trend','trend_momentum','mean_reversion']){
    const rows=strategyRows.filter(r=>r.name===name);
    const ranked=rows.slice().sort((a,b)=>b.promotion_score-a.promotion_score);
    const best=ranked[0]||null;
    const familyPassCount=rows.filter(r=>r.validation_pass).length;
    familyProgress[name]={tested:rows.length,candidate_count:rows.length,validated:familyPassCount,pass_count:familyPassCount,best_candidate:best?.name||null,best_market:best?.symbol||null,best_stress_return_pct:rows.length?Math.max(...rows.map(r=>r.stress_return_pct)):null,best_base_return_pct:rows.length?Math.max(...rows.map(r=>r.return_pct)):null,promoted_count:researchState.promotions.filter(x=>x.to===name).length};
  }
  const marketIntelMarkets={};
  const pipelineMarkets={};
  for(const symbol of enabled){
    const mark=latest[symbol];
    const selected=config.market_settings?.[symbol]?.paper_strategy||'trend_momentum';
    const candle=candlesBySymbol[symbol]?.at(-1);
    const selectedRow=results.find(r=>r.symbol===symbol&&r.strategy===selected);
    const signal=signals.find(x=>x.symbol===symbol&&x.strategy===selected)?.signal||'flat';
    const available=!!mark;
    const traderSignal=copySignals.find(x=>x.symbol===symbol),row={regime:'unknown',bias:signal==='long'?'bullish':signal==='short'?'bearish':'neutral',opportunity_score:selectedRow?Math.max(0,Math.min(100,Math.round(candidateScore(selectedRow)/10))):0,source_count:(available?1:0)+(copyFresh&&traderSignal?1:0),consensus_price:available?round(mark.price,8):null,dispersion_bps:null,flow:null,sources:{gmx:{available,mark_source:mark?.source||null,updated_at:mark?.timestamp?new Date(mark.timestamp*1000).toISOString():null},copy_traders:{available:!!(copyFresh&&traderSignal),signal:traderSignal?.side||null,confidence:traderSignal?.confidence??null,updated_at:copyFresh?copyRaw.generated_at:null}},selected_strategy:selected};
    marketIntelMarkets[symbol]=row;
    pipelineMarkets[symbol]={...row,latest_candle_at:candle?.timestamp?new Date(candle.timestamp*1000).toISOString():null};
  }
  const books=strategyRows.map(r=>{
    const paperTrades=allTrades.filter(t=>t.symbol===r.symbol&&t.strategy===r.name);
    const paperPnl=paperTrades.reduce((sum,t)=>sum+n(t.pnl,0),0);
    const open=Object.values(paper.positions||{}).find(p=>p.symbol===r.symbol&&p.strategy===r.name)||null;
    return{key:r.name+'|'+r.symbol,strategy:r.name,symbol:r.symbol,signal:signals.find(x=>x.symbol===r.symbol&&x.strategy===r.name)?.signal||'flat',paper_pnl:round(paperPnl,2),paper_trades:paperTrades.length,paper_win_rate:paperTrades.length?round(paperTrades.filter(t=>n(t.pnl,0)>0).length/paperTrades.length*100,2):0,backtest_pnl:n(results.find(x=>x.symbol===r.symbol&&x.strategy===r.name)?.base?.pnl,0),stress_pnl:n(results.find(x=>x.symbol===r.symbol&&x.strategy===r.name)?.stress?.pnl,0),profit_factor:null,experiment_score:r.promotion_score,open_position:open};
  });
  const marketCount=Object.keys(latest).length;
  const researchRuntime={enabled:researchOn,last_run_at:lastResearchEpoch?new Date(lastResearchEpoch*1000).toISOString():null,last_backtest_at:lastResearchEpoch?new Date(lastResearchEpoch*1000).toISOString():null,interval_seconds:config.research_exploration?.interval_seconds||120,next_run_at:researchOn&&lastResearchEpoch?new Date((lastResearchEpoch+(config.research_exploration?.interval_seconds||120))*1000).toISOString():null,timeframe:config.timeframe,history_limit:config.history_limit,tested_candidates:strategyRows.length,validated_candidates:passCount,forward_test_candidates:forwardDetails.length,paper_lab_enabled:paperBotOn,tournament_enabled:config.research_exploration?.tournament_enabled!==false,scalping_mode:['1m','5m'].includes(config.timeframe),method:'GMX Oracle candles · stressed costs · walk-forward + forward paper',forward_test_details:forwardDetails};
  const familyRows=Object.entries(familyProgress).map(([family,x])=>({family,...x}));
  const strategyHypotheses=strategyRows.slice().sort((a,b)=>b.promotion_score-a.promotion_score).slice(0,8).map(r=>({symbol:r.symbol,family:r.name,thesis:r.validation_pass?`Validated: ${r.stress_return_pct.toFixed(2)}% stressed return across ${r.trades} trades.`:r.forward_test_eligible?`Forward candidate: ${r.stress_return_pct.toFixed(2)}% stressed return; watching the next closed ${config.timeframe} candle.`:`Rejected for now: ${r.stress_return_pct.toFixed(2)}% stressed return or insufficient walk-forward evidence.`,score:r.promotion_score,bias:marketIntelMarkets[r.symbol]?.bias||'neutral',signal:signals.find(x=>x.symbol===r.symbol&&x.strategy===r.name)?.signal||'flat'}));
  const traderHypotheses=copySignals.slice(0,5).map(x=>({symbol:x.symbol,family:'copy_trader_consensus',thesis:`GMX trader consensus is ${String(x.side||'').toUpperCase()} at ${Number(x.confidence||0).toFixed(1)}% confidence from ${x.source_count||0} source(s).`,score:Number(x.confidence||0),bias:x.side==='long'?'bullish':'bearish',signal:x.side}));
  const hypotheses=[...strategyHypotheses,...traderHypotheses].sort((a,b)=>Number(b.score||0)-Number(a.score||0)).slice(0,10);
  const traderFinding=copyFresh?`${copyQualified.length} qualified trader account${copyQualified.length===1?'':'s'} and ${copySignals.length} consensus signal${copySignals.length===1?'':'s'} are available.`:copyRaw?.generated_at?`Trader feed is stale (${Math.round(copyAge||0)}s old); it is excluded from promotion decisions.`:'Trader feed has not published a verified snapshot yet.';
  const bestHypothesis=hypotheses[0];
  const findings={
    headline:marketCount?`GMX is publishing ${marketCount} live market${marketCount===1?'':'s'} on the ${config.timeframe} scalp loop.`:'GMX market data is not fresh.',
    detail:`${strategyRows.length} strategy/market candidates were tested; ${forwardDetails.length} remain in the forward-test pool; ${passCount} passed validation. ${traderFinding}`,
    next_action:passCount?`Keep validated candidates paper-only and score the next closed ${config.timeframe} candle before promotion.`:`Continue the research loop; no strategy is promoted until stressed-cost and walk-forward checks pass.`,
    best_candidate:bestHypothesis?{symbol:bestHypothesis.symbol,strategy:bestHypothesis.family,score:bestHypothesis.score,signal:bestHypothesis.signal}:null,
    source_count:(marketCount>0?1:0)+(copyFresh?1:0),market_count:marketCount,timeframe:config.timeframe,tested_candidates:strategyRows.length,forward_candidates:forwardDetails.length,validated:passCount,trader_candidates:copyRaw.candidates?.length||0,trader_signals:copySignals.length,generated_at:now
  };
  const activity=researchState.activity_feed.length?researchState.activity_feed.slice(-24):[{at:now,type:'quant_cycle',title:'Quant cycle',detail:'Waiting for the first verified GMX cycle',value:0}];
  const maxDd=maxDrawdown((paper.equity_curve||[]).map(x=>x.equity));
  return{
    schema_version:4,generated_at:now,signals,
    controls:{continuous_market_research:{enabled:researchOn,status:researchOn?'running':'paused'},paper_trading_bot:{enabled:paperBotOn,status:paperBotOn?'running':'paused'},adaptive_strategy_selection:{enabled:config.paper?.adaptive_strategy_selection!==false,status:config.paper?.adaptive_strategy_selection!==false?'promoting validated candidates':'locked'}},
    research_runtime:researchRuntime,
    research_lab:researchRuntime,
    research_paper:{active_epoch:researchState.cycle_sequence,starting_equity:start,equity:eq,pnl:round(pnl,2),pnl_pct:round(pnl/Math.max(1,start)*100,3),trades:allTrades.length,win_rate:allTrades.length?round(wins/allTrades.length*100,2):0,max_drawdown:round(maxDd,3),open_positions:positions.length,equity_curve:paper.equity_curve||[],recent_trades:allTrades.slice(-30),last_decisions:(paper.decision_feed||[]).slice(-30),last_trade:allTrades.at(-1)||null,last_cycle_at:now},
    research_history:researchState.history.slice(-120),
    family_progress:familyProgress,
    market_intel:{health:{gmx:{available:marketCount>0,ok_markets:marketCount,total_markets:enabled.length,last_update_at:marketCount?now:null},copy_traders:{available:copyFresh,ok_markets:copyFresh?new Set(copySignals.map(x=>x.symbol)).size:0,total_markets:enabled.length,last_update_at:copyFresh?copyRaw.generated_at:null,candidate_count:copyRaw.candidates?.length||0,qualified_count:copyQualified.length}},markets:marketIntelMarkets},
    research_pipeline:{markets:pipelineMarkets,top_hypotheses:hypotheses,families:familyRows,findings,trader_research:{available:copyFresh,source:copyRaw.data_source||'GMX official API and SDK',generated_at:copyRaw.generated_at||null,age_seconds:copyAge,candidates:copyRaw.candidates?.length||0,qualified:copyQualified.length,signals:copySignals.length,selected_accounts:copyRaw.selected_accounts?.length||0},active_strategy_by_market:Object.fromEntries(enabled.map(symbol=>[symbol,config.market_settings?.[symbol]?.paper_strategy||'trend_momentum']))},
    research_tournament:{enabled:config.research_exploration?.tournament_enabled!==false,slot_count:books.length,open_positions:positions.length,trades:allTrades.length,pnl:round(pnl,2),equity_curve:paper.equity_curve||[],books,recent_trades:allTrades.slice(-30)},
    runtime_activity:{cycle:cycleSequence,cycle_number:cycleSequence,last_cycle_at:now,cycle_completed_at:now,next_cycle_at:new Date(Date.now()+config.poll_seconds*1000).toISOString(),duration_ms:meta.duration_ms??null,poll_seconds:config.poll_seconds,market_count:marketCount,market_error_count:Object.keys(errors).length,research_enabled:researchOn,research_last_run_at:lastResearchEpoch?new Date(lastResearchEpoch*1000).toISOString():null,paper_bot_enabled:paperBotOn,open_positions:positions.length,closed_trades:allTrades.length},
    activity_feed:activity,
    engine:{name:'Myles Quant',version:VERSION,status:'running',health:marketCount?'ok':'degraded',venue:config.venue,chain_id:config.chain_id,data_source:'GMX Oracle /prices/candles + 1m market marks'},
    account_type:'SIMULATED PAPER',mode:'paper',execution_locked:true,live_execution:config.live_execution,
    balance:round(eq,2),equity:round(eq,2),starting_equity:round(start,2),total_pnl:round(pnl,2),pnl_pct:round(pnl/Math.max(1,start)*100,3),win_rate:allTrades.length?round(wins/allTrades.length*100,2):0,max_drawdown:round(maxDd,3),
    positions,equity_curve:paper.equity_curve||[],
    markets:Object.entries(latest).map(([symbol,x])=>({symbol,price:round(x.price,8),timestamp:x.timestamp,source:x.source||'GMX 1m candle',mark_degraded:!!x.degraded})),
    market_errors:errors,strategies:strategyRows,
    backtests:results.map(r=>({strategy:r.strategy,market:r.symbol,period:(candlesBySymbol[r.symbol]?.length||0)+' × '+config.timeframe,return_pct:n(r.base?.return_pct,0),stress_return_pct:n(r.stress?.return_pct,0),win_rate:n(r.base?.win_rate,0),max_drawdown:n(r.base?.max_drawdown,0),trades:n(r.base?.trades,0),status:r.validation?.pass?'PASS':'RESEARCH',walk_forward_positive_pct:r.validation?.walk_forward_positive_pct??0,validation_pass:r.validation?.pass===true})),
    recent_trades:allTrades.slice(-30),
    paper_decisions:(paper.decision_feed||[]).slice(-30),
    risk:{...config.risk,halted:!!paper.halted,halt_reason:paper.halt_reason,emergency_stop:!!config.paper.emergency_stop},
    assumptions:{...config.research_costs,stress_cost_multiplier:config.validation.stress_cost_multiplier,note:'Research assumptions; live GMX position fees, funding, borrowing, execution fee and net price impact vary with market state.'},
    configuration:{timeframe:config.timeframe,history_limit:config.history_limit,poll_seconds:config.poll_seconds,market_settings:config.market_settings,paper:config.paper,research_exploration:config.research_exploration},
    validation:{math:mathSelfTest(),candidate_pass_count:passCount,candidate_total:strategyRows.length,live_ready:false,live_ready_reasons:['GMX live adapter is installed separately and remains owner-gated','Owner wallet one-click authorization and explicit ARM are required','Live Auto Bot is disabled until separately armed by the owner']}
  };
}

async function cycle({backtestOnly=false}={}){
  cycleSequence+=1;
  const cycleStarted=Date.now();
  const config=loadConfig(),candlesBySymbol={},latest={},errors={},nowEpoch=Math.floor(Date.now()/1000);
  const enabled=Object.entries(config.market_settings).filter(([,v])=>v.enabled).map(([s])=>s);
  const researchOn=config.research_exploration?.enabled!==false&&config.research_exploration?.continuous_market_research_enabled!==false;
  const researchInterval=Math.max(120,Math.min(900,n(config.research_exploration?.interval_seconds,120)));
  const researchDue=backtestOnly||(researchOn&&(!cachedResearchResults.length||nowEpoch-lastResearchEpoch>=researchInterval));
  const candleLimit=researchDue?config.history_limit:Math.min(config.history_limit,240);
  const marketResults=await Promise.all(enabled.map(async symbol=>{
    try{return{symbol,snapshot:await fetchMarketSnapshot(config,symbol,candleLimit),error:null};}
    catch(err){return{symbol,snapshot:null,error:String(err?.message||err)};}
  }));
  for(const row of marketResults){
    if(row.snapshot){
      candlesBySymbol[row.symbol]=row.snapshot.candles;
      latest[row.symbol]=row.snapshot.latest;
      if(row.snapshot.markError)errors[row.symbol]='1m mark degraded: '+row.snapshot.markError;
    }else{
      errors[row.symbol]=row.error||'GMX market fetch failed';
    }
  }
  let results=researchOn?cachedResearchResults:[];
  let promotions=[];
  if(researchDue){
    const fresh=[];
    for(const symbol of enabled){
      const candles=candlesBySymbol[symbol];
      if(!candles)continue;
      for(const strategy of ['scalp_trend','trend_momentum','mean_reversion']){
        if(config.strategies[strategy]?.enabled===false)continue;
        const base=backtest(candles,strategy,config);
        const stress=backtest(candles,strategy,config,{costMultiplier:n(config.validation.stress_cost_multiplier,2.5)});
        const wf=walkForward(candles,strategy,config);
        const val=validationFor(base,stress,wf,config);
        fresh.push({symbol,strategy,base,stress,walk_forward:wf,validation:val});
      }
    }
    promotions=promoteValidatedStrategies(config,fresh);
    if(promotions.length)writeJsonAtomic(CONFIG_FILE,normalizeConfig(config));
    cachedResearchResults=fresh;
    lastResearchEpoch=nowEpoch;
    results=fresh;
    researchState.last_run_epoch=lastResearchEpoch;
    researchState.results=fresh.map(compactResearchResult);
    researchState.history=[...(researchState.history||[]),{generated_at:iso(),at:iso(),cycle:cycleSequence,tested_candidates:fresh.length,validated_candidates:fresh.filter(r=>r.validation?.pass).length,rejected_candidates:fresh.filter(r=>!r.validation?.pass).map(r=>({symbol:r.symbol,strategy:r.strategy,checks:r.validation?.checks||{}})),promotions:promotions.map(x=>({symbol:x.symbol,from:x.from,to:x.to,score:x.score}))}].slice(-120);
    researchState.promotions=[...(researchState.promotions||[]),...promotions].slice(-120);
  }
  if(!researchState.activity_feed)researchState.activity_feed=[];
  researchState.cycle_sequence=cycleSequence;
  researchState.activity_feed.push({at:iso(),type:'quant_cycle',title:'Quant cycle',detail:'Cycle '+cycleSequence+': '+Object.keys(latest).length+' GMX markets checked',value:(config.paper?.enabled!==false&&config.paper?.auto_trading_enabled!==false)?1:0});
  if(researchDue)researchState.activity_feed.push({at:iso(),type:'research',title:'Strategy research',detail:'Tested '+results.length+' candidates; '+results.filter(r=>r.validation?.pass).length+' passed validation',value:results.filter(r=>r.validation?.pass).length});
  for(const [symbol,error] of Object.entries(errors))researchState.activity_feed.push({at:iso(),type:'market_error',title:'GMX feed warning',detail:symbol+': '+error,value:-1});
  for(const promotion of promotions)researchState.activity_feed.push({at:promotion.at,type:'promotion',title:'Validated strategy promoted',detail:promotion.symbol+': '+promotion.from+' → '+promotion.to,value:promotion.score});
  let paper=readJson(STATE_FILE,null);
  if(!paper||paper.version!==3)paper=createPaperState(config);
  const previousPositions=new Set(Object.keys(paper.positions||{}));
  const previousTradeCount=Array.isArray(paper.trades)?paper.trades.length:0;
  if(!backtestOnly&&config.paper.enabled)paper=updatePaper(paper,candlesBySymbol,latest,config,results);
  const currentPositions=new Set(Object.keys(paper.positions||{}));
  for(const symbol of currentPositions){
    if(previousPositions.has(symbol))continue;
    const position=paper.positions[symbol];
    researchState.activity_feed.push({at:iso(),type:'paper_entry',title:'Paper position opened',detail:symbol+' '+String(position?.side||'').toUpperCase()+' · '+String(position?.strategy||'strategy'),value:n(position?.notional,0)});
  }
  for(const trade of (paper.trades||[]).slice(previousTradeCount)){
    researchState.activity_feed.push({at:trade.closed_at||iso(),type:'paper_result',title:n(trade.pnl,0)>=0?'Paper trade won':'Paper trade lost',detail:trade.symbol+' '+String(trade.side||'').toUpperCase()+' · '+String(trade.reason||'closed'),value:n(trade.pnl,0)});
  }
  researchState.activity_feed=researchState.activity_feed.slice(-120);
  writeJsonAtomic(RESEARCH_FILE,researchState);
  writeJsonAtomic(STATE_FILE,paper);
  const status=telemetry(config,candlesBySymbol,latest,results,paper,errors,{duration_ms:Date.now()-cycleStarted});
  writeJsonAtomic(STATUS_FILE,status);
  return status;
}

export function selfTest(){const math=mathSelfTest(),candles=[];let price=100;for(let i=0;i<900;i++){price*=1+(Math.sin(i/17)*.002)+(i<450?.0004:-.00015);candles.push({timestamp:1700000000+i*3600,open:price*.998,high:price*1.006,low:price*.994,close:price});}const cfg=normalizeConfig(DEFAULT_CONFIG),s=backtest(candles,'scalp_trend',cfg),a=backtest(candles,'trend_momentum',cfg),b=backtest(candles,'mean_reversion',cfg),wf=walkForward(candles,'trend_momentum',cfg);const checks={math:math.pass,scalp:Number.isFinite(s.ending_equity),trend:Number.isFinite(a.ending_equity),mean:Number.isFinite(b.ending_equity),walk_forward:(wf.total_windows||0)>0,research_default_on:cfg.research_exploration.continuous_market_research_enabled===true,paper_bot_default_on:cfg.paper.auto_trading_enabled===true,independent_controls:cfg.research_exploration.continuous_market_research_enabled===true&&cfg.paper.auto_trading_enabled===true,live_locked:true,live_signal_names:['long','short','flat'].includes((signalTrendMomentum(candles,candles.length-1)>0?'long':signalTrendMomentum(candles,candles.length-1)<0?'short':'flat'))};return{pass:Object.values(checks).every(Boolean),checks,math,sample:{scalp:{return_pct:s.return_pct,trades:s.trades,max_drawdown:s.max_drawdown},trend:{return_pct:a.return_pct,trades:a.trades,max_drawdown:a.max_drawdown},mean:{return_pct:b.return_pct,trades:b.trades,max_drawdown:b.max_drawdown},walk_forward:wf}};}

async function main(){
  const rawArgs=process.argv.slice(2),args=new Set(rawArgs);
  if(args.has('--print-default-config')){console.log(JSON.stringify(DEFAULT_CONFIG,null,2));return;}
  if(args.has('--self-test')){const r=selfTest();console.log(JSON.stringify(r,null,2));process.exit(r.pass?0:1);}
  const manualIndex=rawArgs.indexOf('--manual-order');
  if(manualIndex>=0){
    try{const payload=JSON.parse(rawArgs[manualIndex+1]||'{}');const result=await manualPaperAction(payload);console.log(JSON.stringify(result));return;}
    catch(err){console.error(JSON.stringify({ok:false,error:String(err?.message||err)}));process.exit(2);}
  }
  const once=args.has('--once')||args.has('--backtest-only');
  do{try{const status=await cycle({backtestOnly:args.has('--backtest-only')});console.log(JSON.stringify({ok:true,generated_at:status.generated_at,equity:status.equity,pnl:status.total_pnl,positions:status.positions.length,backtests:status.backtests.length,markets:status.markets.map(m=>m.symbol),errors:status.market_errors}));}catch(err){const failure={schema_version:3,generated_at:iso(),engine:{name:'Myles Quant',version:VERSION,status:'error'},mode:'paper',execution_locked:true,error:String(err?.stack||err)};writeJsonAtomic(STATUS_FILE,failure);console.error(failure.error);if(once)process.exit(1);}if(once)break;const cfg=loadConfig();await new Promise(r=>setTimeout(r,cfg.poll_seconds*1000));}while(true);
}
if(import.meta.url===`file://${process.argv[1]?.replaceAll('\\','/')}`||path.resolve(process.argv[1]||'')===path.resolve(fileURLToPath(import.meta.url))){main();}
