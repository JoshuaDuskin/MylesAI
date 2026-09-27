import json
import random
from datetime import datetime, timedelta

# Load config
with open(r'C:\Users\Joshu\AppData\Local\MylesAI\quant\quant_config.json', 'r') as f:
    config = json.load(f)

symbol = config['paper']['symbol']
strategy = config['paper']['strategy']
max_risk_pct = config['risk']['max_risk_per_trade_pct']
stop_loss_pct = config['risk']['stop_loss_pct']
take_profit_pct = config['risk']['take_profit_pct']

print(f"Initializing simulation for {symbol} using strategy: {strategy}")
print("Generating synthetic market data and trade signals...")

# Simulate 100 candles of OHLCV data
candles = []
price = 65000.0  # Starting BTC price
for i in range(100):
    timestamp = datetime.now() - timedelta(hours=100-i)
    change = random.uniform(-0.02, 0.02)
    close = price * (1 + change)
    open_price = close * (1 - random.uniform(0, 0.01))
    high = max(open_price, close) * (1 + random.uniform(0, 0.005))
    low = min(open_price, close) * (1 - random.uniform(0, 0.005))
    volume = random.uniform(100, 500)
    candles.append({
        'timestamp': timestamp.isoformat(),
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })
    price = close

# Simulate strategy signals and trades
trades = []
current_position = 0.0
entry_price = None
max_drawdown = 0.0
peak_equity = 10000.0

for i, candle in enumerate(candles):
    # Simple trend signal: buy if close > open, sell if close < open
    signal = 'buy' if candle['close'] > candle['open'] else 'sell'
    
    if current_position == 0 and signal == 'buy':
        entry_price = candle['close']
        size = (10000 * max_risk_pct / 100) / entry_price
        current_position = size
        trades.append({
            'type': 'entry',
            'price': entry_price,
            'size': size,
            'timestamp': candle['timestamp']
        })
    elif current_position > 0 and signal == 'sell':
        pnl_pct = (candle['close'] - entry_price) / entry_price
        exit_price = candle['close']
        trades.append({
            'type': 'exit',
            'price': exit_price,
            'size': current_position,
            'pnl_pct': pnl_pct * 100,
            'timestamp': candle['timestamp']
        })
        current_position = 0
        entry_price = None
    
    # Update equity and drawdown
    equity = 10000 + (current_position * (candle['close'] - entry_price)) if current_position > 0 else 10000
    peak_equity = max(peak_equity, equity)
    drawdown = (peak_equity - equity) / peak_equity * 100
    max_drawdown = max(max_drawdown, drawdown)

print(f"Simulation complete.")
print(f"Total trades executed: {len(trades)}")
print(f"Max drawdown observed: {max_drawdown:.2f}%")
print(f"Final equity: {10000 + (current_position * (candles[-1]['close'] - entry_price)) if current_position > 0 else 10000:.2f}")

# Save results
with open(r'C:\Users\Joshu\AppData\Local\MylesAI\quant\simulation_results.json', 'w') as f:
    json.dump({'trades': trades, 'max_drawdown': max_drawdown}, f)
print("Results saved to simulation_results.json")