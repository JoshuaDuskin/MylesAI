import test from 'node:test';
import {researchStatistics} from '../quant/research_statistics.mjs';
import assert from 'node:assert/strict';
import {paperAccounting,liquidationEstimate} from '../quant/paper_accounting.mjs';
import {researchFeeds,normalizeGmx,providerState,researchCandles,completedCandles} from '../quant/research_providers.mjs';
import {normalizeConfig,createPaperState,updatePaper,validatePaperOrder,backtest,higherTimeframeBias} from '../quant/quant_service.mjs';
import {simulatePredictionPaper} from '../quant/polymarket_paper_service.mjs';

test('positive unrealized P&L does not create a winning closed trade',()=>{
  const a=paperAccounting({starting_equity:10000,cash:9997,realized_pnl:-1,wins:0,losses:5,trades:[{pnl:-1}],positions:{BTC:{entry_fee:2,unrealized_pnl:78,notional:1000,margin_usd:500}}},10075);
  assert.equal(a.reconciled,true);assert.equal(a.winning_closed_trades,0);assert.equal(a.unrealized_pnl,78);
  assert.equal(a.historical_cost_breakdown_complete,false);assert.equal(a.actual_funding_payments,null);
});
test('isolated liquidation estimates are directional and approximate',()=>{
  assert.ok(liquidationEstimate({entry:100,leverage:5,direction:1})<100);
  assert.ok(liquidationEstimate({entry:100,leverage:5,direction:-1})>100);
});
test('risk normalization never enables real execution or cross margin',()=>{
  const c=normalizeConfig({risk:{max_notional_leverage:100,margin_mode:'cross',trailing_stop_pct:100},live_execution:{enabled:true}});
  assert.equal(c.risk.max_notional_leverage,20);assert.equal(c.risk.margin_mode,'isolated');
  assert.equal(c.risk.trailing_stop_pct,15);assert.equal(c.live_execution.enabled,false);
});
test('paper stops react to current marks even without a new strategy candle',()=>{
  const c=normalizeConfig({market_settings:{'BTC-PERP':{enabled:true},'ETH-PERP':{enabled:false},'SOL-PERP':{enabled:false}}});
  const s=createPaperState(c);s.positions['BTC-PERP']={symbol:'BTC-PERP',entry:100,direction:1,side:'long',notional:100,units:1,margin_usd:100,leverage:1,entry_fee:0,opened_ts:100,stop:99,target:105};
  s.last_candle_ts['BTC-PERP']=200;
  updatePaper(s,{'BTC-PERP':[{timestamp:200,open:100,high:100,low:100,close:100},{timestamp:201,open:100,high:100,low:100,close:100}]},{'BTC-PERP':{price:98,timestamp:Math.floor(Date.now()/1000)}},c,[]);
  assert.equal(Object.keys(s.positions).length,0);assert.equal(s.trades[0].reason,'stop_loss');assert.ok(Math.abs(Date.parse(s.trades[0].closed_at)-Date.now())<2000);
});
test('GMX fixed-point quotes use the documented market ticker schema',()=>{
  const r=normalizeGmx([{symbol:'BTC/USD [BTC-USDC]',markPrice:String(80000e30),minPrice:String(79999e30),maxPrice:String(80001e30)}]);
  assert.equal(r.BTC.price,80000);assert.ok(r.BTC.spread_bps>0);
});
test('provider failures back off, cached successes expire, recovery needs a real response',async()=>{
  let calls=0;const now=Date.now();const failed=async()=>{calls++;throw new Error('test outage');};
  const first=await researchFeeds({fetcher:failed,now});assert.equal(first.health.gmx.available,false);
  const initial=calls;await researchFeeds({fetcher:failed,now:now+1000});assert.equal(calls,initial);
  assert.equal(providerState.gmx.consecutive_failures,1);
  const fake=async url=>({ok:true,json:async()=>{
    if(url.includes('/markets/tickers'))return[{symbol:'BTC/USD [BTC-USDC]',markPrice:String(80000e30),minPrice:String(79999e30),maxPrice:String(80001e30)}];
    if(url.includes('kraken'))return{error:[],result:{XXBTZUSD:{a:['80001'],b:['79999'],c:['80000']}}};
    return{price:'80000',bid:'79999',ask:'80001',time:new Date(now+20000).toISOString()};
  }});
  const recovered=await researchFeeds({fetcher:fake,now:now+20000});assert.equal(recovered.health.gmx.available,true);assert.equal(recovered.health.gmx.error,null);
  const stale=await researchFeeds({fetcher:failed,now:now+240000});assert.equal(stale.health.gmx.available,false);
});
test('only completed and current external candles are research evidence',async()=>{
  const now=Date.now(),hour=Math.floor(now/3600000)*3600;
  const data=Array.from({length:100},(_,i)=>[hour-i*3600,99,101,100,100,1000]);
  const rows=await researchCandles('BTC',{now,fetcher:async()=>({ok:true,json:async()=>data})});
  assert.equal(rows.length,99);assert.ok(rows.at(-1).timestamp+3600<=now/1000);
});
test('prediction paper waits for evidence and uses observed quotes with costs',()=>{
  const m={id:'test',liquidity_usd:20000,best_ask:.55,best_bid:.54,spread:.01,outcomes:[{outcome:'Yes',price:.55}]};
  assert.equal(simulatePredictionPaper({paper_equity_usd:1000},[m],{},1000000).positions.length,0);
  const h={test:[{outcomes:[{outcome:'Yes',price:.50}]},{outcomes:[{outcome:'Yes',price:.52}]},{outcomes:[{outcome:'Yes',price:.55}]}]};
  const opened=simulatePredictionPaper({paper_equity_usd:1000},[m],h,1000000);
  const paused=simulatePredictionPaper({paper_equity_usd:1000},[m],h,1000000,false);
  assert.equal(paused.positions.length,0,'Paused prediction paper must not enter');
  assert.equal(paused.cash_usd,1000);
  assert.equal(opened.positions.length,1);assert.ok(opened.equity_usd<1000);assert.equal(opened.cash_usd,975);
  const closed=simulatePredictionPaper({paper_simulation:opened},[{...m,best_bid:.62,best_ask:.63,outcomes:[{outcome:'Yes',price:.62}]}],{},1001000);
  const managed=simulatePredictionPaper({paper_simulation:opened},[{...m,best_bid:.62,best_ask:.63,outcomes:[{outcome:'Yes',price:.62}]}],{},1001000,false);
  assert.equal(managed.trades.length,1,'Paused entries must still manage an existing position');
  assert.equal(closed.trades.length,1);assert.ok(closed.trades[0].exit_fee>0);
});

test('completed candles reject malformed bars and deduplicate timestamps',()=>{
  const rows=completedCandles([[60,99,101,100,100,1],[60,99,101,100,100,2],[120,101,99,100,100,1],[180,99,101,100,100,-1]],60,300000);
  assert.equal(rows.length,1);assert.equal(rows[0].volume,2);
});
test('four-hour research aggregates only contiguous completed hourly observations',async()=>{
  const now=Date.now(),hour=Math.floor(now/14400000)*14400;
  const data=Array.from({length:320},(_,i)=>[hour-(i+1)*3600,99,101,100,100,10]);
  const rows=await researchCandles('ETH',{timeframe:'4h',now,fetcher:async()=>({ok:true,json:async()=>data})});
  assert.equal(rows.length,80);assert.equal(rows[0].volume,40);assert.ok(rows.at(-1).timestamp+14400<=now/1000);
});
test('gapped historical samples are rejected instead of fabricating missing candles',async()=>{
  const now=Date.now(),t=Math.floor(now/300000)*300;
  const data=Array.from({length:100},(_,i)=>[t-(i+1)*300,99,101,100,100,10]).filter((_,i)=>i!==45);
  await assert.rejects(researchCandles('SOL',{timeframe:'5m',now,fetcher:async()=>({ok:true,json:async()=>data})}),/Gapped/);
});
test('disconnected execution feed cannot open from cached strategy candles',()=>{
  const c=normalizeConfig({market_settings:{'BTC-PERP':{enabled:true},'ETH-PERP':{enabled:false},'SOL-PERP':{enabled:false}}}),s=createPaperState(c);
  const now=Math.floor(Date.now()/1000),bars=Array.from({length:100},(_,i)=>({timestamp:now-10000+i*60,open:100+i,close:100+i,low:99+i,high:101+i}));
  updatePaper(s,{'BTC-PERP':bars},{},c,[]);
  assert.equal(Object.keys(s.positions).length,0);assert.ok(s.decision_feed.some(r=>r.reason==='missing_or_stale_execution_mark'));
});

test('failed paper orders enforce fee-inclusive available margin, position cap and risk budget',()=>{
  const config=normalizeConfig({risk:{max_market_allocation_pct:100,max_risk_per_trade_pct:5,max_notional_leverage:5,max_position_usd:250}});
  const order={equity:1000,usedMargin:0,margin:100,leverage:2,stopPct:1,openCount:0,config};
  assert.equal(validatePaperOrder(order).notional,200);
  assert.throws(()=>validatePaperOrder({...order,usedMargin:900}),/Insufficient/);
  assert.throws(()=>validatePaperOrder({...order,openCount:config.risk.max_concurrent_positions}),/concurrent/);
  assert.throws(()=>validatePaperOrder({...order,margin:200}),/risk limits/);
  assert.throws(()=>validatePaperOrder({...order,margin:NaN}),/Invalid/);
});

test('explicit minute windows avoid stale provider default-range responses',async()=>{
  const now=Date.now(),minute=Math.floor(now/60000)*60;
  const fresh=Array.from({length:100},(_,i)=>[minute-(i+1)*60,99,101,100,100,1]);
  const stale=fresh.map(r=>[r[0]-1200,...r.slice(1)]);
  const rows=await researchCandles('XRP',{timeframe:'1m',now,fetcher:async url=>({ok:true,json:async()=>url.includes('&start=')&&url.includes('&end=')?fresh:stale})});
  assert.equal(rows.at(-1).timestamp,minute-60);
});

test('research statistics do not invent confidence or zero profit factor from no evidence',()=>{
 const empty=researchStatistics([],[],60);assert.equal(empty.expectancy_usd,null);assert.equal(empty.profit_factor,null);assert.equal(empty.sharpe,null);
 const small=researchStatistics([{pnl:20},{pnl:-10}],[{timestamp:0,equity:1000},{timestamp:60,equity:1010}],60);assert.equal(small.expectancy_usd,5);assert.equal(small.profit_factor,2);assert.equal(small.sharpe,null);
});
test('drawdown includes the starting account before trading costs are deducted',()=>{
 const config=normalizeConfig({timeframe:'1h'}),bars=Array.from({length:100},(_,i)=>({timestamp:1700000000+i*3600,open:100+i*.1,close:100+i*.1,high:101+i*.1,low:99+i*.1}));
 const result=backtest(bars,'trend_momentum',config);assert.equal(result.equity_curve[0].equity,config.starting_equity);
});
test('per-strategy exposure cannot exceed an explicitly configured cap',()=>{
 const config=normalizeConfig({risk:{max_strategy_exposure_pct:20,max_position_usd:1000,max_market_allocation_pct:100,max_risk_per_trade_pct:5,max_notional_leverage:5}});
 const order={equity:1000,usedMargin:0,margin:50,leverage:2,stopPct:1,openCount:0,config,strategyExposure:150};
 assert.throws(()=>validatePaperOrder(order),/strategy exposure/);
 assert.equal(validatePaperOrder({...order,strategyExposure:0}).notional,100);
});

test('higher-timeframe confirmation cannot read a candle before it closes',()=>{
 const bars=Array.from({length:60},(_,i)=>({timestamp:i*3600,close:100+i}));
 const asOf=50*3600,before=higherTimeframeBias(bars,3600,asOf);assert.equal(before,1);
 const futureChanged=bars.map((r,i)=>i>=50?{...r,close:1}:r);
 assert.equal(higherTimeframeBias(futureChanged,3600,asOf),before);
 assert.equal(higherTimeframeBias(bars,3600,49*3600),0);
});
