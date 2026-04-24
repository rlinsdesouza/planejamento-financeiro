import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ──────────────────────────────────────────────
# CONFIGURACAO DA PAGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Planejamento Patrimonial",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────
# CSS PERSONALIZADO
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1F3864 0%, #2E75B6 100%);
        padding: 20px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
    }
    .main-header h1 { color: white; margin: 0; font-size: 28px; }
    .main-header p  { color: #cce0f5; margin: 4px 0 0 0; font-size: 14px; }

    .metric-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }
    .metric-card .label {
        font-size: 12px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-card .value {
        font-size: 22px;
        font-weight: 700;
        color: #1F3864;
    }
    .metric-card .sub {
        font-size: 11px;
        color: #999;
        margin-top: 4px;
    }

    .card-verde  { border-top: 4px solid #4CAF50; }
    .card-azul   { border-top: 4px solid #2E75B6; }
    .card-laranja{ border-top: 4px solid #FF9800; }
    .card-roxo   { border-top: 4px solid #9C27B0; }

    .alerta-verde    { background:#e8f5e9; border-left:4px solid #4CAF50;
                       padding:12px 16px; border-radius:6px; margin:8px 0; }
    .alerta-amarelo  { background:#fff8e1; border-left:4px solid #FF9800;
                       padding:12px 16px; border-radius:6px; margin:8px 0; }
    .alerta-vermelho { background:#ffebee; border-left:4px solid #f44336;
                       padding:12px 16px; border-radius:6px; margin:8px 0; }

    .secao-titulo {
        font-size: 16px;
        font-weight: 700;
        color: #1F3864;
        border-bottom: 2px solid #2E75B6;
        padding-bottom: 6px;
        margin: 20px 0 12px 0;
    }
    div[data-testid="stSidebar"] { background: #f8fafd; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# FUNCOES DE CALCULO
# ──────────────────────────────────────────────
def calcular_rentabilidade_ponderada(carteira):
    return sum(c["perc"] * c["rent"] for c in carteira)


def projetar_patrimonio(patrimonio_ini, rent_real, idade_ini,
                         idade_apos, expectativa_vida,
                         aporte_anual, despesa_anual, perc_heranca):
    ano_ini = 2025
    dados = []
    pat = patrimonio_ini

    for i in range(expectativa_vida - idade_ini + 1):
        idade = idade_ini + i
        ano   = ano_ini + i
        fase  = "Acumulação" if idade < idade_apos else "Distribuição"
        rend  = pat * rent_real
        fluxo = aporte_anual if fase == "Acumulação" else -despesa_anual
        pat_fim = pat + rend + fluxo
        heranca = max(pat_fim * perc_heranca, 0)

        dados.append({
            "Ano":                 ano,
            "Idade":               idade,
            "Fase":                fase,
            "Patrimônio Início":   pat,
            "Rendimento Real":     rend,
            "Aporte/Retirada":     fluxo,
            "Patrimônio Fim":      pat_fim,
            "Herança Estimada":    heranca,
        })
        pat = pat_fim

    return pd.DataFrame(dados)


def formatar_moeda(valor):
    if valor >= 1_000_000:
        return f"R$ {valor/1_000_000:.2f}M"
    elif valor >= 1_000:
        return f"R$ {valor/1_000:.0f}K"
    else:
        return f"R$ {valor:.0f}"


def formatar_moeda_completa(valor):
    return f"R$ {valor:,.0f}".replace(",", ".")


# ──────────────────────────────────────────────
# SIDEBAR — INPUTS
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    st.markdown("---")

    # Dados da família
    st.markdown("### 👨‍👩‍👧 Dados da Família")
    nome_familia = st.text_input("Nome da Família", value="Família Silva")

    col1, col2 = st.columns(2)
    with col1:
        idade_atual = st.number_input(
            "Idade Atual", min_value=18, max_value=80,
            value=45, step=1
        )
    with col2:
        idade_apos = st.number_input(
            "Idade Aposentadoria", min_value=idade_atual + 1,
            max_value=90, value=60, step=1
        )

    expectativa_vida = st.slider(
        "Expectativa de Vida", min_value=idade_apos + 1,
        max_value=100, value=85, step=1
    )

    st.markdown("---")

    # Patrimônio e aportes
    st.markdown("### 💰 Patrimônio e Aportes")
    patrimonio_atual = st.number_input(
        "Patrimônio Atual (R$)",
        min_value=0, value=1_500_000, step=50_000,
        format="%d"
    )
    aporte_mensal = st.number_input(
        "Aporte Mensal (R$)",
        min_value=0, value=5_000, step=500,
        format="%d"
    )

    st.markdown("---")

    # Aposentadoria
    st.markdown("### 🏖️ Aposentadoria")
    despesa_mensal = st.number_input(
        "Despesa Mensal Desejada (R$ de hoje)",
        min_value=0, value=20_000, step=1_000,
        format="%d"
    )

    estrategia = st.selectbox(
        "Estratégia de Uso do Patrimônio",
        ["Misto", "Só Rendimentos", "Consumir Tudo"]
    )

    st.markdown("---")

    # Herança
    st.markdown("### 🏛️ Herança")
    perc_heranca = st.slider(
        "% do Patrimônio a Preservar",
        min_value=0.0, max_value=1.0,
        value=0.5, step=0.05,
        format="%.0f%%",
        help="0% = consumir tudo | 100% = preservar tudo"
    )

    st.markdown("---")

    # Carteira
    st.markdown("### 📊 Composição da Carteira")
    st.caption("Ajuste % de alocação e rentabilidade real por classe")

    classes_default = [
        {"nome": "Renda Fixa (Tesouro/CDB)",       "perc": 0.25, "rent": 0.040},
        {"nome": "Crédito Privado (CRI/CRA/Deb.)", "perc": 0.15, "rent": 0.055},
        {"nome": "Multimercado / Hedge Funds",      "perc": 0.10, "rent": 0.050},
        {"nome": "Fundos Imobiliários (FIIs)",      "perc": 0.15, "rent": 0.060},
        {"nome": "Ações Brasil",                    "perc": 0.20, "rent": 0.070},
        {"nome": "Ações Internacionais / ETFs",     "perc": 0.10, "rent": 0.065},
        {"nome": "Outros (Prev./Alternativos)",     "perc": 0.05, "rent": 0.045},
    ]

    carteira = []
    total_alocado = 0.0

    for ativo in classes_default:
        with st.expander(ativo["nome"], expanded=False):
            p = st.slider(
                f"% Alocação",
                min_value=0.0, max_value=1.0,
                value=ativo["perc"], step=0.01,
                format="%.0f%%",
                key=f"perc_{ativo['nome']}"
            )
            r = st.slider(
                f"Rent. Real Anual",
                min_value=0.0, max_value=0.20,
                value=ativo["rent"], step=0.005,
                format="%.1f%%",
                key=f"rent_{ativo['nome']}"
            )
            carteira.append({
                "nome": ativo["nome"],
                "perc": p,
                "rent": r
            })
            total_alocado += p

    # Validação alocação
    if abs(total_alocado - 1.0) > 0.01:
        st.warning(
            f"⚠️ Alocação total: {total_alocado*100:.1f}%  \n"
            f"Ajuste para somar 100%"
        )
    else:
        st.success(f"✅ Alocação: {total_alocado*100:.1f}%")


# ──────────────────────────────────────────────
# CALCULOS PRINCIPAIS
# ──────────────────────────────────────────────
aporte_anual   = aporte_mensal * 12
despesa_anual  = despesa_mensal * 12
rent_base      = calcular_rentabilidade_ponderada(carteira)
rent_pess      = rent_base - 0.01
rent_otim      = rent_base + 0.01

df_base = projetar_patrimonio(
    patrimonio_atual, rent_base, idade_atual,
    idade_apos, expectativa_vida,
    aporte_anual, despesa_anual, perc_heranca
)
df_pess = projetar_patrimonio(
    patrimonio_atual, rent_pess, idade_atual,
    idade_apos, expectativa_vida,
    aporte_anual, despesa_anual, perc_heranca
)
df_otim = projetar_patrimonio(
    patrimonio_atual, rent_otim, idade_atual,
    idade_apos, expectativa_vida,
    aporte_anual, despesa_anual, perc_heranca
)

# Valores-chave
idx_apos   = idade_apos - idade_atual
pat_apos   = df_base.iloc[idx_apos]["Patrimônio Fim"]
rend_apos  = df_base.iloc[idx_apos]["Rendimento Real"]
pat_85     = df_base.iloc[-1]["Patrimônio Fim"]
pat_p85    = df_pess.iloc[-1]["Patrimônio Fim"]
pat_o85    = df_otim.iloc[-1]["Patrimônio Fim"]
anos_acum  = idade_apos - idade_atual


# ──────────────────────────────────────────────
# HEADER PRINCIPAL
# ──────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>💰 Planejamento Patrimonial — {nome_familia}</h1>
    <p>Projeção patrimonial com cenários de aposentadoria e herança •
       Valores em termos reais (acima da inflação)</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# METRICAS RESUMO
# ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card card-azul">
        <div class="label">Patrimônio Atual</div>
        <div class="value">{formatar_moeda(patrimonio_atual)}</div>
        <div class="sub">Idade atual: {idade_atual} anos</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card card-verde">
        <div class="label">Na Aposentadoria ({idade_apos} anos)</div>
        <div class="value">{formatar_moeda(pat_apos)}</div>
        <div class="sub">Em {anos_acum} anos — cenário base</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    renda_mensal_real = rend_apos / 12
    st.markdown(f"""
    <div class="metric-card card-laranja">
        <div class="label">Renda Mensal Real Gerada</div>
        <div class="value">{formatar_moeda(renda_mensal_real)}</div>
        <div class="sub">Desejada: {formatar_moeda(despesa_mensal)}/mês</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    heranca_est = pat_85 * perc_heranca if pat_85 > 0 else 0
    st.markdown(f"""
    <div class="metric-card card-roxo">
        <div class="label">Herança Estimada</div>
        <div class="value">{formatar_moeda(heranca_est)}</div>
        <div class="sub">{int(perc_heranca*100)}% do patrimônio aos {expectativa_vida} anos</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# ALERTA DE SUSTENTABILIDADE
# ──────────────────────────────────────────────
saldo_cobre = rend_apos >= despesa_anual
deficit_mensal = (despesa_anual - rend_apos) / 12

if pat_85 < 0:
    st.markdown(f"""
    <div class="alerta-vermelho">
        ⚠️ <strong>Atenção:</strong> No cenário base, o patrimônio se esgota antes dos
        {expectativa_vida} anos. Considere aumentar aportes, reduzir despesas ou
        revisar a carteira.
    </div>
    """, unsafe_allow_html=True)
elif saldo_cobre:
    st.markdown(f"""
    <div class="alerta-verde">
        ✅ <strong>Sustentável:</strong> Os rendimentos da carteira ({formatar_moeda(rend_apos/12)}/mês)
        cobrem integralmente a despesa desejada ({formatar_moeda(despesa_mensal)}/mês)
        na aposentadoria. O patrimônio tende a crescer mesmo na fase de distribuição.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="alerta-amarelo">
        ⚠️ <strong>Atenção:</strong> Os rendimentos ({formatar_moeda(rend_apos/12)}/mês)
        não cobrem totalmente a despesa desejada ({formatar_moeda(despesa_mensal)}/mês).
        Será consumido capital principal (~{formatar_moeda(deficit_mensal)}/mês).
        Verifique o cenário pessimista.
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# ABAS PRINCIPAIS
# ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Evolução Patrimonial",
    "🔀 Comparativo de Cenários",
    "💼 Carteira",
    "📋 Projeção Detalhada"
])


# ══════════════════════════════════════════════
# TAB 1 — EVOLUCAO PATRIMONIAL
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="secao-titulo">Evolução do Patrimônio — Cenário Base</div>',
                unsafe_allow_html=True)

    fig1 = go.Figure()

    # Área de acumulação
    df_acum = df_base[df_base["Fase"] == "Acumulação"]
    df_dist = df_base[df_base["Fase"] == "Distribuição"]

    fig1.add_trace(go.Scatter(
        x=df_acum["Idade"], y=df_acum["Patrimônio Fim"],
        fill="tozeroy", fillcolor="rgba(46,117,182,0.15)",
        line=dict(color="#2E75B6", width=2.5),
        name="Acumulação",
        hovertemplate="Idade: %{x}<br>Patrimônio: R$ %{y:,.0f}<extra></extra>"
    ))

    fig1.add_trace(go.Scatter(
        x=df_dist["Idade"], y=df_dist["Patrimônio Fim"],
        fill="tozeroy", fillcolor="rgba(76,175,80,0.15)",
        line=dict(color="#4CAF50", width=2.5),
        name="Distribuição",
        hovertemplate="Idade: %{x}<br>Patrimônio: R$ %{y:,.0f}<extra></extra>"
    ))

    # Linha de herança
    fig1.add_trace(go.Scatter(
        x=df_dist["Idade"], y=df_dist["Herança Estimada"],
        line=dict(color="#9C27B0", width=1.5, dash="dot"),
        name=f"Herança ({int(perc_heranca*100)}%)",
        hovertemplate="Idade: %{x}<br>Herança: R$ %{y:,.0f}<extra></extra>"
    ))

    # Linha de despesa desejada na aposentadoria
    fig1.add_hline(
        y=despesa_anual, line_dash="dash",
        line_color="#FF9800", line_width=1,
        annotation_text=f"Despesa anual desejada: {formatar_moeda(despesa_anual)}",
        annotation_position="top right"
    )

    # Linha vertical na aposentadoria
    fig1.add_vline(
        x=idade_apos, line_dash="dash",
        line_color="#f44336", line_width=1.5,
        annotation_text=f"Aposentadoria ({idade_apos} anos)",
        annotation_position="top left"
    )

    fig1.update_layout(
        height=420,
        xaxis_title="Idade",
        yaxis_title="Patrimônio (R$)",
        yaxis_tickformat=",.0f",
        yaxis_tickprefix="R$ ",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        margin=dict(t=40, b=40, l=60, r=40)
    )
    fig1.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig1.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico de rendimentos vs despesa
    st.markdown('<div class="secao-titulo">Rendimento Anual vs Despesa Desejada</div>',
                unsafe_allow_html=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_base["Idade"], y=df_base["Rendimento Real"],
        name="Rendimento Real Anual",
        marker_color=[
            "#2E75B6" if f == "Acumulação" else "#4CAF50"
            for f in df_base["Fase"]
        ],
        hovertemplate="Idade: %{x}<br>Rendimento: R$ %{y:,.0f}<extra></extra>"
    ))
    fig2.add_hline(
        y=despesa_anual, line_dash="dash",
        line_color="#f44336", line_width=2,
        annotation_text=f"Meta de despesa: {formatar_moeda(despesa_anual)}/ano",
        annotation_position="top right"
    )
    fig2.update_layout(
        height=320,
        xaxis_title="Idade",
        yaxis_title="Rendimento Anual (R$)",
        yaxis_tickformat=",.0f",
        yaxis_tickprefix="R$ ",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=40, b=40, l=60, r=40)
    )
    fig2.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig2.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 2 — COMPARATIVO DE CENARIOS
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="secao-titulo">Comparativo: Pessimista × Base × Otimista</div>',
                unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    status_p = "🔴 Em risco" if pat_p85 < 0 else "🟡 Sustentável"
    status_b = "🟢 Saudável"
    status_o = "🚀 Excelente"

    with col_a:
        st.markdown(f"""
        <div class="metric-card" style="border-top:4px solid #f44336">
            <div class="label">Pessimista (rent. {rent_pess*100:.1f}%)</div>
            <div class="value" style="color:#f44336">{formatar_moeda(pat_p85)}</div>
            <div class="sub">{status_p} aos {expectativa_vida} anos</div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div class="metric-card" style="border-top:4px solid #4CAF50">
            <div class="label">Base (rent. {rent_base*100:.1f}%)</div>
            <div class="value" style="color:#4CAF50">{formatar_moeda(pat_85)}</div>
            <div class="sub">{status_b} aos {expectativa_vida} anos</div>
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown(f"""
        <div class="metric-card" style="border-top:4px solid #2196F3">
            <div class="label">Otimista (rent. {rent_otim*100:.1f}%)</div>
            <div class="value" style="color:#2196F3">{formatar_moeda(pat_o85)}</div>
            <div class="sub">{status_o} aos {expectativa_vida} anos</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_pess["Idade"], y=df_pess["Patrimônio Fim"],
        line=dict(color="#f44336", width=2, dash="dot"),
        name=f"Pessimista ({rent_pess*100:.1f}% a.a.)",
        fill="tozeroy", fillcolor="rgba(244,67,54,0.05)",
        hovertemplate="Idade: %{x}<br>R$ %{y:,.0f}<extra></extra>"
    ))
    fig3.add_trace(go.Scatter(
        x=df_base["Idade"], y=df_base["Patrimônio Fim"],
        line=dict(color="#4CAF50", width=3),
        name=f"Base ({rent_base*100:.1f}% a.a.)",
        fill="tozeroy", fillcolor="rgba(76,175,80,0.08)",
        hovertemplate="Idade: %{x}<br>R$ %{y:,.0f}<extra></extra>"
    ))
    fig3.add_trace(go.Scatter(
        x=df_otim["Idade"], y=df_otim["Patrimônio Fim"],
        line=dict(color="#2196F3", width=2, dash="dash"),
        name=f"Otimista ({rent_otim*100:.1f}% a.a.)",
        fill="tozeroy", fillcolor="rgba(33,150,243,0.05)",
        hovertemplate="Idade: %{x}<br>R$ %{y:,.0f}<extra></extra>"
    ))
    fig3.add_vline(
        x=idade_apos, line_dash="dash",
        line_color="#FF9800", line_width=1.5,
        annotation_text=f"Aposentadoria",
        annotation_position="top left"
    )
    fig3.add_hline(
        y=0, line_color="#f44336",
        line_width=1, line_dash="solid"
    )
    fig3.update_layout(
        height=440,
        xaxis_title="Idade",
        yaxis_title="Patrimônio (R$)",
        yaxis_tickformat=",.0f",
        yaxis_tickprefix="R$ ",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        margin=dict(t=40, b=40, l=60, r=40)
    )
    fig3.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig3.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

    st.plotly_chart(fig3, use_container_width=True)

    # Tabela de marcos
    st.markdown('<div class="secao-titulo">Patrimônio em Marcos Importantes</div>',
                unsafe_allow_html=True)

    marcos_idades = [idade_apos, idade_apos + 5, idade_apos + 10,
                     idade_apos + 15, expectativa_vida]
    marcos_idades = [i for i in marcos_idades if i <= expectativa_vida]

    rows_marcos = []
    for idade_m in marcos_idades:
        idx = idade_m - idade_atual
        if idx < len(df_base):
            rows_marcos.append({
                "Idade":      idade_m,
                "Pessimista": formatar_moeda_completa(df_pess.iloc[idx]["Patrimônio Fim"]),
                "Base":       formatar_moeda_completa(df_base.iloc[idx]["Patrimônio Fim"]),
                "Otimista":   formatar_moeda_completa(df_otim.iloc[idx]["Patrimônio Fim"]),
            })

    df_marcos = pd.DataFrame(rows_marcos)
    st.dataframe(df_marcos, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
# TAB 3 — CARTEIRA
# ══════════════════════════════════════════════
with tab3:
    col_esq, col_dir = st.columns([1, 1])

    with col_esq:
        st.markdown('<div class="secao-titulo">Composição da Carteira</div>',
                    unsafe_allow_html=True)

        df_cart = pd.DataFrame(carteira)
        df_cart["Patrimônio Alocado"] = df_cart["perc"] * patrimonio_atual
        df_cart["Contribuição Ponderada"] = df_cart["perc"] * df_cart["rent"]
        df_cart.columns = [
            "Classe de Ativo", "Alocação %",
            "Rent. Real Anual", "Patrimônio Alocado (R$)",
            "Contribuição Ponderada"
        ]

        df_cart_exib = df_cart.copy()
        df_cart_exib["Alocação %"] = df_cart_exib["Alocação %"].map(
            lambda x: f"{x*100:.1f}%"
        )
        df_cart_exib["Rent. Real Anual"] = df_cart_exib["Rent. Real Anual"].map(
            lambda x: f"{x*100:.1f}%"
        )
        df_cart_exib["Patrimônio Alocado (R$)"] = df_cart_exib["Patrimônio Alocado (R$)"].map(
            formatar_moeda_completa
        )
        df_cart_exib["Contribuição Ponderada"] = df_cart_exib["Contribuição Ponderada"].map(
            lambda x: f"{x*100:.2f}%"
        )

        st.dataframe(df_cart_exib, use_container_width=True, hide_index=True)

        st.markdown(f"""
        <div class="alerta-verde">
            <strong>⭐ Rentabilidade Real Ponderada da Carteira: {rent_base*100:.2f}% ao ano</strong>
        </div>
        """, unsafe_allow_html=True)

    with col_dir:
        st.markdown('<div class="secao-titulo">Distribuição por Classe</div>',
                    unsafe_allow_html=True)

        fig_pizza = go.Figure(go.Pie(
            labels=[c["nome"] for c in carteira],
            values=[c["perc"] for c in carteira],
            hole=0.45,
            textinfo="label+percent",
            textfont_size=11,
            marker=dict(colors=[
                "#1F3864", "#2E75B6", "#4472C4",
                "#70AD47", "#ED7D31", "#FFC000", "#9E48C0"
            ])
        ))
        fig_pizza.update_layout(
            height=380,
            showlegend=False,
            margin=dict(t=20, b=20, l=0, r=0),
            paper_bgcolor="white"
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    # Gráfico de rentabilidade por classe
    st.markdown('<div class="secao-titulo">Rentabilidade Real por Classe de Ativo</div>',
                unsafe_allow_html=True)

    nomes  = [c["nome"] for c in carteira]
    rents  = [c["rent"] * 100 for c in carteira]
    cores  = ["#f44336" if r < rent_base * 100 else "#4CAF50" for r in rents]

    fig_bar = go.Figure(go.Bar(
        x=nomes, y=rents,
        marker_color=cores,
        text=[f"{r:.1f}%" for r in rents],
        textposition="outside",
        hovertemplate="%{x}<br>Rent. Real: %{y:.1f}% a.a.<extra></extra>"
    ))
    fig_bar.add_hline(
        y=rent_base * 100, line_dash="dash",
        line_color="#1F3864", line_width=2,
        annotation_text=f"Média ponderada: {rent_base*100:.2f}%",
        annotation_position="top right"
    )
    fig_bar.update_layout(
        height=320,
        xaxis_title="",
        yaxis_title="Rentabilidade Real (% a.a.)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=40, b=80, l=40, r=40),
        yaxis_ticksuffix="%"
    )
    fig_bar.update_xaxes(tickangle=-25, showgrid=False)
    fig_bar.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

    st.plotly_chart(fig_bar, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 4 — PROJECAO DETALHADA
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="secao-titulo">Projeção Detalhada — Cenário Base</div>',
                unsafe_allow_html=True)

    df_exib = df_base.copy()
    for col in ["Patrimônio Início", "Rendimento Real",
                "Aporte/Retirada", "Patrimônio Fim", "Herança Estimada"]:
        df_exib[col] = df_exib[col].map(formatar_moeda_completa)

    def highlight_fase(row):
        if row["Fase"] == "Acumulação":
            return ["background-color: #e3f2fd"] * len(row)
        else:
            return ["background-color: #e8f5e9"] * len(row)

    st.dataframe(
        df_exib.style.apply(highlight_fase, axis=1),
        use_container_width=True,
        hide_index=True,
        height=500
    )

    col_dl1, col_dl2 = st.columns([1, 4])
    with col_dl1:
        csv = df_base.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Exportar CSV",
            data=csv,
            file_name="projecao_patrimonial.csv",
            mime="text/csv"
        )


# ──────────────────────────────────────────────
# RODAPE
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#999; font-size:12px;'>"
    "💡 Todos os valores são reais (acima da inflação). "
    "Esta ferramenta é apenas para fins de planejamento e simulação. "
    "Consulte um assessor financeiro certificado."
    "</p>",
    unsafe_allow_html=True
)
