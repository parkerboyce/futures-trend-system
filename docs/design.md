# Futures Trend Trading System — Design Doc (v0.1)

## Goals
- Build a modular, event-driven futures trading system for trend following (MES, 5-min, RTH).
- Support a single codebase for:
  - Research/backtesting
  - Paper trading
  - Live execution (future)
- Enforce realism:
  - No lookahead bias
  - Explicit transaction costs and slippage assumptions
  - Explicit risk constraints and kill switch behavior

## Non-Goals (v0.1)
- Tick-level/order-book simulation
- Multi-asset portfolio optimization
- Advanced ML regime detection
- Full exchange-grade OMS

---

## System Overview

**Pipeline**
Market Data → Strategy → Risk Engine → Execution → Portfolio → Monitoring/Reports

**Principles**
- Strategy emits *intent* (signals/orders), never mutates portfolio directly.
- Risk engine is the gatekeeper for orders.
- Execution is broker-agnostic via adapters.
- Backtest and live share the same Strategy/Risk/Portfolio logic (different data & execution adapters).

---

## Repository Layout (key modules)

- `src/ft/data/` — ingest, continuous contract construction, session calendar, storage
- `src/ft/backtest/` — event engine, broker simulator, costs, portfolio accounting
- `src/ft/strategies/` — strategy interfaces + implementations
- `src/ft/risk/` — limits + order approval/adjustment
- `src/ft/execution/` — paper/live broker adapters
- `src/ft/monitoring/` — logging, metrics, reports

---

## Data Layer

### Responsibilities
- Ingest raw per-contract futures bars (MES expiries).
- Construct continuous contract time series:
  - Volume-based rollover
  - Additive back-adjustment
  - No-lookahead roll timing
- Apply session filters (RTH only).
- Persist raw + processed datasets (Parquet).

### Data Model
A canonical `Bar` schema used across backtest and live:

- `ts` (datetime): bar close timestamp (ET)
- `open`, `high`, `low`, `close` (float)
- `volume` (int)
- `symbol` (str): e.g., "MES"
- `contract` (str): e.g., "MESM26" (optional in continuous)
- `session` (str): "RTH"
- Optional: `vwap`, `trade_count`

### Storage
- Raw: `data/raw/<symbol>/<contract>.parquet`
- Processed:
  - Continuous: `data/processed/<symbol>_continuous_<bar>.parquet`
  - Roll schedule: `data/processed/<symbol>_rolls.parquet`
  - data/processed/<symbol>_continuous_metadata.json
  - Metadata/specs: `data/processed/contract_specs.json`

### Key APIs (design contracts)

`src/ft/data/ingest.py`
- `ingest_contract_bars(symbol: str, contract: str, src: str, out_path: str) -> None`

`src/ft/data/calendar.py`
- `is_rth(ts) -> bool`
- `filter_rth(df) -> df`
- `trading_days(start, end) -> list[date]`

`src/ft/data/continuous.py`
- `compute_roll_schedule(raw_bars: dict[str, df], rule: str) -> df_rolls`
- `build_continuous(raw_bars: dict[str, df], rolls: df_rolls, adjust: str) -> df_continuous`

**Roll timing rule (no-lookahead)**
- Determine trigger day when next contract volume exceeds front contract volume using that day’s complete data.
- Switch to new contract at **next RTH session open**.

`src/ft/data/storage.py`
- `save_parquet(df, path) -> None`
- `load_parquet(path) -> df`

---

## Event-Driven Backtest Engine

### Responsibilities
- Iterate market data bars in chronological order.
- Generate `MarketEvent` from each bar.
- Pass to Strategy to generate signals.
- Convert signals → orders.
- Pass orders through Risk Engine.
- Simulate execution/fills via BrokerSim with costs/slippage.
- Update Portfolio state and record metrics.

### Event Types (src/ft/backtest/events.py)
- `MarketEvent(bar: Bar)`
- `SignalEvent(ts, signal)` (e.g., desired direction/target position)
- `OrderEvent(ts, order)` (market/limit/stop)
- `FillEvent(ts, fill)` (price, qty, fees, slippage)

### Engine Loop (src/ft/backtest/engine.py)
Pseudocode:

1. For each `bar` in dataset:
   - emit `MarketEvent(bar)`
   - `strategy.on_bar(bar, state) -> Optional[Signal]`
   - if signal:
     - `portfolio.generate_order(signal, bar) -> Order`
     - `risk.evaluate(order, portfolio_state, bar) -> RiskDecision`
     - if approved:
       - `broker.place_order(order)`
       - `fills = broker.simulate_fills(bar)`
       - `portfolio.apply_fills(fills)`
   - `portfolio.mark_to_market(bar.close)`
   - record metrics (equity, drawdown, exposure)

### Broker Simulation (src/ft/backtest/broker_sim.py)
- Market orders fill at:
  - default v1: next bar open +/- slippage
- Slippage model (v1):
  - fixed ticks per side (e.g., 1 tick entry, 1 tick exit)
- Fees:
  - fixed commission per contract round turn (placeholder initially)

Key APIs:
- `place_order(order) -> order_id`
- `simulate_fills(bar) -> list[Fill]`

---

## Strategy Layer

### Responsibilities
- Produce trading signals based on incoming bars.
- Maintain internal indicator state (Donchian levels, ATR).
- Must not execute trades directly.

### Strategy Interface (src/ft/strategies/base.py)
- `on_bar(bar: Bar, state: StrategyState) -> Optional[Signal]`

`Signal` should be one of:
- `TargetPositionSignal(target_contracts: int)`
- or `DirectionalSignal(side: "LONG"|"SHORT"|"FLAT")` (engine converts to target sizing)

### Trend Strategy (v1): Donchian Breakout
- Long when `close > rolling_high(N)`
- Short when `close < rolling_low(N)`
- Exit: ATR-based trailing stop OR opposite breakout (defined in SPEC)

Indicators:
- Donchian lookback N (default 20)
- ATR window (default 14)
- Stop multiple k (default 3.0)

---

## Portfolio & Accounting

### Responsibilities
- Maintain positions, cash, equity curve.
- Translate signals into orders (in coordination with sizing + risk).
- Mark-to-market each bar.
- Track realized/unrealized PnL, fees, slippage.

Key State
- `cash`
- `position_contracts` (int)
- `avg_entry_price`
- `realized_pnl`
- `unrealized_pnl`
- `equity`
- `peak_equity`, `drawdown`

Key APIs (src/ft/backtest/portfolio.py)
- `generate_order(signal, bar, sizing) -> Order`
- `apply_fills(fills) -> None`
- `mark_to_market(price) -> None`

---

## Risk Engine

### Responsibilities
- Enforce limits and modify/reject orders.
- Provide kill switch behavior.
- Ensure session compliance (RTH only, flatten at close policy).
- Enforce daily loss limits.

Key Rules (v1)
- Max contracts (e.g., 5 MES)
- Max trades per day (e.g., 10)
- Daily loss limit (e.g., 2% equity): flatten + stop trading
- Volatility spike breaker (TBD): stop new trades if ATR above threshold
- Order validation (qty nonzero, within bounds)

Risk API (src/ft/risk/manager.py)
- `evaluate(order, portfolio_state, bar) -> RiskDecision`

`RiskDecision`
- `approved: bool`
- `order: Optional[Order]` (possibly modified qty)
- `reason: str`
- `kill_switch: bool` (if true: flatten + disable)

---

## Execution Layer (Paper/Live Adapters)

### Responsibilities
- Provide broker-agnostic interface for order placement and fill updates.
- Paper adapter can simulate fills using live bars.
- Live adapter (future) connects to broker API.

Execution Interface (src/ft/execution/base.py)
- `connect() -> None`
- `place_order(order) -> broker_order_id`
- `cancel_order(broker_order_id) -> None`
- `poll_fills() -> list[Fill]`
- `get_positions() -> PositionSnapshot`

Adapters
- `paper.py`: consumes live bars (or replay) and simulates fills
- `ibkr.py`: placeholder adapter for Interactive Brokers (future)

---

## Monitoring & Reporting

### Responsibilities
- Structured logs (JSON)
- Daily summaries
- Metrics capture (equity, drawdown, exposure, turnover)
- Alerts (future): daily loss limit triggered, disconnects, kill switch

Logging (src/ft/monitoring/logger.py)
- unified logger config for all modules

Reports (src/ft/monitoring/reports.py)
- daily report: trades, PnL attribution, slippage vs model, risk stats

---

## Config System

- Store configs in `configs/*.yaml`
- Example: `configs/dev.yaml`, `configs/paper.yaml`

Config should include:
- Symbol(s), timeframe, session
- Strategy params (N, ATR window, k)
- Costs assumptions (commission, slippage ticks)
- Risk limits (max contracts, daily loss)
- Data paths

---

## Testing Plan (v0.1)

### Unit Tests
- `test_calendar.py`: RTH filter correctness, timezone handling
- `test_continuous.py`: roll schedule correctness, back-adjustment math, no-lookahead roll timing
- `test_engine.py`: engine runs on toy dataset, produces deterministic PnL with fixed slippage

### Invariants
- No missing timestamps after continuous construction
- Roll schedule dates are non-decreasing
- Portfolio equity updates monotonically with correct PnL arithmetic
- Strategy uses only historical bars up to current bar

---

## Milestones

- Week 1: Spec + architecture + tooling (this doc)
- Week 2: Data ingestion + continuous contract builder + tests
- Week 3: Backtest engine MVP + portfolio accounting
- Week 4: Donchian trend strategy + ATR sizing + initial results
- Week 5+: Risk hardening, walk-forward validation, paper trading