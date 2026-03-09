"""
Fibonacci Swing Trade Analyzer
Aplicação para análise técnica automática com Retração de Fibonacci

Autor: Fibonacci Swing Trade Analyzer
Data: 2024
Licença: MIT
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Tuple, Dict, List

# ==================== FUNÇÕES UTILITÁRIAS ====================

def detect_pivot_points(df: pd.DataFrame, left_bars: int = 5, right_bars: int = 5) -> pd.DataFrame:
    """Identifica Pontos de Pivô (Swing High e Swing Low)"""
    df = df.copy()
    df = df.reset_index(drop=True)
    df['PivotHigh'] = np.nan
    df['PivotLow'] = np.nan
    
    for i in range(left_bars, len(df) - right_bars):
        if df['High'].iloc[i] == df['High'].iloc[i-right_bars:i+right_bars+1].max():
            df.loc[i, 'PivotHigh'] = df['High'].iloc[i]
    
    for i in range(left_bars, len(df) - right_bars):
        if df['Low'].iloc[i] == df['Low'].iloc[i-right_bars:i+right_bars+1].min():
            df.loc[i, 'PivotLow'] = df['Low'].iloc[i]
    
    return df


def find_last_significant_pivots(df: pd.DataFrame, min_distance: int = 20) -> Tuple[float, float, int, int]:
    """Encontra os últimos pivôs significativos para traçar Fibonacci"""
    df = df.reset_index(drop=True)
    
    pivot_highs = df[df['PivotHigh'].notna()]
    pivot_lows = df[df['PivotLow'].notna()]
    
    if pivot_highs.empty or pivot_lows.empty:
        high_idx = df['High'].idxmax()
        low_idx = df['Low'].idxmin()
        return float(df.loc[high_idx, 'High']), float(df.loc[low_idx, 'Low']), int(high_idx), int(low_idx)
    
    last_high = pivot_highs.iloc[-1]
    last_low = pivot_lows.iloc[-1]
    
    high_idx = int(last_high.name)
    low_idx = int(last_low.name)
    
    if abs(high_idx - low_idx) < min_distance:
        if len(pivot_highs) > 1:
            last_high = pivot_highs.iloc[-2]
            high_idx = int(last_high.name)
        if len(pivot_lows) > 1:
            last_low = pivot_lows.iloc[-2]
            low_idx = int(last_low.name)
    
    return float(last_high['PivotHigh']), float(last_low['PivotLow']), high_idx, low_idx


def calculate_fibonacci_levels(high: float, low: float, trend: str) -> Dict[str, float]:
    """Calcula os níveis de Fibonacci"""
    diff = high - low
    
    if trend == 'ALTA':
        levels = {
            "0% (Fundo)": low,
            "23.6%": low + 0.236 * diff,
            "38.2%": low + 0.382 * diff,
            "50%": low + 0.5 * diff,
            "61.8% (Zona de Ouro)": low + 0.618 * diff,
            "78.6%": low + 0.786 * diff,
            "100% (Topo)": high,
            "127.2% (Extensão)": high + 0.272 * diff,
            "161.8% (Extensão)": high + 0.618 * diff
        }
    else:
        levels = {
            "0% (Topo)": high,
            "23.6%": high - 0.236 * diff,
            "38.2%": high - 0.382 * diff,
            "50%": high - 0.5 * diff,
            "61.8% (Zona de Ouro)": high - 0.618 * diff,
            "78.6%": high - 0.786 * diff,
            "100% (Fundo)": low,
            "12
