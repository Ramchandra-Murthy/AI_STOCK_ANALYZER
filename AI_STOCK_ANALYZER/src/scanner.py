import pandas as pd
import yfinance as yf
from src.indicators import calculate_technical_indicators, calculate_cpr

def batch_scan_stocks(tickers: list, period: str = "6mo") -> pd.DataFrame:
    print(f"Downloading data for {len(tickers)} symbols...")
    results = []
    
    # Process tickers individually to prevent a single failure from blocking the batch
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, progress=False)
            
            # Handle multi-index columns if returned by yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.dropna(how='all')
            
            if len(df) < 100:
                continue
                
            df = calculate_technical_indicators(df)
            df = calculate_cpr(df)
            
            latest = df.iloc[-1]
            
            is_uptrend = latest['Close'] > latest['SMA_50'] > latest['SMA_200']
            volume_spike = latest['Volume_Ratio'] > 1.5
            narrow_cpr = latest['CPR_Width'] < 0.6
            
            if is_uptrend and (volume_spike or narrow_cpr):
                results.append({
                    'Ticker': ticker,
                    'Close': round(float(latest['Close']), 2),
                    'ATR': round(float(latest['ATR']), 2),
                    'Volume_Ratio': round(float(latest['Volume_Ratio']), 2),
                    'CPR_Width': round(float(latest['CPR_Width']), 2),
                    'Signal_Type': 'BREAKOUT_SETUP' if volume_spike else 'CPR_COMPRESSION'
                })
        except Exception as e:
            print(f"Skipping {ticker}: Error fetching or processing data.")
            continue
            
    return pd.DataFrame(results)
