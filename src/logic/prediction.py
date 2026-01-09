import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import statsmodels.api as sm
import streamlit as st

def get_future_dates(df, days_ahead):
    last_date = df.index[-1]
    return pd.date_range(start=last_date + pd.Timedelta(days=1), periods=days_ahead)

def calculate_confidence_interval(std_dev, future_pred, days_ahead):
    """Calcule l'intervalle basé sur l'écart-type historique."""
    z_score = 1.96 # 95%
    time_step = np.arange(1, days_ahead + 1)
    # L'incertitude s'élargit avec le temps
    expanding_interval = std_dev * z_score * np.sqrt(time_step)
    return future_pred - expanding_interval, future_pred + expanding_interval

@st.cache_data(show_spinner=False)
def run_prediction_model(data, model_type="Linear Regression", days_ahead=30, params=None):
    if data.empty: return pd.DataFrame(), {}
    
    df = data.copy()
    df['date_ordinal'] = df.index.map(pd.Timestamp.toordinal)
    
    X = df[['date_ordinal']]
    y = df['Close']
    
    # Dates futures
    future_dates = get_future_dates(df, days_ahead)
    future_ordinal = future_dates.map(pd.Timestamp.toordinal).values.reshape(-1, 1)
    
    # Dernier point connu (pour l'ancrage)
    last_ordinal = X.iloc[[-1]]
    last_actual_price = y.iloc[-1]
    
    hist_pred = None
    future_raw = None
    
    # --- MODELING ---
    try:
        if model_type == "Linear Regression":
            model = LinearRegression()
            model.fit(X, y)
            hist_pred = model.predict(X)
            future_raw = model.predict(future_ordinal)
            # Valeur prédite pour aujourd'hui (pour calculer le décalage)
            last_model_val = model.predict(last_ordinal)[0]
            
        elif model_type == "Random Forest":
            n_est = params.get('n_estimators', 100)
            model = RandomForestRegressor(n_estimators=n_est, random_state=42)
            model.fit(X, y)
            hist_pred = model.predict(X)
            future_raw = model.predict(future_ordinal)
            last_model_val = model.predict(last_ordinal)[0]
            
        elif model_type == "ARIMA":
            p = params.get('p', 5)
            # ARIMA est naturellement plus continu, mais on force l'ancrage aussi
            model = sm.tsa.ARIMA(y, order=(p, 1, 0))
            model_fit = model.fit()
            hist_pred = model_fit.fittedvalues
            forecast_res = model_fit.get_forecast(steps=days_ahead)
            future_raw = forecast_res.predicted_mean.values
            last_model_val = hist_pred.iloc[-1]

    except Exception as e:
        return pd.DataFrame(), {"error": str(e)}

    if hist_pred is None: return pd.DataFrame(), {}

    # --- ANCHORING (Correction de continuité) ---
    # On calcule le saut entre la réalité et le modèle
    offset = last_actual_price - last_model_val
    
    # On applique ce saut à la prédiction future pour qu'elle colle au prix actuel
    future_adjusted = future_raw + offset

    # --- METRICS (Sur historique brut pour honnêteté) ---
    mae = mean_absolute_error(y, hist_pred)
    rmse = np.sqrt(mean_squared_error(y, hist_pred))
    r2 = r2_score(y, hist_pred)
    
    metrics = {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    }

    # --- CONFIDENCE INTERVALS ---
    # On calcule l'écart-type des résidus
    residuals = y - hist_pred
    std_dev = residuals.std()
    
    lower, upper = calculate_confidence_interval(std_dev, future_adjusted, days_ahead)
    
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast': future_adjusted, # Prédiction lissée
        'Lower': lower,
        'Upper': upper
    })
    
    return forecast_df, metrics