from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from data.data_single_asset import get_price_history
from logic.strategies_single import backtest_buy_and_hold, backtest_momentum_sma
from logic.metrics import summarize_strategy, annualized_volatility


# Select assets for the report (CAC 40 index + subset)
ASSET_TICKERS = [
    "^FCHI",   # CAC 40 index
    "AI.PA",   # Air Liquide
    "MC.PA",   # LVMH
    "SAN.PA",  # Sanofi
    "TTE.PA",  # TotalEnergies
    "SU.PA",   # Schneider
]


def build_report_row(ticker: str, years: int = 5) -> dict:
    data = get_price_history(ticker=ticker, years=years)

    last_idx = data.index[-1]
    last_row = data.iloc[-1]

    last_open = float(last_row["Open"])
    last_close = float(last_row["Close"])
    last_return = float(last_row["return"])

    vol20 = annualized_volatility(data["return"].tail(20), periods_per_year=252)

    # Buy & Hold
    bh = backtest_buy_and_hold(data, initial_capital=1_000.0)
    bh_summary = summarize_strategy(bh, initial_capital=1_000.0)

    # Momentum SMA(50)
    mom = backtest_momentum_sma(data, window=50, initial_capital=1_000.0)
    mom_summary = summarize_strategy(mom, initial_capital=1_000.0)

    return {
        "date": last_idx.date().isoformat(),
        "ticker": ticker,
        "last_open": last_open,
        "last_close": last_close,
        "last_return": last_return,
        "vol20_annualized": vol20,
        # Buy & Hold
        "bh_total_return": float(bh_summary["total_return"]),
        "bh_sharpe": float(bh_summary["sharpe_ratio"]),
        "bh_max_drawdown": float(bh_summary["max_drawdown"]),
        # Momentum
        "mom_total_return": float(mom_summary["total_return"]),
        "mom_sharpe": float(mom_summary["sharpe_ratio"]),
        "mom_max_drawdown": float(mom_summary["max_drawdown"]),
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    rows = []
    for t in ASSET_TICKERS:
        try:
            rows.append(build_report_row(t))
        except Exception as e:
            # Capture errors to avoid crashing the whole cron job
            print(f"Error processing {t}: {e}")
            rows.append({"date": date.today().isoformat(), "ticker": t, "error": str(e)})

    df_report = pd.DataFrame(rows)

    today_str = date.today().isoformat()
    outfile = reports_dir / f"daily_report_{today_str}.csv"
    df_report.to_csv(outfile, index=False)

    print(f"Daily report saved to {outfile}")
    print(df_report)


if __name__ == "__main__":
    main()