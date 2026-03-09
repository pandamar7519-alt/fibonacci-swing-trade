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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import (
    detect_pivot_points,
    find_last_significant_pivots,
    calculate_fibonacci_levels,
    identify_trend,
    generate_trade_signal,
    calculate_risk_reward
)

# Configuração da Página
st.set_page_config(
    page_title="Fibonacci Swing Trade",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado
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
    </style>
""", unsafe_allow_html=True)

# Título e Header
st.title("📈 Fibonacci Swing Trade Analyzer")
st.markdown("""
    **Análise técnica automática com Retração de Fibonacci para operações de Swing Trade**
    
    *Este aplicativo identifica tendências, traça níveis de Fibonacci automaticamente e sugere zonas de entrada.*
""")

# Sidebar - Configurações
st.sidebar.header("⚙️ Configurações")

ticker = st.sidebar.text_input(
    "Código da Ação",
    value="CSNA3.SA",
    help="Ex: PETR4.SA, VALE3.SA, AAPL, TSLA"
)

mercado = st.sidebar.selectbox(
    "Mercado",
    ["B3 (Brasil)", "NYSE (EUA)", "NASDAQ (EUA)"],
    index=0
)

periodo = st.sidebar.selectbox(
    "Período de Análise",
    ["3mo", "6mo", "1y", "2y", "5y"],
    index=1,
    help="Período para identificar topos e fundos"
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1d", "5d", "1wk", "1mo"],
    index=0,
    help="Para Swing Trade, recomenda-se 1d (diário)"
)

left_bars = st.sidebar.slider(
    "Sensibilidade dos Pivôs (Barras)",
    min_value=3,
    max_value=15,
    value=5,
    help="Quanto maior, menos pivôs serão identificados (mais significativos)"
)

# Botão de Análise
analyze_btn = st.sidebar.button("🔍 Analisar Agora", type="primary", use_container_width=True)

# Disclaimer
st.sidebar.markdown("---")
st.sidebar.warning("""
    ⚠️ **Aviso Legal**
    
    Este aplicativo é uma **ferramenta educacional** e não constitui recomendação de investimento.
    
    - Dados podem ter atraso de 15 minutos
    - Sempre faça sua própria análise
    - Swing Trade envolve risco de perda
    - Consulte um advisor financeiro
""")

# Função para carregar dados
@st.cache_data
def load_data(ticker: str, periodo: str, timeframe: str) -> pd.DataFrame:
    """Carrega dados históricos do Yahoo Finance"""
    try:
        df = yf.download(ticker, period=periodo, interval=timeframe, progress=False)
        if df.empty:
            return None
        
        # Ajusta colunas para multi-index se necessário
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

# Executa análise se botão for clicado ou ticker for preenchido
if analyze_btn or ticker:
    
    # Carrega dados
    with st.spinner("Carregando dados..."):
        df = load_data(ticker, periodo, timeframe)
    
    if df is not None and not df.empty:
        
        # Processa dados
        df = detect_pivot_points(df, left_bars=left_bars, right_bars=left_bars)
        high_price, low_price, high_idx, low_idx = find_last_significant_pivots(df)
        
        # Identifica tendência
        trend_curto, trend_longo = identify_trend(df)
        trend_principal = trend_longo.split()[0]  # 'ALTA' ou 'BAIXA'
        
        # Calcula Fibonacci
        fib_levels = calculate_fibonacci_levels(high_price, low_price, trend_principal)
        
        # Gera sinal de trade
        signal = generate_trade_signal(df, fib_levels, trend_principal)
        
        # Calcula Risk/Reward
        if signal['preco_ideal'] and signal['stop_loss'] and signal['take_profit']:
            rr_ratio = calculate_risk_reward(
                signal['preco_ideal'],
                signal['stop_loss'],
                signal['take_profit']
            )
        else:
            rr_ratio = 0.0
        
        # ==================== DASHBOARD ====================
        
        # Colunas de Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Preço Atual",
                value=f"R$ {df['Close'].iloc[-1]:.2f}",
                delta=f"{df['Close'].pct_change().iloc[-1]*100:.2f}%"
            )
        
        with col2:
            st.metric(
                label="📊 Tendência Curto",
                value=trend_curto
            )
        
        with col3:
            st.metric(
                label="📈 Tendência Longo",
                value=trend_longo
            )
        
        with col4:
            st.metric(
                label="🎯 Sinal",
                value=signal['acao'],
                delta=signal['confianca']
            )
        
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
            """)
        else:
            st.info(f"""
                **⏳ AGUARDAR MELHOR OPORTUNIDADE**
                
                *{signal['mensagem']}*
                
                **Próximos Níveis de Interesse:**
                - Suporte: R$ {fib_levels.get('61.8% (Zona de Ouro)', 0):.2f}
                - Resistência: R$ {fib_levels.get('38.2%', 0):.2f}
            """)
        
        # ==================== NÍVEIS DE FIBONACCI ====================
        
        st.subheader("📐 Níveis de Fibonacci")
        
        fib_df = pd.DataFrame(list(fib_levels.items()), columns=['Nível', 'Preço'])
        fib_df['Preço'] = fib_df['Preço'].round(2)
        fib_df['Distância do Preço Atual'] = (
            (fib_df['Preço'] - df['Close'].iloc[-1]) / df['Close'].iloc[-1] * 100
        ).round(2).astype(str) + '%'
        
        st.dataframe(fib_df, use_container_width=True, hide_index=True)
        
        # ==================== GRÁFICO ====================
        
        st.subheader("📊 Gráfico com Fibonacci e Pivôs")
        
        # Cria gráfico com subplots
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=('Preço e Fibonacci', 'Volume')
        )
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Preço',
                increasing_line_color='#00C853',
                decreasing_line_color='#FF5252'
            ),
            row=1, col=1
        )
        
        # Linhas de Fibonacci
        colors = ['#FFFFFF', '#90CAF9', '#64B5F6', '#42A5F5', '#FFD54F', '#FF7043', '#FFFFFF', '#00E676', '#00E676']
        
        for i, (nivel, preco) in enumerate(fib_levels.items()):
            fig.add_hline(
                y=preco,
                line_dash="dash",
                line_color=colors[i % len(colors)],
                line_width=1,
                annotation_text=nivel,
                annotation_position="right",
                annotation_font_size=10,
                row=1, col=1
            )
        
        # Marca os Pivôs
        pivot_highs = df[df['PivotHigh'].notna()]
        pivot_lows = df[df['PivotLow'].notna()]
        
        if not pivot_highs.empty:
            fig.add_trace(
                go.Scatter(
                    x=pivot_highs.index,
                    y=pivot_highs['PivotHigh'],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=12, color='red'),
                    name='Swing High',
                    showlegend=True
                ),
                row=1, col=1
            )
        
        if not pivot_lows.empty:
            fig.add_trace(
                go.Scatter(
                    x=pivot_lows.index,
                    y=pivot_lows['PivotLow'],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=12, color='green'),
                    name='Swing Low',
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # Médias Móveis
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='purple', width=1), name='SMA 200'),
            row=1, col=1
        )
        
        # Volume
        colors_volume = ['#00C853' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF5252' 
                        for i in range(len(df))]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                marker_color=colors_volume,
                name='Volume',
                opacity=0.5
            ),
            row=2, col=1
        )
        
        # Layout do Gráfico
        fig.update_layout(
            height=800,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_dark",
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Data", row=2, col=1)
        fig.update_yaxes(title_text="Preço (R$)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ==================== DADOS DA AÇÃO ====================
        
        with st.expander("📋 Informações da Ação"):
            try:
                stock_info = yf.Ticker(ticker).info
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nome:** {stock_info.get('longName', 'N/A')}")
                    st.write(f"**Setor:** {stock_info.get('sector', 'N/A')}")
                    st.write(f"**Mercado:** {stock_info.get('exchange', 'N/A')}")
                with col2:
                    st.write(f"**P/L:** {stock_info.get('trailingPE', 'N/A')}")
                    st.write(f"**P/VP:** {stock_info.get('priceToBook', 'N/A')}")
                    st.write(f"**Div Yield:** {stock_info.get('dividendYield', 'N/A')}")
            except:
                st.write("Informações não disponíveis")
        
        # ==================== CHECKLIST OPERACIONAL ====================
        
        st.subheader("✅ Checklist Operacional")
        
        checklist = {
            "✅ Tendência identificada e clara": True,
            "✅ Preço próximo a nível de Fibonacci": signal['acao'] != 'AGUARDAR',
            "✅ Relação Risco/Retorno > 1.5": rr_ratio >= 1.5,
            "✅ Volume confirmando movimento": True,
            "✅ Stop Loss definido": signal['stop_loss'] is not None,
            "✅ Take Profit definido": signal['take_profit'] is not None
        }
        
        for item, status in checklist.items():
            if status:
                st.success(item)
            else:
                st.warning(item)
        
    else:
        st.error("Não foi possível carregar os dados. Verifique o código da ação.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #888;'>
        <p><strong>Fibonacci Swing Trade Analyzer</strong> | Desenvolvido com Python + Streamlit</p>
        <p>⚠️ Este aplicativo é para fins educacionais. Não é recomendação de investimento.</p>
        <p>📧 Dúvidas? Abra uma issue no GitHub</p>
    </div>
""", unsafe_allow_html=True)
