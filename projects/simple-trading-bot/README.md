# Simple Trading Bot

A small educational quantitative-finance project implementing a **moving-average crossover strategy** with a basic backtest.

The project is intentionally simple: the goal is to demonstrate clean strategy logic, avoidance of look-ahead bias, transaction-cost modelling, and basic performance analytics.

## Strategy

The strategy uses two simple moving averages:

- **Fast MA:** 20 trading days by default
- **Slow MA:** 50 trading days by default
- **Long position:** when the fast MA is above the slow MA
- **Cash:** otherwise

The signal generated on day `t` is applied from day `t+1`, which avoids using future information in the backtest.

## Features

- Downloads daily adjusted market data with `yfinance`
- Implements a long/cash SMA crossover strategy
- Includes configurable transaction costs
- Calculates:
  - Total return
  - CAGR
  - Sharpe ratio
  - Maximum drawdown
  - Number of trades
- Compares the strategy with buy-and-hold
- Exports the full backtest to CSV

## Installation

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Default example:

```bash
python trading_bot.py
```

Custom ticker and parameters:

```bash
python trading_bot.py --ticker QQQ --start 2020-01-01 --end 2026-01-01 --fast 20 --slow 50 --cost-bps 10
```

Example with a different instrument:

```bash
python trading_bot.py --ticker AAPL --fast 10 --slow 40
```

## Output

The script prints a performance summary to the terminal and saves detailed daily results to:

```text
backtest_results.csv
```

The CSV includes price, moving averages, position, turnover, strategy return, strategy equity, and buy-and-hold equity.

## Project structure

```text
simple-trading-bot/
├── trading_bot.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Why this project

This is the first project in my public quantitative-finance portfolio. The next iterations may include:

- walk-forward validation
- parameter sensitivity analysis
- volatility targeting
- benchmark comparison
- richer risk metrics
- event logging
- broker API integration in paper-trading mode

## Disclaimer

This project is for **educational and research purposes only**. It is not investment advice and does not place live orders.
