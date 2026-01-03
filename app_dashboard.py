import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

from data_single_asset import get_price_history, DEFAULT_TICKER
from strategies_single import backtest_buy_and_hold, backtest_momentum_sma
from metrics import summarize_strategy

from streamlit_autorefresh import st_autorefresh


# ===== Univers d'actifs (CAC 40) =====
TICKERS = {
    "^FCHI": "CAC 40 (Index)",

    "AC.PA": "Accor",
    "AI.PA": "Air Liquide",
    "AIR.PA": "Airbus",
    "MT.AS": "ArcelorMittal",  
    "CS.PA": "AXA",
    "BNP.PA": "BNP Paribas",
    "EN.PA": "Bouygues",
    "BVI.PA": "Bureau Veritas",
    "CAP.PA": "Capgemini",
    "CA.PA": "Carrefour",
    "ACA.PA": "Crédit Agricole",
    "BN.PA": "Danone",
    "DSY.PA": "Dassault Systèmes",
    "EDEN.PA": "Edenred",
    "ENGI.PA": "Engie",
    "EL.PA": "EssilorLuxottica",
    "ERF.PA": "Eurofins Scientific",
    "RMS.PA": "Hermès",
    "KER.PA": "Kering",
    "LR.PA": "Legrand",
    "OR.PA": "L'Oréal",
    "MC.PA": "LVMH",
    "ML.PA": "Michelin",
    "ORA.PA": "Orange",
    "RI.PA": "Pernod Ricard",
    "PUB.PA": "Publicis Groupe",
    "RNO.PA": "Renault",
    "SAF.PA": "Safran",
    "SGO.PA": "Saint-Gobain",
    "SAN.PA": "Sanofi",
    "SU.PA": "Schneider Electric",
    "GLE.PA": "Société Générale",
    "STLA.PA": "Stellantis",
    "STM.PA": "STMicroelectronics",
    "TEP.PA": "Teleperformance",
    "HO.PA": "Thales",
    "TTE.PA": "TotalEnergies",
    "URW.AS": "Unibail-Rodamco-Westfield",  
    "VIE.PA": "Veolia",
    "DG.PA": "Vinci",
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
    st.subheader("Live market view")

    st.write(
        "Current intraday prices (1-minute data) retrieved from Yahoo Finance "
        "via the public `yfinance` API."
    )

    ticker_choices = list(TICKERS.keys())

    # Sélection par défaut (quelques actifs)
    default_list = ["^FCHI", "AI.PA", "AIR.PA", "MC.PA", "SAN.PA", "TTE.PA", "SU.PA"]
    default_list = [t for t in default_list if t in ticker_choices]

    selected_tickers = st.multiselect(
        "Choose assets to display:",
        options=ticker_choices,
        default=default_list,
        format_func=lambda x: f"{TICKERS[x]} ({x})",
    )

    if not selected_tickers:
        st.warning("Select at least one asset.")
        return

    # --- tableau récap --- 
    st.markdown("### Summary table")

    rows = []
    for ticker in selected_tickers:
        price = get_last_price(ticker)
        rows.append(
            {
                "Name": TICKERS[ticker],
                "Ticker": ticker,
                "Last price": price,
            }
        )

    df_summary = pd.DataFrame(rows).sort_values("Name")
    st.dataframe(df_summary, use_container_width=True)

    now_utc = datetime.now(timezone.utc)
    st.caption(f"Last update (system time, UTC): {now_utc:%Y-%m-%d %H:%M:%S %Z}")


# ---------- Onglet Quant A : Single asset backtest ----------

def single_asset_tab():
    """Onglet 2 : module Quant A (un seul actif + backtests)."""

    st.subheader("Single asset backtest – Quant A")

    st.write(
        "Focus on one asset at a time. Two strategies are implemented: "
        "Buy & Hold and Momentum (SMA filter)."
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
    sma_window = 50
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

    # --- Backtest ---
    run = st.button("Run backtest")

    if not run:
        st.info("Choose parameters then click **Run backtest**.")
        return

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

    # Option : afficher les dernières lignes du backtest
    with st.expander("Show last rows of backtest data"):
        st.dataframe(result.tail(30), use_container_width=True)


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

