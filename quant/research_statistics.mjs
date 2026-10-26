// Descriptive statistics, never a profitability or probability guarantee.
export function researchStatistics(trades,curve,periodSeconds){
 const pnl=trades.map(t=>Number(t.pnl)).filter(Number.isFinite),wins=pnl.filter(x=>x>0),losses=pnl.filter(x=>x<0),profit=wins.reduce((a,x)=>a+x,0),loss=-losses.reduce((a,x)=>a+x,0);
 const returns=curve.slice(1).map((p,i)=>curve[i].equity>0?p.equity/curve[i].equity-1:null).filter(Number.isFinite);
 const regular=periodSeconds>0&&curve.slice(1).every((p,i)=>Math.abs(p.timestamp-curve[i].timestamp-periodSeconds)<1);
 const meaningful=pnl.length>=30&&returns.length>=100&&regular;
 const mean=returns.length?returns.reduce((a,x)=>a+x,0)/returns.length:0;
 const sd=returns.length>1?Math.sqrt(returns.reduce((a,x)=>a+(x-mean)**2,0)/(returns.length-1)):0;
 const downside=returns.length?Math.sqrt(returns.reduce((a,x)=>a+Math.min(0,x)**2,0)/returns.length):0;
 const annual=periodSeconds>0?Math.sqrt(365*86400/periodSeconds):0;
 return {expectancy_usd:pnl.length?pnl.reduce((a,x)=>a+x,0)/pnl.length:null,profit_factor:loss>0?profit/loss:null,
 average_win_usd:wins.length?profit/wins.length:null,average_loss_usd:losses.length?loss/losses.length:null,
 sharpe:meaningful&&sd>0?mean/sd*annual:null,sortino:meaningful&&downside>0?mean/downside*annual:null,
 ratio_basis:'zero reference rate; annualized evenly spaced crypto equity returns; descriptive only',
 sample_quality:pnl.length<30?'limited closed-trade sample':'descriptive sample; not proof of future return',closed_trade_sample:pnl.length};
}
