"""
============================================================
DASHBOARD BI - MINIMARKET
============================================================
Autor: Ricardo Muñoz
Empresa: G&S Gestión y Sistemas
Descripción: Dashboard interactivo de ventas del minimarket
             con KPIs, análisis por sucursal, producto, tiempo
             y método de pago.
============================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard BI - Minimarket | G&S",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILOS PERSONALIZADOS
# ============================================================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f4e79;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #1f4e79;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f4e79;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f4e79;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# CARGA DE DATOS (con caché para velocidad)
# ============================================================
@st.cache_data
def cargar_datos():
    """Carga los datos procesados desde Parquet."""
    BASE_DIR = Path(__file__).resolve().parent
    ruta = BASE_DIR / "data_processed" / "ventas_consolidado.parquet"
    df = pd.read_parquet(ruta)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


df = cargar_datos()


# ============================================================
# SIDEBAR - FILTROS INTERACTIVOS
# ============================================================
st.sidebar.title("🎛️ Filtros")
st.sidebar.markdown("---")

# Filtro: Rango de fechas
fecha_min = df["Fecha"].min().date()
fecha_max = df["Fecha"].max().date()

rango_fechas = st.sidebar.date_input(
    "📅 Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

# Filtro: Sucursales (multi-selección)
sucursales = sorted(df["NombreSucursal"].unique())
sucursales_sel = st.sidebar.multiselect(
    "🏪 Sucursales",
    options=sucursales,
    default=sucursales
)

# Filtro: Categorías
categorias = sorted(df["Categoría"].unique())
categorias_sel = st.sidebar.multiselect(
    "📦 Categorías de producto",
    options=categorias,
    default=categorias
)

# Filtro: Turnos
turnos = sorted(df["Turno"].unique())
turnos_sel = st.sidebar.multiselect(
    "🕐 Turnos",
    options=turnos,
    default=turnos
)

# Filtro: Método de pago
metodos = sorted(df["MetodoPago"].unique())
metodos_sel = st.sidebar.multiselect(
    "💳 Método de pago",
    options=metodos,
    default=metodos
)

st.sidebar.markdown("---")
st.sidebar.info("💡 Los filtros afectan a todo el dashboard en tiempo real.")


# ============================================================
# APLICAR FILTROS
# ============================================================
if len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas
    df_filtrado = df[
        (df["Fecha"].dt.date >= fecha_inicio) &
        (df["Fecha"].dt.date <= fecha_fin) &
        (df["NombreSucursal"].isin(sucursales_sel)) &
        (df["Categoría"].isin(categorias_sel)) &
        (df["Turno"].isin(turnos_sel)) &
        (df["MetodoPago"].isin(metodos_sel))
    ]
else:
    df_filtrado = df.copy()

# Validación: si no hay datos con los filtros
if df_filtrado.empty:
    st.warning("⚠️ No hay datos con los filtros seleccionados. Ajusta tus filtros.")
    st.stop()


# ============================================================
# HEADER PRINCIPAL
# ============================================================
st.markdown('<div class="main-header">🛒 Dashboard BI - Minimarket</div>', unsafe_allow_html=True)
st.markdown(f"📅 **Período analizado:** {fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')} &nbsp;|&nbsp; 🏪 **Sucursales:** {len(sucursales_sel)} de {len(sucursales)}")
st.markdown("")


# ============================================================
# KPIs PRINCIPALES
# ============================================================
st.subheader("📊 Indicadores Clave (KPIs)")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    ventas_totales = df_filtrado["TotalVenta"].sum()
    st.metric("💰 Ventas Totales", f"${ventas_totales:,.2f}")

with col2:
    ganancia_total = df_filtrado["Ganancia"].sum()
    st.metric("📈 Ganancia Total", f"${ganancia_total:,.2f}")

with col3:
    margen_promedio = (ganancia_total / ventas_totales * 100) if ventas_totales > 0 else 0
    st.metric("💎 Margen (%)", f"{margen_promedio:.1f}%")

with col4:
    n_transacciones = df_filtrado["VentaID"].nunique()
    st.metric("🧾 Transacciones", f"{n_transacciones:,}")

with col5:
    ticket_promedio = ventas_totales / n_transacciones if n_transacciones > 0 else 0
    st.metric("🎫 Ticket Promedio", f"${ticket_promedio:.2f}")

st.markdown("---")


# ============================================================
# FILA 1: EVOLUCIÓN TEMPORAL
# ============================================================
st.subheader("📈 Evolución Temporal de Ventas")

col1, col2 = st.columns([2, 1])

with col1:
    ventas_mensuales = (
        df_filtrado.groupby("AñoMes")
        .agg(TotalVenta=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum"))
        .reset_index()
        .sort_values("AñoMes")
    )
    fig_evolucion = go.Figure()
    fig_evolucion.add_trace(go.Scatter(
        x=ventas_mensuales["AñoMes"], y=ventas_mensuales["TotalVenta"],
        name="Ventas", mode="lines+markers",
        line=dict(color="#1f4e79", width=3), fill="tozeroy", fillcolor="rgba(31,78,121,0.1)"
    ))
    fig_evolucion.add_trace(go.Scatter(
        x=ventas_mensuales["AñoMes"], y=ventas_mensuales["Ganancia"],
        name="Ganancia", mode="lines+markers",
        line=dict(color="#28a745", width=3, dash="dot")
    ))
    fig_evolucion.update_layout(
        title="Ventas y Ganancia por Mes",
        xaxis_title="Mes", yaxis_title="Monto ($)",
        hovermode="x unified", height=400, showlegend=True
    )
    st.plotly_chart(fig_evolucion, use_container_width=True)

with col2:
    ventas_anuales = df_filtrado.groupby("Año")["TotalVenta"].sum().reset_index()
    fig_anual = px.bar(
        ventas_anuales, x="Año", y="TotalVenta",
        title="Ventas por Año", text_auto=".2s",
        color="TotalVenta", color_continuous_scale="Blues"
    )
    fig_anual.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
    fig_anual.update_traces(textposition="outside")
    st.plotly_chart(fig_anual, use_container_width=True)


# ============================================================
# FILA 2: ANÁLISIS POR SUCURSAL Y CATEGORÍA
# ============================================================
st.subheader("🏪 Análisis por Sucursal y Categoría")

col1, col2 = st.columns(2)

with col1:
    ventas_sucursal = (
        df_filtrado.groupby("NombreSucursal")
        .agg(TotalVenta=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum"))
        .reset_index()
        .sort_values("TotalVenta", ascending=True)
    )
    fig_suc = go.Figure()
    fig_suc.add_trace(go.Bar(
        y=ventas_sucursal["NombreSucursal"], x=ventas_sucursal["TotalVenta"],
        name="Ventas", orientation="h", marker_color="#1f4e79",
        text=ventas_sucursal["TotalVenta"].apply(lambda x: f"${x:,.0f}"),
        textposition="outside"
    ))
    fig_suc.update_layout(
        title="Ventas por Sucursal", xaxis_title="Ventas ($)",
        height=400, showlegend=False
    )
    st.plotly_chart(fig_suc, use_container_width=True)

with col2:
    ventas_cat = (
        df_filtrado.groupby("Categoría")["TotalVenta"].sum()
        .reset_index()
        .sort_values("TotalVenta", ascending=False)
    )
    fig_cat = px.pie(
        ventas_cat, values="TotalVenta", names="Categoría",
        title="Distribución de Ventas por Categoría",
        hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig_cat.update_traces(textposition="inside", textinfo="percent+label")
    fig_cat.update_layout(height=400)
    st.plotly_chart(fig_cat, use_container_width=True)


# ============================================================
# FILA 3: TOP PRODUCTOS
# ============================================================
st.subheader("🏆 Top Productos")

col1, col2 = st.columns(2)

with col1:
    top_ventas = (
        df_filtrado.groupby("NombreProducto")["TotalVenta"].sum()
        .reset_index()
        .sort_values("TotalVenta", ascending=False)
        .head(10)
    )
    fig_top_v = px.bar(
        top_ventas.sort_values("TotalVenta"), x="TotalVenta", y="NombreProducto",
        orientation="h", title="Top 10 Productos por Ventas",
        text_auto=".2s", color="TotalVenta", color_continuous_scale="Blues"
    )
    fig_top_v.update_layout(height=450, showlegend=False, coloraxis_showscale=False,
                             yaxis_title="", xaxis_title="Ventas ($)")
    st.plotly_chart(fig_top_v, use_container_width=True)

with col2:
    top_ganancia = (
        df_filtrado.groupby("NombreProducto")["Ganancia"].sum()
        .reset_index()
        .sort_values("Ganancia", ascending=False)
        .head(10)
    )
    fig_top_g = px.bar(
        top_ganancia.sort_values("Ganancia"), x="Ganancia", y="NombreProducto",
        orientation="h", title="Top 10 Productos por Ganancia",
        text_auto=".2s", color="Ganancia", color_continuous_scale="Greens"
    )
    fig_top_g.update_layout(height=450, showlegend=False, coloraxis_showscale=False,
                             yaxis_title="", xaxis_title="Ganancia ($)")
    st.plotly_chart(fig_top_g, use_container_width=True)


# ============================================================
# FILA 4: ANÁLISIS DE TURNOS, DÍAS Y MÉTODOS DE PAGO
# ============================================================
st.subheader("🕐 Patrones de Consumo")

col1, col2, col3 = st.columns(3)

with col1:
    ventas_turno = df_filtrado.groupby("Turno")["TotalVenta"].sum().reset_index()
    fig_turno = px.bar(
        ventas_turno, x="Turno", y="TotalVenta",
        title="Ventas por Turno", text_auto=".2s",
        color="Turno", color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_turno.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_turno, use_container_width=True)

with col2:
    orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    ventas_dia = df_filtrado.groupby("DiaSemana")["TotalVenta"].sum().reset_index()
    ventas_dia["DiaSemana"] = pd.Categorical(ventas_dia["DiaSemana"], categories=orden_dias, ordered=True)
    ventas_dia = ventas_dia.sort_values("DiaSemana")
    fig_dia = px.bar(
        ventas_dia, x="DiaSemana", y="TotalVenta",
        title="Ventas por Día de la Semana", text_auto=".2s",
        color="TotalVenta", color_continuous_scale="Blues"
    )
    fig_dia.update_layout(height=350, showlegend=False, coloraxis_showscale=False,
                          xaxis_title="")
    st.plotly_chart(fig_dia, use_container_width=True)

with col3:
    ventas_pago = df_filtrado.groupby("MetodoPago")["TotalVenta"].sum().reset_index()
    fig_pago = px.pie(
        ventas_pago, values="TotalVenta", names="MetodoPago",
        title="Método de Pago Preferido", hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pago.update_traces(textposition="inside", textinfo="percent+label")
    fig_pago.update_layout(height=350)
    st.plotly_chart(fig_pago, use_container_width=True)


# ============================================================
# TABLA DETALLADA + DESCARGA
# ============================================================
st.subheader("📋 Detalle de Transacciones")

with st.expander("🔍 Ver tabla detallada y descargar datos"):
    columnas_mostrar = [
        "Fecha", "NombreSucursal", "Turno", "NombreProducto", "Categoría",
        "Cantidad", "TotalVenta", "Ganancia", "MargenPct", "MetodoPago"
    ]
    st.dataframe(df_filtrado[columnas_mostrar].head(1000), use_container_width=True, height=400)
    st.caption(f"Mostrando primeras 1,000 filas de {len(df_filtrado):,} transacciones filtradas.")

    # Botón de descarga
    csv = df_filtrado[columnas_mostrar].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=csv,
        file_name=f"ventas_filtradas_{fecha_inicio}_{fecha_fin}.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("📊 Dashboard BI • Ricardo Muñoz • G&S Gestión y Sistemas S.A.C. • 2026")