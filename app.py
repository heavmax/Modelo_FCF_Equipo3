import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero FCF",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Modelo Financiero Interactivo - FCF & Descuentos")
st.markdown("Simulación de Escenarios Financieros y Evaluación de Políticas de Pronto Pago.")

# --- BARRA LATERAL (PARÁMETROS) ---
st.sidebar.header("⚙️ Parámetros de Entrada")

# Escenarios predefinidos
escenario = st.sidebar.selectbox(
    "Seleccionar Escenario Base:",
    ["Personalizado", "Conservador", "Base", "Optimista"]
)

# Valores por defecto según escenario
if escenario == "Conservador":
    crec_sales_def, margin_def = 0.15, 0.25
elif escenario == "Optimista":
    crec_sales_def, margin_def = 0.35, 0.35
else:  # Base / Personalizado
    crec_sales_def, margin_def = 0.25, 0.30

# Controles interactivos
st.sidebar.subheader("📈 Operaciones & Ventas")
crec_sales = st.sidebar.slider("Crecimiento de Ventas Anual (%)", 0.0, 0.50, crec_sales_def, 0.01)
oper_margin = st.sidebar.slider("Margen Operativo EBIT (%)", 0.10, 0.50, margin_def, 0.01)
tax_rate = st.sidebar.number_input("Tasa de Impuestos (%)", value=0.30, step=0.01)

st.sidebar.subheader("💰 Política de Pronto Pago")
descuento_pp = st.sidebar.slider("Descuento por Pronto Pago (%)", 0.0, 10.0, 2.0, 0.5) / 100
porcentaje_clientes_pp = st.sidebar.slider("% Clientes que aplican Pronto Pago", 0.0, 100.0, 30.0, 5.0) / 100

st.sidebar.subheader("🔄 Capital de Trabajo & CapEx")
days_nwc = st.sidebar.slider("Días de Capital de Trabajo (NWC)", 10, 90, 45, 5)
capex_sales_ratio = st.sidebar.slider("CapEx / Ventas (%)", 0.01, 0.15, 0.05, 0.01)
wacc = st.sidebar.slider("Costo de Capital (WACC) (%)", 0.05, 0.20, 0.10, 0.005)

# --- CÁLCULOS DEL MODELO ---
ventas_base = 1000000  # Ventas año 0
anios = [f"Año {i}" for i in range(1, 6)]

ventas_brutas = [ventas_base * ((1 + crec_sales) ** i) for i in range(1, 6)]

# Cálculo de Costo por Pronto Pago
costo_pronto_pago = [v * descuento_pp * porcentaje_clientes_pp for v in ventas_brutas]
ventas_netas = [v - c for v, c in zip(ventas_brutas, costo_pronto_pago)]

ebit = [v * oper_margin for v in ventas_netas]
impuestos = [e * tax_rate for e in ebit]
nopat = [e - t for e, t in zip(ebit, impuestos)]

# Depreciación proyectada
depreciacion = [v * 0.03 for v in ventas_netas]

# NWC (Capital de Trabajo Neto ajustado por días)
nwc = [(v / 365) * days_nwc for v in ventas_netas]
delta_nwc = [nwc[0] - (ventas_base / 365 * days_nwc)] + [nwc[i] - nwc[i-1] for i in range(1, 5)]

# CapEx
capex = [v * capex_sales_ratio for v in ventas_netas]

# Free Cash Flow (FCF)
fcf = [n + d - dn - c for n, d, dn, c in zip(nopat, depreciacion, delta_nwc, capex)]

# Valor Presente del FCF
fcf_vp = [f / ((1 + wacc) ** (i + 1)) for i, f in enumerate(fcf)]
valor_presente_total = sum(fcf_vp)

# --- DASHBOARD / PRESENTACIÓN ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Valor Presente FCF (5 años)", f"${valor_presente_total:,.2f}")
col2.metric("Ventas Netas Año 5", f"${ventas_netas[-1]:,.2f}")
col3.metric("Costo Total Dcto. Pronto Pago", f"${sum(costo_pronto_pago):,.2f}")
col4.metric("FCF Promedio Anual", f"${np.mean(fcf):,.2f}")

st.markdown("---")

# Gráficos
tab1, tab2 = st.tabs(["📈 Proyección de FCF", "📊 Impacto de Pronto Pago"])

with tab1:
    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(x=anios, y=fcf, name="Flujo de Caja Libre (FCF)", marker_color="#2ecc71"))
    fig_fcf.add_trace(go.Scatter(x=anios, y=ventas_netas, name="Ventas Netas", yaxis="y2", line=dict(color="#3498db", width=3)))
    
    fig_fcf.update_layout(
        title="Proyección de FCF vs Ventas Netas",
        yaxis=dict(title="FCF ($)"),
        yaxis2=dict(title="Ventas Netas ($)", overlaying="y", side="right"),
        legend=dict(x=0, y=1.1, orientation="h")
    )
    st.plotly_chart(fig_fcf, use_container_width=True)

with tab2:
    df_pp = pd.DataFrame({
        "Año": anios,
        "Ventas Brutas": ventas_brutas,
        "Costo Descuento PP": costo_pronto_pago,
        "Ventas Netas": ventas_netas
    })
    
    fig_pp = px.bar(
        df_pp, 
        x="Año", 
        y=["Ventas Netas", "Costo Descuento PP"], 
        title="Impacto del Descuento por Pronto Pago en las Ventas",
        labels={"value": "Monto ($)", "variable": "Concepto"},
        color_discrete_map={"Ventas Netas": "#1f77b4", "Costo Descuento PP": "#e74c3c"}
    )
    st.plotly_chart(fig_pp, use_container_width=True)

# Tabla de detalle
with st.expander("📄 Ver Tabla de Proyecciones Detallada"):
    df_detalle = pd.DataFrame({
        "Concepto": ["Ventas Brutas", "(-) Costo Pronto Pago", "Ventas Netas", "EBIT", "NOPAT", "Depreciación", "(+/-) Δ NWC", "(-) CapEx", "Free Cash Flow (FCF)"],
        "Año 1": [ventas_brutas[0], costo_pronto_pago[0], ventas_netas[0], ebit[0], nopat[0], depreciacion[0], delta_nwc[0], capex[0], fcf[0]],
        "Año 2": [ventas_brutas[1], costo_pronto_pago[1], ventas_netas[1], ebit[1], nopat[1], depreciacion[1], delta_nwc[1], capex[1], fcf[1]],
        "Año 3": [ventas_brutas[2], costo_pronto_pago[2], ventas_netas[2], ebit[2], nopat[2], depreciacion[2], delta_nwc[2], capex[2], fcf[2]],
        "Año 4": [ventas_brutas[3], costo_pronto_pago[3], ventas_netas[3], ebit[3], nopat[3], depreciacion[3], delta_nwc[3], capex[3], fcf[3]],
        "Año 5": [ventas_brutas[4], costo_pronto_pago[4], ventas_netas[4], ebit[4], nopat[4], depreciacion[4], delta_nwc[4], capex[4], fcf[4]],
    })
    st.dataframe(df_detalle.style.format({col: "${:,.2f}" for col in df_detalle.columns if col != "Concepto"}))
