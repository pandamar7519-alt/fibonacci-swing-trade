# 📈 Fibonacci Swing Trade Analyzer

Aplicação web para análise técnica automática de ações usando **Retração de Fibonacci** e **Pontos de Pivô**, desenvolvida para operações de **Swing Trade**.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🎯 Funcionalidades

- ✅ **Identificação Automática de Tendência** (Curto e Longo Prazo)
- ✅ **Detecção de Pivot Points** (Swing High e Swing Low)
- ✅ **Cálculo Automático de Fibonacci** (Retração e Extensão)
- ✅ **Sinais de Compra/Venda** com Preço Ideal, Stop Loss e Take Profit
- ✅ **Relação Risco/Retorno** calculada automaticamente
- ✅ **Gráficos Interativos** com Plotly
- ✅ **Checklist Operacional** para validar a operação

---

## 🚀 Como Usar

### Opção 1: Streamlit Cloud (Recomendado)

1. Faça fork deste repositório
2. Acesse [share.streamlit.io](https://share.streamlit.io/)
3. Conecte seu GitHub e selecione o repositório
4. O app será deployado automaticamente!

### Opção 2: Localmente

```bash
# Clone o repositório
git clone https://github.com/SEU-USUARIO/fibonacci-swing-trade.git
cd fibonacci-swing-trade

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Execute o aplicativo
streamlit run app.py
