"""
Fibonacci Swing Trade Analyzer v2.0
Aplicação para análise técnica automática com Retração de Fibonacci e Volatilidade

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
            "127.2% (Extensao)": high + 0.272 * diff,
            "161.8% (Extensao)": high + 0.618 * diff
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
            "127.2% (Extensao)": low - 0.272 * diff,
            "161.8% (Extensao)": low - 0.618 * diff
        }
    
    return levels


def identify_trend(df: pd.DataFrame) -> Tuple[str, str]:
    """Identifica a tendência atual - ADICIONA as colunas SMA no DataFrame"""
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    preco_atual = float(df['Close'].iloc[-1])
    sma20 = float(df['SMA20'].iloc[-1]) if not pd.isna(df['SMA20'].iloc[-1]) else 0
    sma50 = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else 0
    sma200 = float(df['SMA200'].iloc[-1]) if not pd.isna(df['SMA200'].iloc[-1]) else 0
    
    if preco_atual > sma200:
        tendencia_longo = "ALTA"
        icon_longo = "🟢"
    else:
        tendencia_longo = "BAIXA"
        icon_longo = "🔴"
    
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


def check_volatility(df: pd.DataFrame, window: int = 20) -> Dict[str, any]:
    """
    Calcula e analisa a volatilidade do ativo
    
    Returns:
        Dict com:
        - volatilidade_anualizada (float)
        - classificacao (str)
        - recomendacao (str)
        - cor (str para UI)
    """
    returns = df['Close'].pct_change()
    vol = returns.rolling(window).std() * (252**0.5)  # Volatilidade anualizada
    vol_atual = vol.iloc[-1] if not pd.isna(vol.iloc[-1]) else 0
    
    if vol_atual > 0.6:  # >60% ao ano
        classificacao = "MUITO ALTA"
        icon = "🔴"
        recomendacao = "⚠️ Aumente sensibilidade dos pivôs para 7-10 barras. Risco elevado!"
        cor = "error"
    elif vol_atual > 0.4:  # >40% ao ano
        classificacao = "ALTA"
        icon = "🟠"
        recomendacao = "⚠️ Considere aumentar sensibilidade dos pivôs para 7 barras"
        cor = "warning"
    elif vol_atual > 0.25:  # >25% ao ano
        classificacao = "MODERADA"
        icon = "🟡"
        recomendacao = "✅ Volatilidade dentro do esperado para Swing Trade"
        cor = "info"
    else:
        classificacao = "BAIXA"
        icon = "🟢"
        recomendacao = "✅ Baixa volatilidade. Pode reduzir sensibilidade para 3-4 barras"
        cor = "success"
    
    return {
        'volatilidade_anualizada': vol_atual,
        'classificacao': classificacao,
        'icon': icon,
        'recomendacao': recomendacao,
        'cor': cor
    }


def generate_trade_signal(df: pd.DataFrame, fib_levels: Dict[str, float], trend: str, volatility: Dict[str, any]) -> Dict:
    """Gera sinais de compra/venda considerando volatilidade"""
    preco_atual = float(df['Close'].iloc[-1])
    
    signal = {
        'acao': 'AGUARDAR',
        'preco_ideal': None,
        'stop_loss': None,
        'take_profit': None,
        'confianca': 'BAIXA',
        'mensagem': '',
        'ajuste_volatilidade': ''
    }
    
    # Ajusta confiança baseado na volatilidade
    if volatility['classificacao'] in ['MUITO ALTA', 'ALTA']:
        ajuste_confianca = -1  # Reduz confiança em alta volatilidade
        signal['ajuste_volatilidade'] = '⚠️ Confiança reduzida devido à alta volatilidade'
    elif volatility['classificacao'] == 'BAIXA':
        ajuste_confianca = 1  # Aumenta confiança em baixa volatilidade
        signal['ajuste_volatilidade'] = '✅ Confiança aumentada devido à baixa volatilidade'
    else:
        ajuste_confianca = 0
        signal['ajuste_volatilidade'] = ''
    
    if trend == 'ALTA':
        nivel_38 = fib_levels.get("38.2%", 0)
        nivel_50 = fib_levels.get("50%", 0)
        nivel_61 = fib_levels.get("61.8% (Zona de Ouro)", 0)
        
        if nivel_61 <= preco_atual <= nivel_50:
            signal['acao'] = 'COMPRA'
            signal['preco_ideal'] = nivel_61
            # Ajusta stop loss baseado na volatilidade
            if volatility['classificacao'] in ['MUITO ALTA', 'ALTA']:
                signal['stop_loss'] = nivel_50 * 0.95  # Stop mais largo
            else:
                signal['stop_loss'] = nivel_50 * 0.97
            signal['take_profit'] = fib_levels.get("100% (Topo)", 0)
            signal['confianca'] = 'ALTA' if ajuste_confianca >= 0 else 'MEDIA'
            signal['mensagem'] = 'Preco na Zona de Ouro (61.8%). Boa oportunidade de compra.'
        elif nivel_50 < preco_atual <= nivel_38:
            signal['acao'] = 'COMPRA'
            signal['preco_ideal'] = nivel_50
            if volatility['classificacao'] in ['MUITO ALTA', 'ALTA']:
                signal['stop_loss'] = nivel_61 * 0.95
            else:
                signal['stop_loss'] = nivel_61 * 0.97
            signal['take_profit'] = fib_levels.get("127.2% (Extensao)", 0)
            signal['confianca'] = 'MEDIA'
            signal['mensagem'] = 'Preco em retracao moderada. Oportunidade de compra.'
        elif preco_atual > fib_levels.get("100% (Topo)", 0):
            signal['acao'] = 'AGUARDAR'
            signal['mensagem'] = 'Preco acima do topo. Aguardar nova retracao ou rompimento confirmado.'
        else:
            signal['acao'] = 'AGUARDAR'
            signal['mensagem'] = 'Preco muito acima dos niveis de Fibonacci. Aguardar retracao.'
    
    else:  # Tendência de BAIXA
        nivel_38 = fib_levels.get("38.2%", 0)
        nivel_50 = fib_levels.get("50%", 0)
        nivel_61 = fib_levels.get("61.8% (Zona de Ouro)", 0)
        
        if nivel_50 <= preco_atual <= nivel_61:
            signal['acao'] = 'VENDA'
            signal['preco_ideal'] = nivel_61
            if volatility['classificacao'] in ['MUITO ALTA', 'ALTA']:
                signal['stop_loss'] = nivel_50 * 1.05  # Stop mais largo
            else:
                signal['stop_loss'] = nivel_50 * 1.03
            signal['take_profit'] = fib_levels.get("100% (Fundo)", 0)
            signal['confianca'] = 'ALTA' if ajuste_confianca >= 0 else 'MEDIA'
            signal['mensagem'] = 'Preco na Zona de Ouro (61.8%). Boa oportunidade de venda.'
        elif nivel_38 <= preco_atual < nivel_50:
            signal['acao'] = 'VENDA'
            signal['preco_ideal'] = nivel_50
            if volatility['classificacao'] in ['MUITO ALTA', 'ALTA']:
                signal['stop_loss'] = nivel_61 * 1.05
            else:
                signal['stop_loss'] = nivel_61 * 1.03
            signal['take_profit'] = fib_levels.get("127.2% (Extensao)", 0)
            signal['confianca'] = 'MEDIA'
            signal['mensagem'] = 'Preco em repique moderado. Oportunidade de venda.'
        elif preco_atual < fib_levels.get("100% (Fundo)", 0):
            signal['acao'] = 'AGUARDAR'
            signal['mensagem'] = 'Preco abaixo do fundo. Aguardar novo repique ou rompimento confirmado.'
        else:
            signal['acao'] = 'AGUARDAR'
            signal['mensagem'] = 'Preco muito abaixo dos niveis de Fibonacci. Aguardar repique.'
    
    return signal


def calculate_risk_reward(entry: float, stop: float, target: float) -> float:
    """Calcula a relação Risco/Retorno"""
    if entry is None or stop is None or target is None:
        return 0.0
    
    risk = abs(entry - stop)
    reward = abs(target - entry)
    
    if risk == 0:
        return 0.0
    
    return round(reward / risk, 2)


def export_to_csv(df: pd.DataFrame, fib_levels: Dict, signal: Dict, ticker: str) -> str:
    """Gera CSV para download com análise completa"""
    export_data = {
        'Ticker': ticker,
        'Data_Analise': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
        'Preco_Atual': df['Close'].iloc[-1],
        'Sinal': signal['acao'],
        'Preco_Entrada': signal['preco_ideal'] if signal['preco_ideal'] else 'N/A',
        'Stop_Loss': signal['stop_loss'] if signal['stop_loss'] else 'N/A',
        'Take_Profit': signal['take_profit'] if signal['take_profit'] else 'N/A',
    }
    
    for nivel, preco in fib_levels.items():
        export_data[f'Fib_{nivel}'] = round(preco, 2)
    
    csv_data = pd.DataFrame([export_data])
    return csv_data.to_csv(index=False).encode('utf-8')

# ==================== APLICAÇÃO PRINCIPAL ====================

st.set_page_config(
    page_title="Fibonacci Swing Trade Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .stAlert {
        border-radius: 10px;
    }
    .volatility-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .volatility-normal {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Fibonacci Swing Trade Analyzer Pro v2.0")
st.markdown("""
    **Análise técnica automática com Retração de Fibonacci, Volatilidade e Pivôs para Swing Trade**
    
    *Este aplicativo identifica tendências, calcula volatilidade, traça níveis de Fibonacci e sugere zonas de entrada.*
""")

# Sidebar
st.sidebar.header("⚙️ Configurações")

ticker = st.sidebar.text_input("Código da Ação", value="CSNA3.SA", help="Ex: PETR4.SA, VALE3.SA, AAPL, TSLA")

periodo = st.sidebar.selectbox("Período de Análise", ["3mo", "6mo", "1y", "2y", "5y"], index=1)

timeframe = st.sidebar.selectbox("Timeframe", ["1d", "5d", "1wk", "1mo"], index=0)

left_bars = st.sidebar.slider("Sensibilidade dos Pivôs (Barras)", min_value=3, max_value=15, value=5)

show_volatility = st.sidebar.checkbox("Mostrar Análise de Volatilidade", value=True)

analyze_btn = st.sidebar.button("🔍 Analisar Agora", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.warning("""
    ⚠️ **Aviso Legal**
    
    Este aplicativo é uma **ferramenta educacional** e não constitui recomendação de investimento.
    
    - Dados podem ter atraso de 15 minutos
    - Sempre faça sua própria análise
    - Swing Trade envolve risco de perda
    - Consulte um advisor financeiro
""")

@st.cache_data
def load_data(ticker: str, periodo: str, timeframe: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=periodo, interval=timeframe, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

if analyze_btn or ticker:
    
    with st.spinner("Carregando e analisando dados..."):
        df = load_data(ticker, periodo, timeframe)
    
    if df is not None and not df.empty:
        
        # 1. Detectar Pivôs
        df = detect_pivot_points(df, left_bars=left_bars, right_bars=left_bars)
        
        # 2. Encontrar últimos pivôs significativos
        high_price, low_price, high_idx, low_idx = find_last_significant_pivots(df)
        
        # 3. Identificar tendência (ADICIONA as colunas SMA no DataFrame)
        trend_curto, trend_longo = identify_trend(df)
        trend_principal = trend_longo.split()[0]
        
        # 4. Calcular Volatilidade
        volatility = check_volatility(df, window=20)
        
        # 5. Calcular Fibonacci
        fib_levels = calculate_fibonacci_levels(high_price, low_price, trend_principal)
        
        # 6. Gerar sinal de trade (considerando volatilidade)
        signal = generate_trade_signal(df, fib_levels, trend_principal, volatility)
        
        # 7. Calcular Risk/Reward
        if signal['preco_ideal'] and signal['stop_loss'] and signal['take_profit']:
            rr_ratio = calculate_risk_reward(signal['preco_ideal'], signal['stop_loss'], signal['take_profit'])
        else:
            rr_ratio = 0.0
        
        # ==================== MÉTRICAS PRINCIPAIS ====================
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("💰 Preço Atual", f"R$ {df['Close'].iloc[-1]:.2f}", delta=f"{df['Close'].pct_change().iloc[-1]*100:.2f}%")
        
        with col2:
            st.metric("📊 Tendência Curto", value=trend_curto)
        
        with col3:
            st.metric("📈 Tendência Longo", value=trend_longo)
        
        with col4:
            st.metric("🎯 Sinal", value=signal['acao'], delta=signal['confianca'])
        
        with col5:
            st.metric("📉 Volatilidade", value=f"{volatility['classificacao']} {volatility['icon']}", 
                     delta=f"{volatility['volatilidade_anualizada']*100:.1f}% ano")
        
        # ==================== ALERTA DE VOLATILIDADE ====================
        if show_volatility:
            st.subheader("📊 Análise de Volatilidade")
            
            if volatility['classificacao'] in ['MUITO ALTA', 'ALTA']:
                st.warning(f"""
                    **{volatility['icon']} VOLATILIDADE {volatility['classificacao']}**
                    
                    - Volatilidade Anualizada: **{volatility['volatilidade_anualizada']*100:.2f}%**
                    - {volatility['recomendacao']}
                    - Stop Loss ajustado automaticamente para maior proteção
                """)
            elif volatility['classificacao'] == 'MODERADA':
                st.info(f"""
                    **{volatility['icon']} VOLATILIDADE {volatility['classificacao']}**
                    
                    - Volatilidade Anualizada: **{volatility['volatilidade_anualizada']*100:.2f}%**
                    - {volatility['recomendacao']}
                """)
            else:
                st.success(f"""
                    **{volatility['icon']} VOLATILIDADE {volatility['classificacao']}**
                    
                    - Volatilidade Anualizada: **{volatility['volatilidade_anualizada']*100:.2f}%**
                    - {volatility['recomendacao']}
                """)
        
        # ==================== SINAL DE TRADE ====================
        st.subheader("🎯 Sinal de Operação")
        
        if signal['acao'] == 'COMPRA':
            st.success(f"""
                **✅ OPORTUNIDADE DE COMPRA**
                
                - **Preço Ideal de Entrada:** R$ {signal['preco_ideal']:.2f}
                - **Stop Loss:** R$ {signal['stop_loss']:.2f}
                - **Take Profit:** R$ {signal['take_profit']:.2f}
                - **Relação Risco/Retorno:** {rr_ratio}:1
                - **Confiança:** {signal['confianca']}
                
                *{signal['mensagem']}*
                
                {signal['ajuste_volatilidade']}
            """)
        elif signal['acao'] == 'VENDA':
            st.error(f"""
                **🔻 OPORTUNIDADE DE VENDA**
                
                - **Preço Ideal de Entrada:** R$ {signal['preco_ideal']:.2f}
                - **Stop Loss:** R$ {signal['stop_loss']:.2f}
                - **Take Profit:** R$ {signal['take_profit']:.2f}
                - **Relação Risco/Retorno:** {rr_ratio}:1
                - **Confiança:** {signal['confianca']}
                
                *{signal['mensagem']}*
                
                {signal['ajuste_volatilidade']}
            """)
        else:
            st.info(f"""
                **⏳ AGUARDAR MELHOR OPORTUNIDADE**
                
                *{signal['mensagem']}*
                
                **Próximos Níveis de Interesse:**
                - Suporte: R$ {fib_levels.get('61.8% (Zona de Ouro)', 0):.2f}
                - Resistência: R$ {fib_levels.get('38.2%', 0):.2f}
                
                {signal['ajuste_volatilidade']}
            """)
        
        # ==================== NÍVEIS DE FIBONACCI ====================
        st.subheader("📐 Níveis de Fibonacci")
        
        fib_df = pd.DataFrame(list(fib_levels.items()), columns=['Nível', 'Preço'])
        fib_df['Preço'] = fib_df['Preço'].round(2)
        fib_df['Distância do Preço Atual'] = ((fib_df['Preço'] - df['Close'].iloc[-1]) / df['Close'].iloc[-1] * 100).round(2).astype(str) + '%'
        
        st.dataframe(fib_df, use_container_width=True, hide_index=True)
        
        # ==================== BOTÃO DE EXPORTAÇÃO ====================
        st.subheader("💾 Exportar Análise")
        
        csv_data = export_to_csv(df, fib_levels, signal, ticker)
        
        st.download_button(
            label="📥 Baixar Análise em CSV",
            data=csv_data,
            file_name=f"analise_{ticker}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # ==================== GRÁFICO ====================
        st.subheader("📊 Gráfico com Fibonacci e Pivôs")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3], subplot_titles=('Preço e Fibonacci', 'Volume'))
        
        # Candlestick
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Preço', increasing_line_color='#00C853', decreasing_line_color='#FF5252'), row=1, col=1)
        
        # Linhas de Fibonacci
        colors = ['#FFFFFF', '#90CAF9', '#64B5F6', '#42A5F5', '#FFD54F', '#FF7043', '#FFFFFF', '#00E676', '#00E676']
        
        for i, (nivel, preco) in enumerate(fib_levels.items()):
            fig.add_hline(y=preco, line_dash="dash", line_color=colors[i % len(colors)], line_width=1, annotation_text=nivel, annotation_position="right", annotation_font_size=10, row=1, col=1)
        
        # Pivôs
        pivot_highs = df[df['PivotHigh'].notna()]
        pivot_lows = df[df['PivotLow'].notna()]
        
        if not pivot_highs.empty:
            fig.add_trace(go.Scatter(x=pivot_highs.index, y=pivot_highs['PivotHigh'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name='Swing High'), row=1, col=1)
        
        if not pivot_lows.empty:
            fig.add_trace(go.Scatter(x=pivot_lows.index, y=pivot_lows['PivotLow'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='green'), name='Swing Low'), row=1, col=1)
        
        # Médias Móveis
        if 'SMA20' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)
        if 'SMA50' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'), row=1, col=1)
        if 'SMA200' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='purple', width=1), name='SMA 200'), row=1, col=1)
        
        # Volume
        colors_volume = ['#00C853' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF5252' for i in range(len(df))]
        
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors_volume, name='Volume', opacity=0.5), row=2, col=1)
        
        # Layout
        fig.update_layout(height=800, xaxis_rangeslider_visible=False, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), template="plotly_dark", hovermode='x unified')
        
        fig.update_xaxes(title_text="Data", row=2, col=1)
        fig.update_yaxes(title_text="Preço (R$)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ==================== CHECKLIST ====================
        st.subheader("✅ Checklist Operacional")
        
        checklist = {
            "✅ Tendência identificada e clara": True,
            "✅ Preço próximo a nível de Fibonacci": signal['acao'] != 'AGUARDAR',
            "✅ Relação Risco/Retorno > 1.5": rr_ratio >= 1.5,
            "✅ Volume confirmando movimento": True,
            "✅ Stop Loss definido": signal['stop_loss'] is not None,
            "✅ Take Profit definido": signal['take_profit'] is not None,
            "✅ Volatilidade dentro do aceitável": volatility['classificacao'] not in ['MUITO ALTA']
        }
        
        for item, status in checklist.items():
            if status:
                st.success(item)
            else:
                st.warning(item)
        
    else:
        st.error("Não foi possível carregar os dados. Verifique o código da ação.")

st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #888;'>
        <p><strong>Fibonacci Swing Trade Analyzer Pro v2.0</strong> | Desenvolvido com Python + Streamlit</p>
        <p>⚠️ Este aplicativo é para fins educacionais. Não é recomendação de investimento.</p>
        <p>📊 Versão com análise de volatilidade e exportação de dados</p>
    </div>
""", unsafe_allow_html=True)
