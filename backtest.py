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
import webbrowser
from pathlib import Path

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

    # Buy-and-Hold Sharpe & Max Drawdown
    bnh_rets = [
        (bnh_equity[i]['totalEquity'] - bnh_equity[i - 1]['totalEquity']) / bnh_equity[i - 1]['totalEquity']
        for i in range(1, len(bnh_equity))
        if bnh_equity[i - 1]['totalEquity'] > 0
    ]
    bnh_sharpe = 0.0
    if len(bnh_rets) > 1:
        bnh_mean = sum(bnh_rets) / len(bnh_rets)
        bnh_var = sum((r - bnh_mean) ** 2 for r in bnh_rets) / (len(bnh_rets) - 1)
        bnh_std = math.sqrt(bnh_var)
        if bnh_std > 0:
            bnh_sharpe = (bnh_mean / bnh_std) * math.sqrt(252)

    bnh_peak = bnh_equity[0]['totalEquity']
    bnh_max_dd = 0.0
    for point in bnh_equity:
        bnh_peak = max(bnh_peak, point['totalEquity'])
        bnh_max_dd = max(bnh_max_dd, (bnh_peak - point['totalEquity']) / bnh_peak)

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
            'bnhFinalEquity': round(bnh_equity[-1]['totalEquity'], 2),
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
            'bnhSharpe': round(bnh_sharpe, 4),
            'bnhMaxDrawdown': round(bnh_max_dd * 100, 4),
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


def generate_dashboard_html(result, output_path='dashboard.html'):
    data_json = json.dumps({
        'summary': result['summary'],
        'metrics': result['metrics'],
        'equity': [{'d': p['date'], 'v': p['equity']} for p in result['equityCurve']],
        'drawdown': [{'d': p['date'], 'v': p['drawdown']} for p in result['drawdownSeries']],
        'benchmark': [{'d': p['date'], 'v': p['equity']} for p in result['benchmarkCurve']],
        'trades': result['trades'],
    })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mean Reversion Backtest Dashboard</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 24px;
      background: #0f172a; color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .container {{ max-width: 1080px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }}
    .header {{ display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px; padding-bottom: 14px; border-bottom: 1px solid #334155; }}
    .header h1 {{ margin: 0; font-size: 20px; }}
    .sub {{ margin: 4px 0 0; font-size: 12px; color: #94a3b8; }}
    .badge {{ padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; font-family: monospace; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 14px 16px; }}
    .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8; }}
    .val {{ font-size: 22px; font-weight: 700; margin-top: 6px; font-family: monospace; }}
    .hint {{ font-size: 11px; color: #94a3b8; margin-top: 4px; }}
    .pos {{ color: #22c55e; }}
    .neg {{ color: #ef4444; }}
    .chart-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 8px; flex-wrap: wrap; }}
    .chart-head h2 {{ margin: 0; font-size: 15px; }}
    .readout {{ font-size: 12px; font-family: monospace; color: #94a3b8; }}
    canvas {{ display: block; width: 100%; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; font-family: monospace; }}
    th, td {{ padding: 9px 12px; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ background: #0f172a; color: #94a3b8; font-weight: 600; }}
    tr:hover td {{ background: #263449; }}
    .right {{ text-align: right; }}
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>Mean Reversion Backtest Results</h1>
      <p class="sub" id="subtitle"></p>
    </div>
    <span class="badge" id="excessBadge"></span>
  </div>

  <div class="grid" id="metricsGrid"></div>

  <div class="card">
    <div class="chart-head">
      <div>
        <h2>1. Equity Curve</h2>
        <p class="sub">Portfolio value over time</p>
      </div>
      <span class="readout" id="readout-equity">Hover chart for values</span>
    </div>
    <canvas id="canvas-equity" height="220"></canvas>
  </div>

  <div class="card">
    <div class="chart-head">
      <div>
        <h2>2. Drawdown Chart</h2>
        <p class="sub">Portfolio decline from peak equity (%)</p>
      </div>
      <span class="readout" id="readout-drawdown">Hover chart for values</span>
    </div>
    <canvas id="canvas-drawdown" height="200"></canvas>
  </div>

  <div class="card">
    <div class="chart-head">
      <div>
        <h2>3. Benchmark Comparison (Mean Reversion vs Buy &amp; Hold)</h2>
        <p class="sub">Strategy equity vs passive Buy &amp; Hold</p>
      </div>
      <span class="readout" id="readout-benchmark">Hover chart for values</span>
    </div>
    <canvas id="canvas-benchmark" height="230"></canvas>
  </div>

  <div class="card" style="padding:0; overflow:hidden;">
    <div style="padding:14px 16px; border-bottom:1px solid #334155;">
      <h2 style="margin:0; font-size:15px;">Completed Trades</h2>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead>
          <tr><th>#</th><th>Entry Date</th><th>Exit Date</th><th>Qty</th><th>Entry</th><th>Exit</th><th class="right">Net P&amp;L</th></tr>
        </thead>
        <tbody id="tradeRows"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const DATA = {data_json};
const s = DATA.summary, m = DATA.metrics;

document.getElementById('subtitle').textContent =
  `Testing Period: ${{s.testStartDate}} -> ${{s.testEndDate}} (${{s.testingCandles}} days · 70/30 split of ${{s.totalCandles}} candles) · Initial Capital: ₹${{s.initialCapital.toLocaleString()}}`;

const excessBadge = document.getElementById('excessBadge');
excessBadge.textContent = `Excess Return: ${{m.excessReturn >= 0 ? '+' : ''}}${{m.excessReturn.toFixed(2)}}%`;
excessBadge.style.background = m.excessReturn >= 0 ? '#16a34a' : '#dc2626';
excessBadge.style.color = '#ffffff';

const cards = [
  {{ label: 'Total Return', val: `${{m.totalReturn >= 0 ? '+' : ''}}${{m.totalReturn.toFixed(2)}}%`, cls: m.totalReturn >= 0 ? 'pos' : 'neg', hint: `₹${{s.finalEquity.toLocaleString()}} final equity` }},
  {{ label: 'Sharpe Ratio', val: m.sharpeRatio.toFixed(2), cls: '', hint: `Annualized (vs ${{m.bnhSharpe.toFixed(2)}} B&H)` }},
  {{ label: 'Max Drawdown', val: `-${{m.maxDrawdown.toFixed(2)}}%`, cls: 'neg', hint: `vs -${{m.bnhMaxDrawdown.toFixed(2)}}% Buy & Hold` }},
  {{ label: 'Win Rate', val: `${{m.winRate.toFixed(2)}}%`, cls: m.winRate >= 50 ? 'pos' : 'neg', hint: `${{m.winningTrades}}W / ${{m.losingTrades}}L` }},
  {{ label: 'Total Trades', val: m.totalTrades, cls: '', hint: 'Completed round-trips' }},
  {{ label: 'Profit Factor', val: typeof m.profitFactor === 'number' ? m.profitFactor.toFixed(2) : m.profitFactor, cls: 'pos', hint: 'Gross profit / Gross loss' }},
  {{ label: 'Buy & Hold Return', val: `${{m.buyAndHoldReturn >= 0 ? '+' : ''}}${{m.buyAndHoldReturn.toFixed(2)}}%`, cls: m.buyAndHoldReturn >= 0 ? 'pos' : 'neg', hint: `₹${{s.bnhFinalEquity.toLocaleString()}} final value` }},
  {{ label: 'Excess Return', val: `${{m.excessReturn >= 0 ? '+' : ''}}${{m.excessReturn.toFixed(2)}}%`, cls: m.excessReturn >= 0 ? 'pos' : 'neg', hint: 'Strategy - Benchmark' }},
];

const grid = document.getElementById('metricsGrid');
cards.forEach(c => {{
  grid.innerHTML += `<div class="card"><div class="label">${{c.label}}</div><div class="val ${{c.cls}}">${{c.val}}</div><div class="hint">${{c.hint}}</div></div>`;
}});

const tbody = document.getElementById('tradeRows');
DATA.trades.forEach((t, idx) => {{
  const cls = t.netPnL >= 0 ? 'pos' : 'neg';
  const sign = t.netPnL >= 0 ? '+' : '';
  tbody.innerHTML += `<tr>
    <td>${{idx + 1}}</td><td>${{t.entryDate}}</td><td>${{t.exitDate}}</td><td>${{t.quantity}}</td>
    <td>₹${{t.entryPrice.toFixed(2)}}</td><td>₹${{t.exitPrice.toFixed(2)}}</td>
    <td class="right ${{cls}}">${{sign}}₹${{t.netPnL.toFixed(2)}}</td>
  </tr>`;
}});

const dpr = window.devicePixelRatio || 1;
const pad = {{ l: 68, r: 20, t: 22, b: 28 }};

function prepCanvas(canvas, heightCss) {{
  const w = Math.max(300, canvas.parentElement.clientWidth - 32);
  canvas.style.width = w + 'px';
  canvas.style.height = heightCss + 'px';
  canvas.width = w * dpr;
  canvas.height = heightCss * dpr;
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return {{ ctx, w, h: heightCss }};
}}

function drawGrid(ctx, data, min, max, w, h, unit) {{
  const plotW = w - pad.l - pad.r;
  const plotH = h - pad.t - pad.b;
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 0.7;
  ctx.font = '11px monospace';
  ctx.fillStyle = '#94a3b8';
  ctx.textAlign = 'right';

  for (let i = 0; i <= 4; i++) {{
    const y = pad.t + (plotH / 4) * i;
    const val = max - ((max - min) / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
    const label = unit === '₹' ? '₹' + Math.round(val).toLocaleString() : val.toFixed(2) + '%';
    ctx.fillText(label, pad.l - 6, y + 4);
  }}

  ctx.textAlign = 'center';
  const step = Math.max(1, Math.floor(data.length / 6));
  for (let i = 0; i < data.length; i += step) {{
    const x = pad.l + (i / (data.length - 1)) * plotW;
    const parts = data[i].d.split('-');
    ctx.fillText(parts[1] + '/' + parts[0].slice(2), x, h - 6);
  }}
}}

function drawSeries(ctx, data, min, max, w, h, color, fillAlpha) {{
  const plotW = w - pad.l - pad.r;
  const plotH = h - pad.t - pad.b;
  const range = max - min || 1;
  ctx.beginPath();
  data.forEach((d, i) => {{
    const x = pad.l + (i / (data.length - 1)) * plotW;
    const y = pad.t + plotH - ((d.v - min) / range) * plotH;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }});
  if (fillAlpha) {{
    const baseY = Math.max(pad.t, Math.min(pad.t + plotH, pad.t + plotH - ((0 - min) / range) * plotH));
    ctx.lineTo(pad.l + plotW, baseY);
    ctx.lineTo(pad.l, baseY);
    ctx.closePath();
    ctx.save(); ctx.globalAlpha = fillAlpha; ctx.fillStyle = color; ctx.fill(); ctx.restore();
    ctx.beginPath();
    data.forEach((d, i) => {{
      const x = pad.l + (i / (data.length - 1)) * plotW;
      const y = pad.t + plotH - ((d.v - min) / range) * plotH;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }});
  }}
  ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
}}

function drawAll() {{
  {{
    const {{ ctx, w, h }} = prepCanvas(document.getElementById('canvas-equity'), 220);
    const vals = DATA.equity.map(d => d.v);
    const min = Math.min(...vals) - 100, max = Math.max(...vals) + 100;
    drawGrid(ctx, DATA.equity, min, max, w, h, '₹');
    drawSeries(ctx, DATA.equity, min, max, w, h, '#22c55e', 0);
  }}
  {{
    const {{ ctx, w, h }} = prepCanvas(document.getElementById('canvas-drawdown'), 200);
    const vals = DATA.drawdown.map(d => d.v);
    const min = Math.min(...vals, -1.0), max = 0.05;
    drawGrid(ctx, DATA.drawdown, min, max, w, h, '%');
    drawSeries(ctx, DATA.drawdown, min, max, w, h, '#ef4444', 0.2);
  }}
  {{
    const {{ ctx, w, h }} = prepCanvas(document.getElementById('canvas-benchmark'), 230);
    const all = [...DATA.equity.map(d => d.v), ...DATA.benchmark.map(d => d.v)];
    const min = Math.min(...all) - 1000, max = Math.max(...all) + 1000;
    drawGrid(ctx, DATA.equity, min, max, w, h, '₹');
    drawSeries(ctx, DATA.benchmark, min, max, w, h, '#3b82f6', 0);
    drawSeries(ctx, DATA.equity, min, max, w, h, '#22c55e', 0);
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#22c55e'; ctx.fillRect(pad.l + 10, pad.t + 2, 14, 3);
    ctx.fillStyle = '#e2e8f0'; ctx.fillText(`Mean Reversion (${{m.totalReturn >= 0 ? '+' : ''}}${{m.totalReturn.toFixed(2)}}%)`, pad.l + 30, pad.t + 7);
    ctx.fillStyle = '#3b82f6'; ctx.fillRect(pad.l + 215, pad.t + 2, 14, 3);
    ctx.fillStyle = '#e2e8f0'; ctx.fillText(`Buy & Hold (${{m.buyAndHoldReturn >= 0 ? '+' : ''}}${{m.buyAndHoldReturn.toFixed(2)}}%)`, pad.l + 235, pad.t + 7);
  }}
}}

function attachHover(canvasId, readoutId, formatter) {{
  const canvas = document.getElementById(canvasId);
  const readout = document.getElementById(readoutId);
  canvas.addEventListener('mousemove', e => {{
    const rect = canvas.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (e.clientX - rect.left - pad.l) / (rect.width - pad.l - pad.r)));
    const idx = Math.round(frac * (DATA.equity.length - 1));
    readout.textContent = formatter(idx);
  }});
  canvas.addEventListener('mouseleave', () => {{ readout.textContent = 'Hover chart for values'; }});
}}

attachHover('canvas-equity', 'readout-equity', i => `${{DATA.equity[i].d}} · ₹${{DATA.equity[i].v.toLocaleString()}}`);
attachHover('canvas-drawdown', 'readout-drawdown', i => `${{DATA.drawdown[i].d}} · ${{DATA.drawdown[i].v.toFixed(2)}}%`);
attachHover('canvas-benchmark', 'readout-benchmark', i => `${{DATA.equity[i].d}} · Strategy: ₹${{DATA.equity[i].v.toLocaleString()}} | B&H: ₹${{DATA.benchmark[i].v.toLocaleString()}}`);

window.addEventListener('resize', drawAll);
drawAll();
</script>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return str(Path(output_path).resolve())


if __name__ == '__main__':
    args = sys.argv[1:]
    json_only = '--json' in args
    no_open = '--no-open' in args
    positional = [a for a in args if not a.startswith('--')]
    csv_path = positional[0] if positional else 'data/RELIANCE.csv'

    result = run_backtest(csv_path)
    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    if json_only:
        print(json.dumps(result))
    else:
        m = result['metrics']
        s = result['summary']
        print("\n========== BACKTEST SUMMARY ==========")
        print(f"Period          : {s['testStartDate']} to {s['testEndDate']} ({s['testingCandles']} days)")
        print(f"Total Return    : {m['totalReturn']:+.4f}% (Final: Rs {s['finalEquity']:,.2f})")
        print(f"Sharpe Ratio    : {m['sharpeRatio']:.4f}")
        print(f"Max Drawdown    : {m['maxDrawdown']:.4f}%")
        print(f"Win Rate        : {m['winRate']:.2f}% ({m['winningTrades']}W / {m['losingTrades']}L)")
        print(f"Total Trades    : {m['totalTrades']}")
        print(f"Profit Factor   : {m['profitFactor']}")
        print(f"Buy & Hold      : {m['buyAndHoldReturn']:+.4f}%")
        print(f"Excess Return   : {m['excessReturn']:+.4f}%")
        print("======================================")

        dashboard_file = generate_dashboard_html(result, 'dashboard.html')
        print(f"Dashboard saved : {dashboard_file}")
        if not no_open:
            webbrowser.open(Path(dashboard_file).as_uri())
