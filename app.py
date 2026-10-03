import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Financiero Interactivo - FCF & Valuación",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Dashboard Financiero Interactivo (Modelo FCF)")
st.markdown("Ajusta los parámetros financieros en la barra lateral o en las pestañas para evaluar el comportamiento de todas las variables en tiempo real.")

# -----------------------------------------------------------------------------
# SIDEBAR: PANEL DE CONTROL DE PARÁMETROS GENERALES Y ESCENARIOS
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Configuración & Escenarios")

escenario_opcion = st.sidebar.selectbox(
    "Seleccionar Escenario Base:",
    ["Equipo 3 (Personalizado)", "Conservador (25% Crec.)", "Optimista (40% Crec.)"]
)

# Valores por defecto según escenario
if escenario_opcion == "Optimista (40% Crec.)":
    g_sales_default = 0.40
    red_costo_default = 0.02
    dso_2027_def, dso_2028_def = 75, 90
    tasa_int_def = 0.08
    isr_def = 0.28
elif escenario_opcion == "Conservador (25% Crec.)":
    g_sales_default = 0.25
    red_costo_default = 0.00
    dso_2027_def, dso_2028_def = 75, 90
    tasa_int_def = 0.08
    isr_def = 0.28
else: # Equipo 3 / Personalizado
    g_sales_default = 0.25
    red_costo_default = 0.00
    dso_2027_def, dso_2028_def = 60, 60
    tasa_int_def = 0.10
    isr_def = 0.28

st.sidebar.subheader("📈 Parámetros Clave Proyección (2027-2030)")

crec_ventas = st.sidebar.slider("Crecimiento Ventas Brutas (%)", 0.0, 0.60, float(g_sales_default), step=0.01)
costo_ventas_pct = st.sidebar.slider("Costo de Ventas (% Ventas Brutas)", 0.30, 0.70, 0.50, step=0.01)
red_costo_anual = st.sidebar.slider("Reducción Anual Relativa % Costo Ventas", 0.0, 0.05, float(red_costo_default), step=0.005)

dso_2027 = st.sidebar.number_input("Días de Cartera / Clientes (DSO 2027)", 10, 120, dso_2027_def)
dso_2028 = st.sidebar.number_input("Días de Cartera / Clientes (DSO 2028-2030)", 10, 120, dso_2028_def)

tasa_isr = st.sidebar.slider("Tasa ISR (%)", 0.15, 0.35, float(isr_def), step=0.01)
tasa_deuda_lp = st.sidebar.slider("Tasa Interés Deuda LP (%)", 0.04, 0.18, float(tasa_int_def), step=0.005)

ke_costo_capital = st.sidebar.slider("Costo Capital Propio (Ke) (%)", 0.08, 0.25, 0.15, step=0.005)
g_terminal = st.sidebar.slider("Crecimiento Terminal (g) (%)", 0.01, 0.08, 0.04, step=0.005)

# -----------------------------------------------------------------------------
# MOTOR DE CÁLCULO FINANCIERO (2024A - 2030E)
# -----------------------------------------------------------------------------
years = ['2024A', '2025A', '2026A', '2027E', '2028E', '2029E', '2030E']
proj_years = ['2027E', '2028E', '2029E', '2030E']

# Ventas
v_brutas = [240.0, 264.0, 295.68]
for i in range(4):
    v_brutas.append(v_brutas[-1] * (1 + crec_ventas))

# Costo de ventas %
c_v_pct = [0.5, 0.5, 0.5]
curr_c_pct = costo_ventas_pct
for i in range(4):
    c_v_pct.append(curr_c_pct)
    curr_c_pct = curr_c_pct * (1 - red_costo_anual)

costo_ventas = [-v_brutas[i] * c_v_pct[i] for i in range(len(years))]
v_netas = v_brutas.copy()
utilidad_bruta = [v_netas[i] + costo_ventas[i] for i in range(len(years))]

# Gastos op
g_op_efectivo = [-20.0, -20.0, -20.0]
for i in range(4):
    g_op_efectivo.append(g_op_efectivo[-1] * 1.10) # +10% anual

depreciacion = [-20.0] * len(years)
ebit = [utilidad_bruta[i] + g_op_efectivo[i] + depreciacion[i] for i in range(len(years))]

# Gastos Financieros
interes_deuda = [-16.0, -16.0, -16.0]
for i in range(4):
    interes_deuda.append(-200.0 * tasa_deuda_lp)

ebt = [ebit[i] + interes_deuda[i] for i in range(len(years))]

isrs = []
for i, yr in enumerate(years):
    t_isr = 0.25 if yr in ['2024A', '2025A'] else tasa_isr
    isrs.append(-ebt[i] * t_isr)

utilidad_neta = [ebt[i] + isrs[i] for i in range(len(years))]

# Balance General & Capital de Trabajo
clientes = [20.0, 22.0, 49.28]
dsos = [30, 30, 60, dso_2027, dso_2028, dso_2028, dso_2028]
for i in range(3, len(years)):
    clientes.append((v_netas[i] * dsos[i]) / 360.0)

inventarios = [20.0, 22.0, 24.64]
for i in range(3, len(years)):
    inventarios.append((-costo_ventas[i] * 60.0) / 360.0)

maquinaria_costo = [400.0] * len(years)
dep_acum = [-20.0 * (i+1) for i in range(len(years))]
maquinaria_neta = [maquinaria_costo[i] + dep_acum[i] for i in range(len(years))]

proveedores = [100.0] * len(years)
deuda_lp = [200.0] * len(years)

# Capital Contable acumulado
capital_contable = [248.0, 305.0, 371.1248]
for i in range(3, len(years)):
    # Asumiendo dividendos del 40% a partir de 2028
    div = 0.40 if years[i] in ['2028E', '2029E', '2030E'] else 0.0
    retenido = utilidad_neta[i] * (1 - div)
    capital_contable.append(capital_contable[-1] + retenido)

# Efectivo como cuadre de Balance
efectivo = []
for i in range(len(years)):
    pasivo_patrimonio = proveedores[i] + deuda_lp[i] + capital_contable[i]
    activos_no_efectivo = clientes[i] + inventarios[i] + maquinaria_neta[i]
    efectivo.append(pasivo_patrimonio - activos_no_efectivo)

# FCFF (Free Cash Flow to Firm)
nopat = [ebit[i] * (1 - (0.25 if years[i] in ['2024A', '2025A'] else tasa_isr)) for i in range(len(years))]
delta_nwc = [0.0]
for i in range(1, len(years)):
    nwc_prev = clientes[i-1] + inventarios[i-1] - proveedores[i-1]
    nwc_curr = clientes[i] + inventarios[i] - proveedores[i]
    delta_nwc.append(nwc_curr - nwc_prev)

fcff = [nopat[i] + 20.0 - delta_nwc[i] for i in range(len(years))]

# Valuación DCF
wacc_list = []
for i in range(3, len(years)):
    d = deuda_lp[i]
    e = capital_contable[i]
    wd = d / (d + e)
    we = e / (d + e)
    kd_after_tax = tasa_deuda_lp * (1 - tasa_isr)
    wacc = wd * kd_after_tax + we * ke_costo_capital
    wacc_list.append(wacc)

wacc_promedio = np.mean(wacc_list)

# Valor Terminal y VP de Flujos
factor_desc = [(1 + wacc_promedio)**(i+1) for i in range(4)]
vp_fcff = [fcff[3+i] / factor_desc[i] for i in range(4)]
sum_vp_fcff = sum(vp_fcff)

fcff_2030 = fcff[-1]
valor_terminal = (fcff_2030 * (1 + g_terminal)) / (wacc_promedio - g_terminal)
vp_valor_terminal = valor_terminal / ((1 + wacc_promedio)**4)

enterprise_value = sum_vp_fcff + vp_valor_terminal
equity_value = enterprise_value - deuda_lp[2] + efectivo[2] # Ajustado con caja y deuda de 2026

# -----------------------------------------------------------------------------
# INTERFAZ POR PESTAÑAS (REPLICANDO HOJAS DE EXCEL)
# -----------------------------------------------------------------------------
tab_sup, tab_esc, tab_er, tab_bg, tab_fe, tab_fcf, tab_ratios, tab_dcf, tab_notas = st.tabs([
    "📋 Supuestos", 
    "🎯 Escenarios", 
    "📈 Estado de Resultados", 
    "🏛️ Balance General", 
    "💵 Flujo de Efectivo", 
    "⚡ FCF (Flujo Libre)", 
    "📊 Ratios", 
    "🏷️ Valuación DCF", 
    "📝 Notas del Caso"
])

# --- PESTAÑA 1: SUPUESTOS ---
with tab_sup:
    st.header("Supuestos del Modelo (2024A - 2030E)")
    
    df_sup = pd.DataFrame({
        "Concepto": [
            "Crecimiento Ventas Brutas", 
            "Costo de Ventas (% Ventas)", 
            "Días de Cartera (DSO)", 
            "Días de Inventario (DIO)", 
            "Tasa ISR", 
            "Tasa Interés Deuda LP"
        ],
        "2024A": ["-", "50.0%", "30 días", "60 días", "25.0%", "8.0%"],
        "2025A": ["10.0%", "50.0%", "30 días", "60 días", "25.0%", "8.0%"],
        "2026A": ["12.0%", "50.0%", "60 días", "60 días", "28.0%", "8.0%"],
        "2027E": [f"{crec_ventas*100:.1f}%", f"{c_v_pct[3]*100:.1f}%", f"{dsos[3]} días", "60 días", f"{tasa_isr*100:.1f}%", f"{tasa_deuda_lp*100:.1f}%"],
        "2028E": [f"{crec_ventas*100:.1f}%", f"{c_v_pct[4]*100:.1f}%", f"{dsos[4]} días", "60 días", f"{tasa_isr*100:.1f}%", f"{tasa_deuda_lp*100:.1f}%"],
        "2029E": [f"{crec_ventas*100:.1f}%", f"{c_v_pct[5]*100:.1f}%", f"{dsos[5]} días", "60 días", f"{tasa_isr*100:.1f}%", f"{tasa_deuda_lp*100:.1f}%"],
        "2030E": [f"{crec_ventas*100:.1f}%", f"{c_v_pct[6]*100:.1f}%", f"{dsos[6]} días", "60 días", f"{tasa_isr*100:.1f}%", f"{tasa_deuda_lp*100:.1f}%"],
    })
    st.table(df_sup)

# --- PESTAÑA 2: ESCENARIOS ---
with tab_esc:
    st.header("Matriz de Escenarios de Crecimiento y Gestión")
    st.info("El escenario activo actual aplica los valores modificados desde la barra lateral.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Crecimiento Anual Ventas", f"{crec_ventas*100:.1f}%")
    col2.metric("Reducción % Costo Ventas", f"{red_costo_anual*100:.1f}%")
    col3.metric("DSO Objetivo 2028-2030", f"{dso_2028} días")

# --- PESTAÑA 3: ESTADO DE RESULTADOS ---
with tab_er:
    st.header("Estado de Resultados (NIF B-3)")
    
    df_er = pd.DataFrame([
        v_brutas,
        costo_ventas,
        utilidad_bruta,
        g_op_efectivo,
        depreciacion,
        ebit,
        interes_deuda,
        ebt,
        isrs,
        utilidad_neta
    ], index=[
        "Ventas Brutas", "Costo de Ventas", "Utilidad Bruta", 
        "Gastos Op. (sin dep.)", "Depreciación", "EBIT (Utilidad Op.)", 
        "Gastos Financieros", "Utilidad Antes ISR (EBT)", "ISR", "Utilidad Neta"
    ], columns=years)
    
    st.dataframe(df_er.style.format("{:,.2f}"))
    
    fig_er = go.Figure()
    fig_er.add_trace(go.Bar(x=years, y=v_brutas, name="Ventas Brutas", marker_color="#1f77b4"))
    fig_er.add_trace(go.Bar(x=years, y=ebit, name="EBIT", marker_color="#ff7f0e"))
    fig_er.add_trace(go.Bar(x=years, y=utilidad_neta, name="Utilidad Neta", marker_color="#2ca02c"))
    fig_er.update_layout(barmode='group', title="Evolución de Ingresos y Utilidades (u.m.)")
    st.plotly_chart(fig_er, use_container_width=True)

# --- PESTAÑA 4: BALANCE GENERAL ---
with tab_bg:
    st.header("Estado de Situación Financiera / Balance General (NIF B-6)")
    
    df_bg = pd.DataFrame([
        efectivo, clientes, inventarios,
        [efectivo[i]+clientes[i]+inventarios[i] for i in range(len(years))],
        maquinaria_costo, dep_acum, maquinaria_neta,
        [efectivo[i]+clientes[i]+inventarios[i]+maquinaria_neta[i] for i in range(len(years))],
        proveedores, deuda_lp,
        [proveedores[i]+deuda_lp[i] for i in range(len(years))],
        capital_contable,
        [proveedores[i]+deuda_lp[i]+capital_contable[i] for i in range(len(years))]
    ], index=[
        "Efectivo y Equivalentes", "Clientes", "Inventarios", "Total Activo Circulante",
        "Maquinaria (Costo)", "(−) Depreciación Acumulada", "Maquinaria Neto", "TOTAL ACTIVO",
        "Proveedores", "Deuda Largo Plazo", "TOTAL PASIVO", "CAPITAL CONTABLE", "TOTAL PASIVO + CAPITAL"
    ], columns=years)
    
    st.dataframe(df_bg.style.format("{:,.2f}"))

# --- PESTAÑA 5: FLUJO DE EFECTIVO ---
with tab_fe:
    st.header("Estado de Flujos de Efectivo (Método Indirecto - NIF B-2)")
    
    flujo_op = [utilidad_neta[i] - depreciacion[i] - delta_nwc[i] for i in range(len(years))]
    
    df_fe = pd.DataFrame([
        utilidad_neta,
        [-d for d in depreciacion],
        [-d for d in delta_nwc],
        flujo_op,
        efectivo
    ], index=[
        "Utilidad Neta", "(+) Depreciación", "(−) Incremento en Capital de Trabajo", 
        "Flujo Neto de Operación", "Efectivo Final en Cierre"
    ], columns=years)
    
    st.dataframe(df_fe.style.format("{:,.2f}"))

# --- PESTAÑA 6: FCF (FLUJO DE CAJA LIBRE) ---
with tab_fcf:
    st.header("Flujo de Caja Libre de la Empresa (FCFF)")
    
    df_fcf = pd.DataFrame([
        ebit, nopat, [-d for d in depreciacion], delta_nwc, fcff
    ], index=[
        "EBIT", "NOPAT", "(+) Depreciación", "(−) Incremento Capital Trabajo (NWC)", "FLUJO DE CAJA LIBRE (FCFF)"
    ], columns=years)
    
    st.dataframe(df_fcf.style.format("{:,.2f}"))
    
    fig_fcf = px.line(x=years, y=fcff, title="Trayectoria del FCFF Proyectado (u.m.)", markers=True)
    st.plotly_chart(fig_fcf, use_container_width=True)

# --- PESTAÑA 7: RATIOS ---
with tab_ratios:
    st.header("Ratios de Rentabilidad, Liquidez y Apalancamiento")
    
    margo_op = [ebit[i]/v_netas[i] * 100 for i in range(len(years))]
    margo_neto = [utilidad_neta[i]/v_netas[i] * 100 for i in range(len(years))]
    roe = [utilidad_neta[i]/capital_contable[i] * 100 for i in range(len(years))]
    
    df_ratios = pd.DataFrame([
        margo_op, margo_neto, roe
    ], index=["Margen Operativo (%)", "Margen Neto (%)", "ROE (%)"], columns=years)
    
    st.dataframe(df_ratios.style.format("{:.2f}%"))

# --- PESTAÑA 8: VALUACIÓN DCF ---
with tab_dcf:
    st.header("Valuación por Flujos de Caja Descontados (DCF)")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("WACC Promedio Proyectado", f"{wacc_promedio*100:.2f}%")
    c2.metric("Valor de Empresa (Enterprise Value)", f"${enterprise_value:,.2f} u.m.")
    c3.metric("Valor del Capital (Equity Value)", f"${equity_value:,.2f} u.m.")
    
    st.subheader("Desglose del Valor")
    df_dcf_summary = pd.DataFrame({
        "Concepto": ["Valor Presente FCFF 2027-2030", "Valor Terminal Proyectado", "VP Valor Terminal", "Enterprise Value (EV)", "Equity Value (Capital)"],
        "Monto (u.m.)": [sum_vp_fcff, valor_terminal, vp_valor_terminal, enterprise_value, equity_value]
    })
    st.table(df_dcf_summary.style.format({"Monto (u.m.)": "${:,.2f}"}))

# --- PESTAÑA 9: NOTAS DEL CASO ---
with tab_notas:
    st.header("Notas del Caso y Marco Contable")
    st.markdown("""
    * **Marco Contable:** NIF mexicanas (B-3, B-6, B-2, C-6, D-4).
    * **Reglas de Negocio:**
      1. El balance de apertura (2024) inicia con activos por $500 u.m.
      2. Días de Cartera y Proveedores calculados bajo la convención comercial de **360 días**.
      3. Sensibilidad activa: Cualquier cambio en la barra lateral recalcula la valuación final en tiempo real.
    """)
