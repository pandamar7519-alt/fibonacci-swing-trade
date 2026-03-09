"""
Módulo de utilitários para análise técnica com Fibonacci
Autor: Fibonacci Swing Trade Analyzer
Data: 2024
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List


def detect_pivot_points(df: pd.DataFrame, left_bars: int = 5, right_bars: int = 5) -> pd.DataFrame:
    """
    Identifica Pontos de Pivô (Swing High e Swing Low) usando algoritmo de Pivot Points.
    """
    df = df.copy()
    df['PivotHigh'] = np.nan
    df['PivotLow'] = np.nan
    
    # Reset index para usar posições inteiras
    df = df.reset_index(drop=True)
    
    # Swing High: máxima maior que as N barras antes e depois
    for i in range(left_bars, len(df) - right_bars):
        if df['High'].iloc[i] == df['High'].iloc[i-right_bars:i+right_bars+1].max():
            df.loc[i, 'PivotHigh'] = df['High'].iloc[i]
    
    # Swing Low: mínima menor que as N barras antes e depois
    for i in range(left_bars, len(df) - right_bars):
        if df['Low'].iloc[i] == df['Low'].iloc[i-right_bars:i+right_bars+1].min():
            df.loc[i, 'PivotLow'] = df['Low'].iloc[i]
    
    return df


def find_last_significant_pivots(df: pd.DataFrame, min_distance: int = 20) -> Tuple[float, float, int, int]:
    """
    Encontra os últimos pivôs significativos (topo e fundo) para traçar Fibonacci.
    """
    # Garante que o index é numérico (posições inteiras)
    df = df.reset_index(drop=True)
    
    pivot_highs = df[df['PivotHigh'].notna()]
    pivot_lows = df[df['PivotLow'].notna()]
    
    # Fallback se não encontrar pivôs
    if pivot_highs.empty or pivot_lows.empty:
        high_idx = df['High'].idxmax()
        low_idx = df['Low'].idxmin()
        return float(df.loc[high_idx, 'High']), float(df.loc[low_idx, 'Low']), int(high_idx), int(low_idx)
    
    # Pega o último topo e fundo
    last_high = pivot_highs.iloc[-1]
    last_low = pivot_lows.iloc[-1]
    
    # Converte para posição inteira
    high_idx = int(last_high.name)
    low_idx = int(last_low.name)
    
    # Garante distância mínima entre eles
    if abs(high_idx - low_idx) < min_distance:
        # Busca o anterior se estiver muito perto
        if len(pivot_highs) > 1:
            last_high = pivot_highs.iloc[-2]
            high_idx = int(last_high.name)
        if len(pivot_lows) > 1:
            last_low = pivot_lows.iloc[-2]
            low_idx = int(last_low.name)
    
    return float(last_high['PivotHigh']), float(last_low['PivotLow']), high_idx, low_idx


def calculate_fibonacci_levels(high: float, low: float, trend: str) -> Dict[str, float]:
    """
    Calcula os níveis de Fibonacci baseados no topo e fundo identificados.
    """
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
            "127.2% (Extensão)": low - 0.272 * diff,
            "161.8% (Extensão)": low - 0.618 * diff
        }
    
    return levels


def identify_trend(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Identifica a tendência atual usando múltiplos indicadores.
    """
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    preco_atual = float(df['Close'].iloc[-1])
    sma20 = float(df['SMA20'].iloc[-1]) if not pd.isna(df['SMA20'].iloc[-1]) else 0
    sma50 = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else 0
    sma200 = float(df['SMA200'].iloc[-1]) if not pd.isna(df['SMA200'].iloc[-1]) else 0
    
    # Tendência de Longo Prazo
    if preco_atual > sma200:
        tendencia_longo = "ALTA"
        icon_longo = "🟢"
    else:
        tendencia_longo = "BAIXA"
        icon_longo = "🔴"
    
    # Tendência de Curto Prazo
    if preco_atual > sma20 and sma20 > sma50:
        tendencia_curto = "ALTA"
        icon_curto = "🟢"
    elif preco_atual < sma20 and sma20 < sma50:
        tendencia_curto = "BAIXA"
        icon_curto = "🔴"
    else:
        tendencia_curto = "LATERAL"
        icon_curto = "🟡"
    
    return f"{tendencia_curto} {icon_curto}", f"{tendencia_longo} {icon_longo}"


def generate_trade_signal(df: pd.DataFrame, fib_levels: Dict[str, float], trend: str) -> Dict:
    """
    Gera sinais de compra/venda baseados nos níveis de Fibonacci e tendência.
    """
    preco_atual = float(df['Close'].iloc[-1])
    
    signal = {
        'acao': 'AGUARDAR',
        'preco_ideal': None,
        'stop_loss': None,
        'take_profit': None,
        'confianca': 'BAIXA',
        'mensagem': ''
    }
    
    if trend == 'ALTA':
        nivel_38 = fib_levels.get("38.2%", 0)
        nivel_50 = fib_levels.get("50%", 0)
        nivel_61 = fib_levels.get("61.8% (Zona de Ouro)", 0)
        
        if nivel_61 <= preco_atual <= nivel_50:
            signal['acao'] = 'COMPRA'
            signal['preco_ideal'] = nivel_61
            signal['stop_loss'] = nivel_50 * 0.97
            signal['take_profit'] = fib_levels.get("100% (Topo)", 0)
            signal['confianca'] = 'ALTA'
            signal['mensagem'] = 'Preço na Zona de Ouro (61.8%). Boa oportunidade de compra.'
        elif nivel_50 < preco_atual <= nivel_38:
            signal['acao'] = 'COMPRA'
            signal['preco_ideal'] = nivel_50
            signal['stop_loss'] = nivel_61 * 0.97
            signal['take_profit'] = fib_levels.get("127.2% (Extensão)", 0)
            signal['confianca'] = 'MÉDIA'
            signal['mensagem'] = 'Preço em retração moderada. Oportunidade de compra.'
        elif preco_atual > fib_levels.get("100% (Topo)", 0):
            signal['acao'] = 'AGUARDAR'
            signal['mensagem'] = 'Preço acima do topo. Aguardar nova retração ou rompimento confirmado.'
        else:
            signal['acao'] = 'AGUARDAR'
            signal['mensagem'] = 'Preço muito acima dos níveis de Fibonacci. Aguardar retração.'
    
    else:  # Tendência de BAIXA
        nivel_3
