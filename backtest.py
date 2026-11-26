"""
Mean Reversion Backtesting Engine
Replicates the C++ trading system logic exactly, then outputs
all metrics and chart data as JSON for the dashboard.
"""

import csv
import math
import json
import sys
import os

# ─── Data Loading ───────────────────────────────────────────────

def load_csv(filename):
    candles = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                candles.append({
                    'date': row['Date'],
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(float(row['Volume'])),
                })
            except (ValueError, KeyError):
                continue
    return candles

# ─── Indicators ─────────────────────────────────────────────────

def calculate_indicators(candles, window=20):
    n = len(candles)
    result = [{'sma': float('nan'), 'sd': float('nan'), 'zScore': float('nan')} for _ in range(n)]

    if window < 2 or n < window:
        return result

    for i in range(window - 1, n):
        closes = [candles[j]['close'] for j in range(i - window + 1, i + 1)]
        sma = sum(closes) / window

        variance = sum((c - sma) ** 2 for c in closes) / (window - 1)
        sd = math.sqrt(variance)

        z_score = float('nan')
        if sd > 0.0:
            z_score = (candles[i]['close'] - sma) / sd

        result[i] = {'sma': sma, 'sd': sd, 'zScore': z_score}

    return result

# ─── Strategy ───────────────────────────────────────────────────

def generate_signal(z_score, has_position, buy_threshold=-2.0,
                    risk_exit_threshold=-3.0, sell_threshold=0.0):
    if not math.isfinite(z_score):
        return 'HOLD'
    if has_position and z_score <= risk_exit_threshold:
        return 'SELL'
    if has_position and z_score >= sell_threshold:
        return 'SELL'
    if not has_position and z_score <= buy_threshold and z_score > risk_exit_threshold:
        return 'BUY'
    return 'HOLD'

# ─── Paper Trader ───────────────────────────────────────────────

class PaperTrader:
    def __init__(self, capital=100000.0, allocation=0.10,
                 cost_rate=0.001, slip_rate=0.0005):
        self.initial_capital = capital
        self.cash_balance = capital
        self.allocation_percent = allocation
        self.transaction_cost_rate = cost_rate
        self.slippage_rate = slip_rate

        self.has_position = False
        self.quantity = 0
        self.entry_price = 0.0
        self.entry_cost = 0.0
        self.entry_date = ''

        self.completed_trades = []
        self.equity_history = []

    def process_signal(self, signal, date, market_price):
        if not math.isfinite(market_price) or market_price <= 0.0:
            return

        if signal == 'BUY' and not self.has_position:
            self.entry_price = market_price * (1.0 + self.slippage_rate)
            allocated_cash = self.cash_balance * self.allocation_percent
            self.quantity = int(math.floor(
                allocated_cash / (self.entry_price * (1.0 + self.transaction_cost_rate))
            ))
            if self.quantity <= 0:
                return
            self.entry_cost = self.quantity * self.entry_price * self.transaction_cost_rate
            purchase_amount = self.quantity * self.entry_price
            self.cash_balance -= purchase_amount + self.entry_cost
            self.entry_date = date
            self.has_position = True

        elif signal == 'SELL' and self.has_position:
            exit_price = market_price * (1.0 - self.slippage_rate)
            exit_cost = self.quantity * exit_price * self.transaction_cost_rate
            sale_amount = self.quantity * exit_price
            self.cash_balance += sale_amount - exit_cost

            gross_pnl = (exit_price - self.entry_price) * self.quantity
            total_costs = self.entry_cost + exit_cost

            self.completed_trades.append({
                'entryDate': self.entry_date,
                'exitDate': date,
                'quantity': self.quantity,
                'entryPrice': self.entry_price,
                'exitPrice': exit_price,
                'grossProfitLoss': gross_pnl,
                'transactionCosts': total_costs,
                'netProfitLoss': gross_pnl - total_costs,
            })
            self.quantity = 0
            self.has_position = False

    def record_equity(self, date, market_price):
        market_value = self.quantity * market_price if self.has_position else 0.0
        self.equity_history.append({
            'date': date,
            'cash': self.cash_balance,
            'marketValue': market_value,
            'totalEquity': self.cash_balance + market_value,
        })

    def get_equity(self, market_price):
        if not self.has_position:
            return self.cash_balance
        return self.cash_balance + self.quantity * market_price


# ─── Main Backtest ──────────────────────────────────────────────

def run_backtest(csv_path):
    candles = load_csv(csv_path)
    if not candles:
        return {'error': 'No market data found'}

    # Split data 70/30
    split_index = int(len(candles) * 0.70)
    training_data = candles[:split_index]
    testing_data = candles[split_index:]

    window = 20
    if len(training_data) < window or len(testing_data) < 2:
        return {'error': 'Insufficient data'}

    # Prepare test input (include last 19 training candles for warm-up)
    test_input = training_data[-(window - 1):] + testing_data

    # Calculate indicators
    test_indicators = calculate_indicators(test_input, window)

    # Create trader
    initial_capital = 100000.0
    trader = PaperTrader(initial_capital, 0.10, 0.001, 0.0005)

    # Record initial equity
    trader.record_equity(testing_data[0]['date'], testing_data[0]['close'])

    # Run strategy
    for i in range(window - 1, len(test_input) - 1):
        signal = generate_signal(
            test_indicators[i]['zScore'],
            trader.has_position
        )
        trader.process_signal(
            signal,
            test_input[i + 1]['date'],
            test_input[i + 1]['open']
        )
        if i + 1 != len(test_input) - 1:
            trader.record_equity(
                test_input[i + 1]['date'],
                test_input[i + 1]['close']
            )

    # Liquidate remaining position
    if trader.has_position:
        trader.process_signal('SELL', test_input[-1]['date'], test_input[-1]['close'])

    trader.record_equity(test_input[-1]['date'], test_input[-1]['close'])

    # ─── Calculate Metrics ──────────────────────────────────────

    equity_history = trader.equity_history
    trades = trader.completed_trades

    # Total Return
    final_equity = equity_history[-1]['totalEquity']
    total_return = ((final_equity - initial_capital) / initial_capital) * 100.0

    # Daily returns
    daily_returns = []
    for i in range(1, len(equity_history)):
        prev = equity_history[i - 1]['totalEquity']
        curr = equity_history[i]['totalEquity']
        if prev > 0:
            daily_returns.append((curr - prev) / prev)

    # Sharpe Ratio (annualized, 0 risk-free)
    sharpe_ratio = 0.0
    if len(daily_returns) > 1:
        mean_ret = sum(daily_returns) / len(daily_returns)
        var = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_std = math.sqrt(var)
        if daily_std > 0:
            sharpe_ratio = (mean_ret / daily_std) * math.sqrt(252)

    # Maximum Drawdown
    peak = equity_history[0]['totalEquity']
    max_drawdown = 0.0
    drawdown_series = []
    for point in equity_history:
        peak = max(peak, point['totalEquity'])
        dd = (peak - point['totalEquity']) / peak
        max_drawdown = max(max_drawdown, dd)
        drawdown_series.append({
            'date': point['date'],
            'drawdown': -dd * 100  # negative percentage
        })

    # Win Rate & Profit Factor
    winning_trades = [t for t in trades if t['netProfitLoss'] > 0]
    losing_trades = [t for t in trades if t['netProfitLoss'] <= 0]
    win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0

    gross_profits = sum(t['netProfitLoss'] for t in winning_trades)
    gross_losses = abs(sum(t['netProfitLoss'] for t in losing_trades))
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else float('inf')

    # Average trade metrics
    avg_win = (gross_profits / len(winning_trades)) if winning_trades else 0
    avg_loss = (gross_losses / len(losing_trades)) if losing_trades else 0

    # Buy-and-Hold Return
    bnh_initial = testing_data[0]['close']
    bnh_final = testing_data[-1]['close']
    bnh_return = ((bnh_final - bnh_initial) / bnh_initial) * 100.0

    # Buy-and-Hold equity curve (for benchmark comparison)
    bnh_equity = []
    for candle in testing_data:
        bnh_eq = initial_capital * (candle['close'] / bnh_initial)
        bnh_equity.append({
            'date': candle['date'],
            'totalEquity': bnh_eq
        })

    # ─── Build Output ───────────────────────────────────────────

    output = {
        'summary': {
            'totalCandles': len(candles),
            'trainingCandles': len(training_data),
            'testingCandles': len(testing_data),
            'testStartDate': testing_data[0]['date'],
            'testEndDate': testing_data[-1]['date'],
            'initialCapital': initial_capital,
            'finalEquity': round(final_equity, 2),
        },
        'metrics': {
            'totalReturn': round(total_return, 4),
            'sharpeRatio': round(sharpe_ratio, 4),
            'maxDrawdown': round(max_drawdown * 100, 4),
            'winRate': round(win_rate, 2),
            'totalTrades': len(trades),
            'winningTrades': len(winning_trades),
            'losingTrades': len(losing_trades),
            'profitFactor': round(profit_factor, 4) if profit_factor != float('inf') else 'Infinity',
            'buyAndHoldReturn': round(bnh_return, 4),
            'avgWin': round(avg_win, 2),
            'avgLoss': round(avg_loss, 2),
            'excessReturn': round(total_return - bnh_return, 4),
        },
        'equityCurve': [{'date': p['date'], 'equity': round(p['totalEquity'], 2)} for p in equity_history],
        'drawdownSeries': [{'date': d['date'], 'drawdown': round(d['drawdown'], 4)} for d in drawdown_series],
        'benchmarkCurve': [{'date': p['date'], 'equity': round(p['totalEquity'], 2)} for p in bnh_equity],
        'trades': [{
            'entryDate': t['entryDate'],
            'exitDate': t['exitDate'],
            'quantity': t['quantity'],
            'entryPrice': round(t['entryPrice'], 2),
            'exitPrice': round(t['exitPrice'], 2),
            'netPnL': round(t['netProfitLoss'], 2),
        } for t in trades],
    }

    return output


if __name__ == '__main__':
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'data/RELIANCE.csv'
    result = run_backtest(csv_path)
    print(json.dumps(result))
