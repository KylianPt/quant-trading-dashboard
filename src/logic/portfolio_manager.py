import pandas as pd
import numpy as np
import yfinance as yf

class PortfolioManager:
    def __init__(self, tickers):
        """
        Initialize the Portfolio Manager with a list of ticker symbols.
        tickers: list of str (e.g. ['AAPL', 'MSFT', 'GOOG'])
        """
        self.tickers = tickers
        self.data = pd.DataFrame()

    def get_portfolio_data(self, period="2y"):
        """
        Download historical 'Close' prices for the selected tickers.
        Returns a DataFrame where columns are tickers and rows are dates.
        """
        if not self.tickers:
            return pd.DataFrame()

        # Download data with group_by='ticker' to handle structure easily
        # auto_adjust=True ensures we get dividends/splits adjusted prices
        raw_data = yf.download(
            self.tickers, 
            period=period, 
            group_by='ticker', 
            auto_adjust=True,
            progress=False
        )

        # Process data to keep only Close prices
        clean_data = pd.DataFrame()

        if len(self.tickers) == 1:
            # Case: Single ticker (yfinance returns a flat DataFrame)
            ticker = self.tickers[0]
            if not raw_data.empty:
                clean_data[ticker] = raw_data['Close']
        else:
            # Case: Multiple tickers (yfinance returns MultiIndex columns)
            for t in self.tickers:
                try:
                    # Check if the ticker exists in the downloaded data
                    # yfinance structure is usually [Ticker] -> [Open, High, Low, Close...]
                    if t in raw_data.columns:
                        clean_data[t] = raw_data[t]['Close']
                except KeyError:
                    # Handle cases where data might be missing for one asset
                    continue

        # Fill missing values (forward fill then backward fill) to avoid calculation errors
        self.data = clean_data.ffill().bfill()
        
        return self.data

    def calculate_metrics(self, weights):
        """
        Calculate the expected annual return and volatility of the portfolio.
        
        weights: numpy array of floats (must sum to 1)
        
        Returns:
        (expected_return, expected_volatility)
        """
        if self.data.empty:
            return 0.0, 0.0

        # Calculate daily percentage returns
        returns = self.data.pct_change().dropna()

        # Calculate Annualized Covariance Matrix (252 trading days)
        cov_matrix = returns.cov() * 252

        # Calculate Portfolio Variance
        # Formula: w^T * Cov * w
        port_variance = np.dot(weights.T, np.dot(cov_matrix, weights))

        # Calculate Portfolio Volatility (Standard Deviation)
        port_volatility = np.sqrt(port_variance)

        # Calculate Portfolio Expected Annual Return
        # Formula: sum(weight * mean_daily_return) * 252
        # We assume mean historical return is a proxy for expected return
        mean_daily_returns = returns.mean()
        port_return = np.sum(mean_daily_returns * weights) * 252

        return port_return, port_volatility

# --- Test block (Executes only if you run this file directly) ---
if __name__ == "__main__":
    # Example usage for testing
    test_tickers = ["AI.PA", "MC.PA", "TTE.PA"] # Air Liquide, LVMH, Total
    print(f"Testing PortfolioManager with: {test_tickers}")
    
    pm = PortfolioManager(test_tickers)
    df = pm.get_portfolio_data(period="1y")
    
    print(f"Data shape: {df.shape}")
    print("Head of data:")
    print(df.head())
    
    # Test with equal weights
    w = np.array([1/3, 1/3, 1/3])
    ret, vol = pm.calculate_metrics(w)
    
    print("-" * 30)
    print(f"Equal Weights Return: {ret:.2%}")
    print(f"Equal Weights Volatility: {vol:.2%}")