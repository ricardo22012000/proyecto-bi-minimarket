"""
============================================================
DASHBOARD BI - MINIMARKET - VERSIÓN 3 (Sin Scroll)
============================================================
Autor: Ricardo Muñoz
Empresa: G&S Gestión y Sistemas
Fecha: Julio 2026
============================================================
MEJORAS RESPECTO A V2:
  ✅ Diseño compacto: todo cabe sin scroll
  ✅ Gráficos con altura optimizada (250-280px)
  ✅ KPIs compactos en una sola línea
  ✅ CSS reducido para maximizar densidad
  ✅ Layout grid 2x2 en cada página
============================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="Dashboard BI v3 - Minimarket | G&S",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS compacto para maximizar el uso del espacio
st.markdown("""
    <style>
    /* Reducir padding del contenedor principal */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    /* Header compacto */
    .main-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f4e79;
        margin: 0;
        padding: 0;
    }
    .sub-header {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    /* KPIs compactos */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1f4e79;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        font-weight: 600;
    }
    [data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 0.6rem;
        border-radius: 8px;
        border-left: 3px solid #1f4e79;
    }
    /* Reducir espaciado entre elementos */
    .element-container { margin-bottom: 0.3rem; }
    /* Títulos de sección compactos */
    .section-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1f4e79;
        margin: 0.3rem 0 0.2rem 0;
        padding-bottom: 0.2rem;
        border-bottom: 1px solid #e0e0e0;
    }
    /* Ocultar el footer default de streamlit */
    footer { visibility: hidden; }
    /* Reducir tamaño del radio de navegación */
    .stRadio > label { font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    BASE_DIR = Path(__file__).resolve().parent.parent
    ruta = BASE_DIR / "data_processed" / "ventas_consolidado.parquet"
    df = pd.read_parquet(ruta)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


df = cargar_datos()


# ============================================================
# HELPER: filtro con fallback
# ============================================================
def filtro_seguro(seleccion, todas_las_opciones):
    return seleccion if seleccion else todas_las_opciones


# ============================================================
# SIDEBAR (compacto)
# ============================================================
st.sidebar.markdown("### 🛒 Dashboard BI")
st.sidebar.caption("G&S • v3 sin scroll")

pagina = st.sidebar.radio(
    "📄 Página",
    options=["📊 General", "🏆 Productos", "🕐 Patrones"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**🎛️ Filtros**")

fecha_min = df["Fecha"].min().date()
fecha_max = df["Fecha"].max().date()

rango_fechas = st.sidebar.date_input(
    "📅 Fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min, max_value=fecha_max
)

sucursales_all = sorted(df["NombreSucursal"].unique())
sucursales_sel = st.sidebar.multiselect("🏪 Sucursales", options=sucursales_all, default=[], placeholder="Todas")

categorias_all = sorted(df["Categoría"].unique())
categorias_sel = st.sidebar.multiselect("📦 Categorías", options=categorias_all, default=[], placeholder="Todas")

turnos_all = sorted(df["Turno"].unique())
turnos_sel = st.sidebar.multiselect("🕐 Turnos", options=turnos_all, default=[], placeholder="Todos")

metodos_all = sorted(df["MetodoPago"].unique())
metodos_sel = st.sidebar.multiselect("💳 Pago", options=metodos_all, default=[], placeholder="Todos")

st.sidebar.caption("💡 Vacío = ver todo")


# ============================================================
# APLICAR FILTROS
# ============================================================
sucursales_f = filtro_seguro(sucursales_sel, sucursales_all)
categorias_f = filtro_seguro(categorias_sel, categorias_all)
turnos_f = filtro_seguro(turnos_sel, turnos_all)
metodos_f = filtro_seguro(metodos_sel, metodos_all)

if len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas
else:
    fecha_inicio, fecha_fin = fecha_min, fecha_max

df_f = df[
    (df["Fecha"].dt.date >= fecha_inicio) &
    (df["Fecha"].dt.date <= fecha_fin) &
    (df["NombreSucursal"].isin(sucursales_f)) &
    (df["Categoría"].isin(categorias_f)) &
    (df["Turno"].isin(turnos_f)) &
    (df["MetodoPago"].isin(metodos_f))
]

if df_f.empty:
    st.warning("⚠️ Sin datos con los filtros seleccionados.")
    st.stop()


# ============================================================
# FUNCIÓN: KPIs COMPACTOS
# ============================================================
def mostrar_kpis(df_datos):
    col1, col2, col3, col4, col5 = st.columns(5)
    ventas = df_datos["TotalVenta"].sum()
    ganancia = df_datos["Ganancia"].sum()
    margen = (ganancia / ventas * 100) if ventas > 0 else 0
    n_trans = df_datos["VentaID"].nunique()
    ticket = ventas / n_trans if n_trans > 0 else 0
    col1.metric("💰 Ventas", f"${ventas:,.0f}")
    col2.metric("📈 Ganancia", f"${ganancia:,.0f}")
    col3.metric("💎 Margen", f"{margen:.1f}%")
    col4.metric("🧾 Ventas #", f"{n_trans:,}")
    col5.metric("🎫 Ticket Prom.", f"${ticket:.2f}")


# ============================================================
# HEADER COMPACTO
# ============================================================
st.markdown(f'<p class="main-header">🛒 Dashboard BI - Minimarket &nbsp;|&nbsp; <span style="font-size:1rem; color:#666;">{pagina}</span></p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="sub-header">📅 {fecha_inicio.strftime("%d/%m/%Y")} → {fecha_fin.strftime("%d/%m/%Y")} '
    f'&nbsp;|&nbsp; 🏪 {len(sucursales_f)}/{len(sucursales_all)} sucursales '
    f'&nbsp;|&nbsp; 📦 {len(categorias_f)}/{len(categorias_all)} categorías</p>',
    unsafe_allow_html=True
)


# ============================================================
# 📊 PÁGINA 1: VISTA GENERAL (compacta)
# ============================================================
if pagina == "📊 General":

    mostrar_kpis(df_f)

    # FILA 1: Evolución temporal (ocupa todo el ancho)
    st.markdown('<p class="section-title">📈 Evolución de Ventas y Ganancia</p>', unsafe_allow_html=True)
    ventas_mensuales = df_f.groupby("AñoMes").agg(
        TotalVenta=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum")
    ).reset_index().sort_values("AñoMes")

    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(
        x=ventas_mensuales["AñoMes"], y=ventas_mensuales["TotalVenta"],
        name="Ventas", mode="lines", stackgroup="one",
        line=dict(color="#1f4e79", width=0.5),
        fillcolor="rgba(31,78,121,0.6)"
    ))
    fig_area.add_trace(go.Scatter(
        x=ventas_mensuales["AñoMes"], y=ventas_mensuales["Ganancia"],
        name="Ganancia", mode="lines", stackgroup="two",
        line=dict(color="#28a745", width=0.5),
        fillcolor="rgba(40,167,69,0.5)"
    ))
    fig_area.update_layout(
        height=220, hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
        xaxis_title="", yaxis_title=""
    )
    st.plotly_chart(fig_area, use_container_width=True)

    # FILA 2: Sucursal + Categoría + Anual (3 columnas)
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown('<p class="section-title">🏪 Ventas por Sucursal</p>', unsafe_allow_html=True)
        vs = df_f.groupby("NombreSucursal").agg(TotalVenta=("TotalVenta", "sum")).reset_index().sort_values("TotalVenta", ascending=True)
        fig_vs = go.Figure()
        fig_vs.add_trace(go.Bar(
            y=vs["NombreSucursal"], x=vs["TotalVenta"], orientation="h",
            marker_color="#1f4e79",
            text=vs["TotalVenta"].apply(lambda x: f"${x/1000:.0f}K"), textposition="inside",
            textfont=dict(color="white", size=11)
        ))
        fig_vs.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                              xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_vs, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">📦 Ventas por Categoría</p>', unsafe_allow_html=True)
        vc = df_f.groupby("Categoría")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False)
        fig_vc = px.pie(vc, values="TotalVenta", names="Categoría", hole=0.55,
                        color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_vc.update_traces(textposition="inside", textinfo="percent", textfont_size=10)
        fig_vc.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                              legend=dict(font=dict(size=9), orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0))
        st.plotly_chart(fig_vc, use_container_width=True)

    with col3:
        st.markdown('<p class="section-title">📅 Comparativa Anual</p>', unsafe_allow_html=True)
        va = df_f.groupby("Año").agg(Ventas=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum")).reset_index()
        fig_anual = go.Figure()
        fig_anual.add_trace(go.Bar(x=va["Año"], y=va["Ventas"], name="Ventas", marker_color="#1f4e79"))
        fig_anual.add_trace(go.Bar(x=va["Año"], y=va["Ganancia"], name="Ganancia", marker_color="#28a745"))
        fig_anual.update_layout(barmode="group", height=230, margin=dict(l=10, r=10, t=10, b=10),
                                 legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
                                 xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_anual, use_container_width=True)


# ============================================================
# 🏆 PÁGINA 2: PRODUCTOS Y SUCURSALES
# ============================================================
elif pagina == "🏆 Productos":

    mostrar_kpis(df_f)

    # FILA 1: Top productos (2 columnas)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title">🥇 Top 10 Productos por Ventas</p>', unsafe_allow_html=True)
        top_v = df_f.groupby("NombreProducto")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False).head(10)
        fig_tv = px.bar(top_v.sort_values("TotalVenta"), x="TotalVenta", y="NombreProducto",
                        orientation="h", text_auto=".2s",
                        color="TotalVenta", color_continuous_scale="Blues")
        fig_tv.update_layout(height=270, margin=dict(l=10, r=10, t=10, b=10),
                              coloraxis_showscale=False, yaxis_title="", xaxis_title="",
                              yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig_tv, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">💎 Top 10 Productos por Ganancia</p>', unsafe_allow_html=True)
        top_g = df_f.groupby("NombreProducto")["Ganancia"].sum().reset_index().sort_values("Ganancia", ascending=False).head(10)
        fig_tg = px.bar(top_g.sort_values("Ganancia"), x="Ganancia", y="NombreProducto",
                        orientation="h", text_auto=".2s",
                        color="Ganancia", color_continuous_scale="Greens")
        fig_tg.update_layout(height=270, margin=dict(l=10, r=10, t=10, b=10),
                              coloraxis_showscale=False, yaxis_title="", xaxis_title="",
                              yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig_tg, use_container_width=True)

    # FILA 2: Heatmap + Rentabilidad
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown('<p class="section-title">🔥 Categoría × Sucursal (mapa de calor)</p>', unsafe_allow_html=True)
        pivot_cat_suc = df_f.pivot_table(index="Categoría", columns="NombreSucursal",
                                           values="TotalVenta", aggfunc="sum", fill_value=0)
        fig_heat1 = px.imshow(pivot_cat_suc, text_auto=".2s", aspect="auto",
                              color_continuous_scale="Blues")
        fig_heat1.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10),
                                 xaxis_title="", yaxis_title="",
                                 xaxis=dict(tickfont=dict(size=10)),
                                 yaxis=dict(tickfont=dict(size=10)),
                                 coloraxis_showscale=False)
        st.plotly_chart(fig_heat1, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">📊 Ventas vs Ganancia por Categoría</p>', unsafe_allow_html=True)
        rent = df_f.groupby("Categoría").agg(
            Ventas=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum")
        ).reset_index().sort_values("Ventas", ascending=False)

        fig_rent = go.Figure()
        fig_rent.add_trace(go.Bar(x=rent["Categoría"], y=rent["Ventas"], name="Ventas", marker_color="#1f4e79"))
        fig_rent.add_trace(go.Bar(x=rent["Categoría"], y=rent["Ganancia"], name="Ganancia", marker_color="#28a745"))
        fig_rent.update_layout(barmode="group", height=250, margin=dict(l=10, r=10, t=10, b=10),
                                legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
                                xaxis_title="", yaxis_title="",
                                xaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig_rent, use_container_width=True)


# ============================================================
# 🕐 PÁGINA 3: PATRONES DE CONSUMO
# ============================================================
elif pagina == "🕐 Patrones":

    mostrar_kpis(df_f)

    orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    orden_turnos = ["Mañana", "Tarde", "Noche"]

    # FILA 1: Heatmap principal (ancho completo)
    st.markdown('<p class="section-title">🔥 Día de la Semana × Turno (mapa de calor de ventas)</p>', unsafe_allow_html=True)
    pivot_dia_turno = df_f.pivot_table(index="Turno", columns="DiaSemana",
                                         values="TotalVenta", aggfunc="sum", fill_value=0)
    pivot_dia_turno = pivot_dia_turno.reindex(index=[t for t in orden_turnos if t in pivot_dia_turno.index])
    pivot_dia_turno = pivot_dia_turno[[d for d in orden_dias if d in pivot_dia_turno.columns]]

    fig_heat2 = px.imshow(pivot_dia_turno, text_auto=".2s", aspect="auto",
                          color_continuous_scale="Reds")
    fig_heat2.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10),
                             xaxis_title="", yaxis_title="",
                             coloraxis_showscale=False)
    st.plotly_chart(fig_heat2, use_container_width=True)

    # FILA 2: Turno + Día + Método pago (3 columnas)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<p class="section-title">🕐 Ventas por Turno</p>', unsafe_allow_html=True)
        vt = df_f.groupby("Turno")["TotalVenta"].sum().reset_index()
        vt["Turno"] = pd.Categorical(vt["Turno"], categories=orden_turnos, ordered=True)
        vt = vt.sort_values("Turno")
        fig_vt = px.bar(vt, x="Turno", y="TotalVenta", text_auto=".2s",
                        color="Turno", color_discrete_sequence=["#FFB84D", "#FF7F50", "#4A5FBF"])
        fig_vt.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                              showlegend=False, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_vt, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">📅 Ventas por Día</p>', unsafe_allow_html=True)
        vd = df_f.groupby("DiaSemana")["TotalVenta"].sum().reset_index()
        vd["DiaSemana"] = pd.Categorical(vd["DiaSemana"], categories=orden_dias, ordered=True)
        vd = vd.sort_values("DiaSemana")
        vd["DiaAbrev"] = vd["DiaSemana"].astype(str).str[:3]
        fig_vd = px.bar(vd, x="DiaAbrev", y="TotalVenta", text_auto=".2s",
                        color="TotalVenta", color_continuous_scale="Blues")
        fig_vd.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                              coloraxis_showscale=False, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_vd, use_container_width=True)

    with col3:
        st.markdown('<p class="section-title">💳 Método de Pago</p>', unsafe_allow_html=True)
        vp = df_f.groupby("MetodoPago")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False)
        fig_vp = px.pie(vp, values="TotalVenta", names="MetodoPago", hole=0.55,
                        color_discrete_sequence=px.colors.qualitative.Set2)
        fig_vp.update_traces(textposition="inside", textinfo="percent", textfont_size=10)
        fig_vp.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                              legend=dict(font=dict(size=9), orientation="v",
                                          yanchor="middle", y=0.5, xanchor="left", x=1.0))
        st.plotly_chart(fig_vp, use_container_width=True)