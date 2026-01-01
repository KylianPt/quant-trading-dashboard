import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

from data_single_asset import get_price_history, DEFAULT_TICKER
from strategies_single import backtest_buy_and_hold, backtest_momentum_sma
from metrics import summarize_strategy

from streamlit_autorefresh import st_autorefresh

# ===== Univers d'actifs (principalement CAC 40) =====
TICKERS = {
    "^FCHI": "CAC 40",
    "MC.PA": "LVMH",
    "AIR.PA": "Airbus",
    "OR.PA": "L'Oréal",
    "SAN.PA": "Sanofi",
    "BNP.PA": "BNP Paribas",
    "GLE.PA": "Société Générale",
    "ENGI.PA": "Engie",
    "SU.PA": "Schneider Electric",
    "DG.PA": "Vinci",
    "RI.PA": "Pernod Ricard",
    "KER.PA": "Kering",
    "AI.PA": "Air Liquide",
    "BN.PA": "Danone",
}


# ---------- Helpers pour la partie "live prices" ----------

def get_last_price(ticker: str) -> float | None:
    """
    Récupère le dernier prix 'Close' non-NaN en intraday (1 minute) pour un ticker.
    Retourne None si aucune donnée valide.
    """
    data = yf.Ticker(ticker).history(period="1d", interval="1m", auto_adjust=True)
    if data.empty:
        return None

    close_series = data["Close"].dropna()
    if close_series.empty:
        return None

    return float(close_series.iloc[-1])


def live_prices_tab():
    """Onglet 1 : vue temps réel multi-actifs (ce que tu avais déjà)."""
    st.subheader("Live market view")

    st.write(
        "Current intraday prices (1-minute data) retrieved from Yahoo Finance "
        "via the public `yfinance` API."
    )

    ticker_choices = list(TICKERS.keys())
    selected_tickers = st.multiselect(
        "Choose assets to display:",
        options=ticker_choices,
        default=ticker_choices,
        format_func=lambda x: f"{TICKERS[x]} ({x})",
    )

    if not selected_tickers:
        st.warning("Select at least one asset.")
        return

    # --- cartes de valeurs actuelles ---
    st.markdown("### Current values")

    cols = st.columns(len(selected_tickers))
    latest_prices: dict[str, float | None] = {}

    for col, ticker in zip(cols, selected_tickers):
        with col:
            name = TICKERS[ticker]
            price = get_last_price(ticker)
            latest_prices[ticker] = price

            if price is None:
                st.metric(label=f"{name} ({ticker})", value="N/A")
            else:
                st.metric(label=f"{name} ({ticker})", value=f"{price:,.2f}")

    # --- tableau récap ---
    st.markdown("### Summary table")

    rows = []
    for ticker in selected_tickers:
        price = latest_prices.get(ticker)
        rows.append(
            {
                "Name": TICKERS[ticker],
                "Ticker": ticker,
                "Last price": price,
            }
        )

    df_summary = pd.DataFrame(rows)
    df_summary = df_summary.sort_values("Name")

    st.dataframe(df_summary, use_container_width=True)

    now_utc = datetime.now(timezone.utc)
    st.caption(f"Last update (system time, UTC): {now_utc:%Y-%m-%d %H:%M:%S %Z}")


# ---------- Onglet Quant A : Single asset backtest ----------

def single_asset_tab():
    """Onglet 2 : module Quant A (un seul actif + backtests)."""

    st.subheader("Single asset backtest – Quant A")

    st.write(
        "Analyse one main asset at a time (default: Air Liquide). "
        "We implement simple buy-and-hold and momentum SMA strategies, "
        "and display key performance metrics."
    )

    # Choix de l'actif
    ticker_options = list(TICKERS.keys())
    default_index = ticker_options.index(DEFAULT_TICKER) if DEFAULT_TICKER in ticker_options else 0
    ticker = st.selectbox(
        "Asset to backtest:",
        options=ticker_options,
        index=default_index,
        format_func=lambda x: f"{TICKERS.get(x, x)} ({x})",
    )

    # Période historique
    years = st.slider("Historical window (years)", min_value=1, max_value=10, value=5, step=1)

    # Choix de la stratégie
    strategy_name = st.radio(
        "Strategy:",
        options=["Buy & Hold", "Momentum SMA"],
        horizontal=True,
    )

    # Paramètre pour la SMA si besoin
    sma_window = None
    if strategy_name == "Momentum SMA":
        sma_window = st.slider("SMA window (days)", min_value=10, max_value=200, value=50, step=5)

    # Capital initial
    initial_capital = st.number_input(
        "Initial capital",
        min_value=100.0,
        max_value=1_000_000.0,
        value=1_000.0,
        step=100.0,
    )

    run = st.button("Run backtest")

    if not run:
        st.info("Choose parameters then click **Run backtest**.")
        return

    # --- Backtest ---
    with st.spinner("Running backtest..."):
        data = get_price_history(ticker=ticker, years=years)

        if strategy_name == "Buy & Hold":
            result = backtest_buy_and_hold(data, initial_capital=initial_capital)
        else:
            result = backtest_momentum_sma(
                data,
                window=sma_window,
                initial_capital=initial_capital,
            )

        summary = summarize_strategy(
            result,
            initial_capital=initial_capital,
            periods_per_year=252,
            risk_free_rate=0.0,
        )

    # --- Graphique principal : prix vs stratégie ---
    st.markdown("### Price vs strategy (normalized)")

    chart_df = pd.DataFrame(
        {
            "Price (normalized)": result["price_norm"],
            "Strategy (normalized)": result["strategy_norm"],
        },
        index=result.index,
    )

    st.line_chart(chart_df)

    # --- métriques de performance ---
    st.markdown("### Performance metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Final equity", f"{summary['final_equity']:.2f}")
    col2.metric("Total return", f"{summary['total_return'] * 100:.1f}%")
    col3.metric("Max drawdown", f"{summary['max_drawdown'] * 100:.1f}%")

    col4, col5, col6 = st.columns(3)
    col4.metric("Annualized return", f"{summary['annualized_return'] * 100:.1f}%")
    col5.metric("Annualized volatility", f"{summary['annualized_volatility'] * 100:.1f}%")
    col6.metric("Sharpe ratio", f"{summary['sharpe_ratio']:.2f}")

    st.caption(
        "Daily data; metrics are annualized assuming 252 trading days per year. "
        "Max drawdown is expressed as a negative percentage from peak to trough."
    )

    # Option : afficher les dernières lignes du backtest
    with st.expander("Show last rows of backtest data"):
        st.dataframe(result.tail(), use_container_width=True)


# ---------- Main app ----------

def main():
     # Auto-refresh toutes les 5 minutes (300 000 ms)
    st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh_5min")

    st.title("Live Market Dashboard – Prototype")

    tabs = st.tabs(["Live prices", "Single asset backtest"])

    with tabs[0]:
        live_prices_tab()

    with tabs[1]:
        single_asset_tab()


if __name__ == "__main__":
    main()

