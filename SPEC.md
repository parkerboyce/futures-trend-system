# Futures Trend Trading System — Spec (v0.1)

## Instrument
- Product: Micro E-mini S&P 500 Futures (MES)
- Venue: CME
- Multiplier: $5 / index point
- Tick size: 0.25 points
- Tick value: $1.25

## Timeframe & Session
- Bar size: 5-minute bars
- Trading session: RTH only (08:30–15:00 CT)
- Position policy (v1): Flatten at RTH close

## Backtest Capital
- Starting equity (backtest): $100,000
- Expected live equity (initial): $5,000–$15,000 (informational)

## Continuous Futures Construction
- Roll rule: Volume-based rollover (roll when next contract volume > front contract volume)
- Roll timing: Switch contracts at next RTH session open after trigger
- Back-adjustment: Additive back-adjustment at roll to create smooth historical series
- Data storage: Parquet (raw per-contract + processed continuous)

## Strategy (Trend Following)
- Strategy family: Breakout trend following (Donchian-style)
- Signals: Generated on bar close (no intrabar lookahead)
- Position sizing: Volatility-based sizing using ATR
- Initial parameter placeholders:
  - Donchian lookback: N = 20 bars
  - ATR window: 14 bars
  - Stop distance: k * ATR (k = 3.0)

## Risk Controls (v1)
- Max contracts: 5 MES
- Max trades/day: 10
- Daily loss limit: 2% of equity (stop trading + flatten)
- Volatility spike circuit breaker: disable new trades if ATR exceeds threshold (TBD)
- Kill switch: flatten all + disable trading until manual reset

## Execution & Costs (v1 placeholders)
- Order type: Market orders at next bar open (backtest) / market at signal time (paper/live)
- Commission (round turn): $1.50 per contract (placeholder)
- Slippage model: 1 tick per entry and 1 tick per exit (placeholder)

## Validation
- Walk-forward testing required
- Metrics: CAGR, Sharpe, Sortino, Max Drawdown, Calmar, turnover, trade count, avg slippage