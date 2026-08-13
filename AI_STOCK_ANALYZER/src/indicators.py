import pandas as pd
import numpy as np

def calculate_cpr(df: pd.DataFrame) -> pd.DataFrame:
    df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['BC'] = (df['High'] + df['Low']) / 2
    df['TC'] = (df['Pivot'] - df['BC']) + df['Pivot']
    df['CPR_Width'] = abs(df['TC'] - df['BC']) / df['Pivot'] * 100
    return df

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    df['Vol_SMA_50'] = df['Volume'].rolling(window=50).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Vol_SMA_50']
    
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    return df
