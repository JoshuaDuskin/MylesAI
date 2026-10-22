const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('node:path').join(__dirname,'..','index.html'),'utf8');
for(const match of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(match[1]);
const context={state:{statusSource:'LIVE TOWER',status:{},quantConfig:{paper:{auto_trading_enabled:false}}},trading:s=>s.trading,
 objOr:(v,d)=>v&&typeof v==='object'?v:d,num:v=>v==null?null:Number(v),bool:Boolean,
 first:(obj,paths,fallback)=>{for(const path of paths){let value=obj;for(const key of path.split('.'))value=value?.[key];if(value!=null)return value;}return fallback;}};
vm.createContext(context);
for(const name of ['tradeMetrics','quantControlFlags']){const line=html.split('\n').find(line=>line.trim().startsWith('function '+name+'('));assert.ok(line);vm.runInContext(line,context);}
const raw={_verified_source:'data/trading_status.json',account_type:'SIMULATED PAPER',mode:'paper',_verified:false,_telemetry_state:'stale',engine:{status:'running'},markets:[{symbol:'BTC'}],equity:10060,total_pnl:60,controls:{paper_trading_bot:{enabled:true}}};
context.state.status.trading=raw;
assert.equal(context.tradeMetrics().verified,false);assert.equal(context.tradeMetrics().pnl,60);
raw._telemetry_state='paused_game_mode';assert.equal(context.tradeMetrics().paused,true);assert.equal(context.tradeMetrics().verified,false);
raw._verified=true;raw._telemetry_state='live';assert.equal(context.tradeMetrics().verified,true);
assert.equal(context.quantControlFlags().bot,true,'Live telemetry beats stale settings');
console.log('Dashboard freshness and control-state regression checks passed');

// Exercise the actual rendering tree with research/open-position telemetry.
const makeNode=()=>({classList:{add(){},remove(){},toggle(){}},style:{},dataset:{},addEventListener(){},setAttribute(){},querySelector(){return null},querySelectorAll(){return[]},getContext(){return null},getBoundingClientRect(){return{width:900,height:300}},replaceChildren(){},appendChild(){},value:'',textContent:'',innerHTML:''});
const nodes={};const document={getElementById:id=>nodes[id]??=makeNode(),querySelector:()=>null,querySelectorAll:()=>[],addEventListener(){},documentElement:makeNode(),body:makeNode()};
const full={document,console,URLSearchParams,URL,Intl,Date,setTimeout:()=>0,clearTimeout(){},setInterval:()=>0,clearInterval(){},requestAnimationFrame:f=>f(),location:{search:'',origin:'https://example.com',pathname:'/'},localStorage:{getItem:()=>null,setItem(){}},navigator:{},window:{innerWidth:900,addEventListener(){},devicePixelRatio:1}};
vm.createContext(full);let script=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map(x=>x[1]).find(x=>x.includes('statusSource:'));
script=script.replace(/\}\)\(\);\s*$/, 'globalThis.testing={state,renderTrading,openPairModal,dashboardUrl};drawChart=()=>{};drawMarketCandles=()=>{};})();');vm.runInContext(script,full);
full.testing.state.status={trading:{...raw,research_tournament:{enabled:true,pnl:60,books:[{strategy:'trend',paper_pnl:60,open_position:{side:'long',notional:100,leverage:1,unrealized_pnl:60}}]}}};
full.testing.state.statusSource='LIVE TOWER';full.testing.renderTrading();assert.equal(nodes.tournamentStatus.textContent,'AUTO SIM');assert.notEqual(nodes.tournamentPnl.textContent,'—');
assert.equal(full.testing.dashboardUrl(),'https://example.com/');full.testing.openPairModal();
assert.ok(!html.includes('initGuestChat'));assert.ok(!html.includes('id="guestShell"'));
console.log('Full dashboard render and single household dashboard checks passed');
