import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

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

def main():
    st.title("Live Market Dashboard – Prototype")

    st.write(
        "Current intraday prices (1-minute data) retrieved from Yahoo Finance "
        "via the public `yfinance` API."
    )

    # ===== Sélection des actifs =====
    ticker_choices = list(TICKERS.keys())
    selected_tickers = st.multiselect(
        "Choose assets to display:",
        options=ticker_choices,
        default=ticker_choices,  # par défaut : tous cochés
        format_func=lambda x: f"{TICKERS[x]} ({x})",
    )

    if not selected_tickers:
        st.warning("Select at least one asset.")
        return

    # ===== Affichage des valeurs actuelles sous forme de métriques =====
    st.subheader("Current values")

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

    # ===== Tableau récapitulatif =====
    st.subheader("Summary table")

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
    # Optionnel : trier par nom
    df_summary = df_summary.sort_values("Name")

    st.dataframe(df_summary, use_container_width=True)

    # ===== Heure de mise à jour (heure système) =====
    now_utc = datetime.now(timezone.utc)
    st.caption(f"Last update (system time, UTC): {now_utc:%Y-%m-%d %H:%M:%S %Z}")

if __name__ == "__main__":
    main()

