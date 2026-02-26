# Futures Trend Trading System

An event-driven systematic futures trading system designed for research, backtesting, and automated execution.

## Overview

This project implements a modular trading framework for systematic trend-following strategies on futures markets. The system is designed with production-quality architecture and includes:

- Continuous contract construction (volume-based roll, back-adjustment)
- Event-driven backtesting engine
- Realistic transaction cost and slippage modeling
- Volatility-targeted position sizing
- Configurable risk engine (position limits, daily loss limits, kill switch)
- Broker-agnostic execution layer
- Walk-forward validation framework

The objective is to build a research-grade trading pipeline suitable for automated deployment.

---

## Architecture

The system is structured into modular components:


Each module is isolated and testable, ensuring clean separation of concerns between research and live trading infrastructure.

---

## Current Status

Week 1: Project scaffolding, architecture design, tooling setup  
Next: Continuous futures data construction

---

## Tech Stack

- Python 3.12
- Pytest (testing)
- Ruff (linting)
- Docker (environment reproducibility)

---

## Disclaimer

This project is for educational and research purposes only. Trading futures involves significant financial risk.