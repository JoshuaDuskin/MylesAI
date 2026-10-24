import test from 'node:test';
import assert from 'node:assert/strict';
import {paperAccounting,liquidationEstimate} from '../quant/paper_accounting.mjs';
import {researchFeeds,normalizeGmx,providerState,researchCandles} from '../quant/research_providers.mjs';
import {normalizeConfig,createPaperState,updatePaper} from '../quant/quant_service.mjs';
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
  updatePaper(s,{'BTC-PERP':[{timestamp:200,open:100,high:100,low:100,close:100},{timestamp:201,open:100,high:100,low:100,close:100}]},{'BTC-PERP':{price:98,timestamp:300}},c,[]);
  assert.equal(Object.keys(s.positions).length,0);assert.equal(s.trades[0].reason,'stop_loss');assert.equal(s.trades[0].closed_at,new Date(300000).toISOString());
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
  assert.equal(opened.positions.length,1);assert.ok(opened.equity_usd<1000);assert.equal(opened.cash_usd,975);
  const closed=simulatePredictionPaper({paper_simulation:opened},[{...m,best_bid:.62,best_ask:.63,outcomes:[{outcome:'Yes',price:.62}]}],{},1001000);
  assert.equal(closed.trades.length,1);assert.ok(closed.trades[0].exit_fee>0);
});
