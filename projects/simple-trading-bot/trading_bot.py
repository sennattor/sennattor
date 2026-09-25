from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd
import yfinance as yf


TRADING_DAYS = 252


@dataclass
class BacktestResult:
    data: pd.DataFrame
    total_return: float
    cagr: float
    sharpe: float
    max_drawdown: float
    trades: int


def download_prices(ticker: str, start: str, end: str) -> pd.Series:
    """Download adjusted daily close prices from Yahoo Finance."""
    frame = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )

    if frame.empty:
        raise ValueError(f"No market data returned for {ticker!r}.")

    close = frame["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna().astype(float)
    close.name = "close"
    return close


def build_signals(prices: pd.Series, fast_window: int, slow_window: int) -> pd.DataFrame:
    """Create a long/cash moving-average crossover signal."""
    if fast_window <= 0 or slow_window <= 0:
        raise ValueError("Moving-average windows must be positive.")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window.")

    df = prices.to_frame()
    df["fast_ma"] = df["close"].rolling(fast_window).mean()
    df["slow_ma"] = df["close"].rolling(slow_window).mean()

    # 1 = invested, 0 = cash. No short selling in this demo.
    df["position"] = (df["fast_ma"] > df["slow_ma"]).astype(float)
    df.loc[df["slow_ma"].isna(), "position"] = 0.0
    return df


def backtest(
    prices: pd.Series,
    fast_window: int = 20,
    slow_window: int = 50,
    initial_cash: float = 10_000.0,
    transaction_cost_bps: float = 10.0,
) -> BacktestResult:
    """Backtest the strategy with simple proportional transaction costs."""
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive.")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps cannot be negative.")

    df = build_signals(prices, fast_window, slow_window)
    df["asset_return"] = df["close"].pct_change().fillna(0.0)

    # Position decided on day t is applied from t+1 onward to avoid look-ahead bias.
    held_position = df["position"].shift(1).fillna(0.0)
    df["turnover"] = df["position"].diff().abs().fillna(df["position"].abs())

    cost_rate = transaction_cost_bps / 10_000.0
    df["strategy_return"] = held_position * df["asset_return"] - df["turnover"] * cost_rate
    df["equity"] = initial_cash * (1.0 + df["strategy_return"]).cumprod()
    df["buy_hold_equity"] = initial_cash * (1.0 + df["asset_return"]).cumprod()

    total_return = df["equity"].iloc[-1] / initial_cash - 1.0

    elapsed_years = max(len(df) / TRADING_DAYS, 1.0 / TRADING_DAYS)
    cagr = (df["equity"].iloc[-1] / initial_cash) ** (1.0 / elapsed_years) - 1.0

    daily = df["strategy_return"]
    volatility = daily.std(ddof=0)
    sharpe = 0.0 if volatility == 0 or np.isnan(volatility) else np.sqrt(TRADING_DAYS) * daily.mean() / volatility

    running_max = df["equity"].cummax()
    drawdown = df["equity"] / running_max - 1.0
    max_drawdown = drawdown.min()

    trades = int((df["turnover"] > 0).sum())

    return BacktestResult(
        data=df,
        total_return=float(total_return),
        cagr=float(cagr),
        sharpe=float(sharpe),
        max_drawdown=float(max_drawdown),
        trades=trades,
    )


def print_summary(ticker: str, result: BacktestResult) -> None:
    final_equity = result.data["equity"].iloc[-1]
    buy_hold = result.data["buy_hold_equity"].iloc[-1]

    print(f"Ticker:            {ticker}")
    print(f"Final equity:      {final_equity:,.2f}")
    print(f"Buy & hold equity: {buy_hold:,.2f}")
    print(f"Total return:      {result.total_return:.2%}")
    print(f"CAGR:              {result.cagr:.2%}")
    print(f"Sharpe ratio:      {result.sharpe:.2f}")
    print(f"Max drawdown:      {result.max_drawdown:.2%}")
    print(f"Trades:            {result.trades}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Educational SMA crossover backtest using Yahoo Finance data."
    )
    parser.add_argument("--ticker", default="SPY")
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=50)
    parser.add_argument("--capital", type=float, default=10_000.0)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--csv", default="backtest_results.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prices = download_prices(args.ticker, args.start, args.end)
    result = backtest(
        prices,
        fast_window=args.fast,
        slow_window=args.slow,
        initial_cash=args.capital,
        transaction_cost_bps=args.cost_bps,
    )
    print_summary(args.ticker, result)
    result.data.to_csv(args.csv)
    print(f"\nSaved detailed results to {args.csv}")


if __name__ == "__main__":
    main()
