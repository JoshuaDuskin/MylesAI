const number=(v,f=0)=>Number.isFinite(Number(v))?Number(v):f;
export const RISK_PROFILES={
  conservative:{max_risk_per_trade_pct:.25,max_notional_leverage:1.5,max_drawdown_pct:5,max_concurrent_positions:2},
  balanced:{max_risk_per_trade_pct:.5,max_notional_leverage:3,max_drawdown_pct:8,max_concurrent_positions:2},
  aggressive:{max_risk_per_trade_pct:1,max_notional_leverage:5,max_drawdown_pct:12,max_concurrent_positions:3},
};
export function liquidationEstimate(position, maintenanceMarginPct=.5) {
  const leverage=number(position.leverage,1),entry=number(position.entry);
  if(!(entry>0&&leverage>0))return null;
  // Isolated approximation, not a venue liquidation quote. Includes a fee reserve.
  const distance=Math.max(0,1/leverage-maintenanceMarginPct/100-.001);
  return position.direction>0?Math.max(0,entry*(1-distance)):entry*(1+distance);
}
export function paperAccounting(state,equity) {
  const trades=state.trades||[],positions=Object.values(state.positions||{});
  const unrealized=positions.reduce((sum,p)=>sum+number(p.unrealized_pnl),0);
  const margin=positions.reduce((sum,p)=>sum+number(p.margin_usd,number(p.notional)/Math.max(1,number(p.leverage,1))),0);
  const start=number(state.starting_equity),cash=number(state.cash),realized=number(state.realized_pnl);
  const openFees=positions.reduce((sum,p)=>sum+number(p.entry_fee),0);
  const residual=cash-start-realized+openFees;
  const detailed=trades.filter(t=>Number.isFinite(t.entry_fee)&&Number.isFinite(t.exit_fee));
  const strategyStats={};
  for(const t of trades){const key=t.strategy||'unknown',row=strategyStats[key]??={strategy:key,closed_trades:0,wins:0,losses:0,net_pnl_usd:0};row.closed_trades++;row.net_pnl_usd+=number(t.pnl);if(number(t.pnl)>0)row.wins++;else row.losses++;}
  return {strategy_performance:Object.values(strategyStats),retained_closed_trade_count:trades.length,starting_equity:start,cash,realized_net_pnl:realized,unrealized_pnl:unrealized,open_entry_fees:openFees,
    equity,identity:'equity = cash + unrealized P&L; cash includes paid entry fees',
    reconciliation_residual:residual,reconciled:Math.abs(residual)<.05,
    closed_trade_count:number(state.wins)+number(state.losses),winning_closed_trades:number(state.wins),losing_closed_trades:number(state.losses),
    win_rate_basis:'closed trades only; unrealized gains are not wins',
    closed_fees_usd:detailed.reduce((s,t)=>s+t.entry_fee+t.exit_fee,0),
    modeled_carrying_cost_usd:detailed.reduce((s,t)=>s+number(t.holding_cost),0),
    historical_cost_breakdown_complete:detailed.length===trades.length,
    actual_funding_payments:null,funding_note:'Paper carrying-cost reserve is modeled; actual venue funding is not booked as observed funding.',
    margin_used_usd:margin,available_margin_usd:Math.max(0,equity-margin),margin_utilization_pct:equity>0?margin/equity*100:null,
    gross_notional_usd:positions.reduce((s,p)=>s+number(p.notional),0),margin_mode:'isolated_simulation',cross_margin_supported:false};
}
