"""
============================================================
DASHBOARD BI - MINIMARKET - VERSIÓN 2
============================================================
Autor: Ricardo Muñoz
Empresa: G&S Gestión y Sistemas
Fecha: Julio 2026
============================================================
MEJORAS RESPECTO A V1 (basadas en feedback del analista):
  ✅ Navegación multi-página (3 vistas)
  ✅ Filtros con fallback (vacío = todos los datos)
  ✅ Heatmap: Categoría × Sucursal
  ✅ Heatmap: Día de semana × Turno
  ✅ Gráfico de área (reemplaza líneas con puntos)
  ✅ KPIs visibles en todas las páginas
  ✅ Placeholders informativos en filtros
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
    page_title="Dashboard BI v2 - Minimarket | G&S",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.3rem; font-weight: 700; color: #1f4e79;
        padding-bottom: 0.5rem; border-bottom: 3px solid #1f4e79;
        margin-bottom: 1rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.7rem; font-weight: 700; color: #1f4e79;
    }
    [data-testid="stMetricLabel"] { font-size: 0.9rem; font-weight: 600; }
    .page-badge {
        background-color: #1f4e79; color: white;
        padding: 0.3rem 0.8rem; border-radius: 20px;
        font-size: 0.85rem; display: inline-block; margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    # Como este archivo está en /versions, subimos un nivel para llegar a la raíz
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
# SIDEBAR - NAVEGACIÓN + FILTROS
# ============================================================
st.sidebar.image("https://img.icons8.com/color/96/shopping-cart-loaded.png", width=80)
st.sidebar.title("Dashboard BI")
st.sidebar.caption("G&S Gestión y Sistemas • v2")
st.sidebar.markdown("---")

pagina = st.sidebar.radio(
    "📄 Navegación",
    options=["📊 Vista General", "🏆 Productos y Sucursales", "🕐 Patrones de Consumo"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Filtros")

fecha_min = df["Fecha"].min().date()
fecha_max = df["Fecha"].max().date()

rango_fechas = st.sidebar.date_input(
    "📅 Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min, max_value=fecha_max
)

sucursales_all = sorted(df["NombreSucursal"].unique())
sucursales_sel = st.sidebar.multiselect("🏪 Sucursales", options=sucursales_all, default=[], placeholder="Todas las sucursales")

categorias_all = sorted(df["Categoría"].unique())
categorias_sel = st.sidebar.multiselect("📦 Categorías", options=categorias_all, default=[], placeholder="Todas las categorías")

turnos_all = sorted(df["Turno"].unique())
turnos_sel = st.sidebar.multiselect("🕐 Turnos", options=turnos_all, default=[], placeholder="Todos los turnos")

metodos_all = sorted(df["MetodoPago"].unique())
metodos_sel = st.sidebar.multiselect("💳 Método de pago", options=metodos_all, default=[], placeholder="Todos los métodos")

st.sidebar.markdown("---")
st.sidebar.info("💡 Deja los filtros vacíos para ver el consolidado total.")


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
    st.warning("⚠️ No hay datos con los filtros seleccionados.")
    st.stop()


# ============================================================
# FUNCIÓN KPIs
# ============================================================
def mostrar_kpis(df_datos):
    col1, col2, col3, col4, col5 = st.columns(5)
    ventas = df_datos["TotalVenta"].sum()
    ganancia = df_datos["Ganancia"].sum()
    margen = (ganancia / ventas * 100) if ventas > 0 else 0
    n_trans = df_datos["VentaID"].nunique()
    ticket = ventas / n_trans if n_trans > 0 else 0
    col1.metric("💰 Ventas Totales", f"${ventas:,.0f}")
    col2.metric("📈 Ganancia Total", f"${ganancia:,.0f}")
    col3.metric("💎 Margen (%)", f"{margen:.1f}%")
    col4.metric("🧾 Transacciones", f"{n_trans:,}")
    col5.metric("🎫 Ticket Promedio", f"${ticket:.2f}")


# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="main-header">🛒 Dashboard BI - Minimarket</div>', unsafe_allow_html=True)
st.markdown(
    f'<span class="page-badge">{pagina}</span> &nbsp; '
    f"📅 **Período:** {fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')} &nbsp;|&nbsp; "
    f"🏪 **Sucursales:** {len(sucursales_f)} de {len(sucursales_all)}",
    unsafe_allow_html=True
)
st.markdown("")


# ============================================================
# PÁGINA 1: VISTA GENERAL
# ============================================================
if pagina == "📊 Vista General":
    st.subheader("📊 Indicadores Clave (KPIs)")
    mostrar_kpis(df_f)
    st.markdown("---")

    st.subheader("📈 Evolución de Ventas y Ganancia")
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
    fig_area.update_layout(xaxis_title="Mes", yaxis_title="Monto ($)", hovermode="x unified", height=400)
    st.plotly_chart(fig_area, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏪 Ventas por Sucursal")
        vs = df_f.groupby("NombreSucursal").agg(TotalVenta=("TotalVenta", "sum")).reset_index().sort_values("TotalVenta", ascending=True)
        fig_vs = go.Figure()
        fig_vs.add_trace(go.Bar(
            y=vs["NombreSucursal"], x=vs["TotalVenta"], orientation="h",
            marker_color="#1f4e79",
            text=vs["TotalVenta"].apply(lambda x: f"${x:,.0f}"), textposition="outside"
        ))
        fig_vs.update_layout(height=350, showlegend=False, xaxis_title="Ventas ($)")
        st.plotly_chart(fig_vs, use_container_width=True)

    with col2:
        st.subheader("📦 Distribución por Categoría")
        vc = df_f.groupby("Categoría")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False)
        fig_vc = px.pie(vc, values="TotalVenta", names="Categoría", hole=0.5,
                        color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_vc.update_traces(textposition="inside", textinfo="percent+label")
        fig_vc.update_layout(height=350)
        st.plotly_chart(fig_vc, use_container_width=True)

    st.subheader("📅 Comparativa Anual")
    va = df_f.groupby("Año").agg(Ventas=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum")).reset_index()
    fig_anual = go.Figure()
    fig_anual.add_trace(go.Bar(x=va["Año"], y=va["Ventas"], name="Ventas", marker_color="#1f4e79",
                                text=va["Ventas"].apply(lambda x: f"${x:,.0f}"), textposition="outside"))
    fig_anual.add_trace(go.Bar(x=va["Año"], y=va["Ganancia"], name="Ganancia", marker_color="#28a745",
                                text=va["Ganancia"].apply(lambda x: f"${x:,.0f}"), textposition="outside"))
    fig_anual.update_layout(barmode="group", height=380, xaxis_title="Año", yaxis_title="Monto ($)")
    st.plotly_chart(fig_anual, use_container_width=True)


# ============================================================
# PÁGINA 2: PRODUCTOS Y SUCURSALES
# ============================================================
elif pagina == "🏆 Productos y Sucursales":
    st.subheader("📊 KPIs del período filtrado")
    mostrar_kpis(df_f)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🥇 Top 10 Productos por Ventas")
        top_v = df_f.groupby("NombreProducto")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False).head(10)
        fig_tv = px.bar(top_v.sort_values("TotalVenta"), x="TotalVenta", y="NombreProducto",
                        orientation="h", text_auto=".2s", color="TotalVenta", color_continuous_scale="Blues")
        fig_tv.update_layout(height=450, coloraxis_showscale=False, yaxis_title="", xaxis_title="Ventas ($)")
        st.plotly_chart(fig_tv, use_container_width=True)

    with col2:
        st.subheader("💎 Top 10 Productos por Ganancia")
        top_g = df_f.groupby("NombreProducto")["Ganancia"].sum().reset_index().sort_values("Ganancia", ascending=False).head(10)
        fig_tg = px.bar(top_g.sort_values("Ganancia"), x="Ganancia", y="NombreProducto",
                        orientation="h", text_auto=".2s", color="Ganancia", color_continuous_scale="Greens")
        fig_tg.update_layout(height=450, coloraxis_showscale=False, yaxis_title="", xaxis_title="Ganancia ($)")
        st.plotly_chart(fig_tg, use_container_width=True)

    st.subheader("🔥 Mapa de Calor: Ventas por Categoría y Sucursal")
    st.caption("💡 Identifica qué categoría rinde mejor en cada sucursal para optimizar el surtido.")
    pivot_cat_suc = df_f.pivot_table(index="Categoría", columns="NombreSucursal",
                                       values="TotalVenta", aggfunc="sum", fill_value=0)
    fig_heat1 = px.imshow(pivot_cat_suc, text_auto=".2s", aspect="auto",
                          color_continuous_scale="Blues", labels=dict(color="Ventas ($)"))
    fig_heat1.update_layout(height=450, xaxis_title="Sucursal", yaxis_title="Categoría")
    st.plotly_chart(fig_heat1, use_container_width=True)

    st.subheader("📊 Rentabilidad por Categoría")
    rent = df_f.groupby("Categoría").agg(
        Ventas=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum"), Unidades=("Cantidad", "sum")
    ).reset_index()
    rent["Margen(%)"] = (rent["Ganancia"] / rent["Ventas"] * 100).round(1)
    rent = rent.sort_values("Ventas", ascending=False)

    fig_rent = go.Figure()
    fig_rent.add_trace(go.Bar(x=rent["Categoría"], y=rent["Ventas"], name="Ventas ($)", marker_color="#1f4e79"))
    fig_rent.add_trace(go.Bar(x=rent["Categoría"], y=rent["Ganancia"], name="Ganancia ($)", marker_color="#28a745"))
    fig_rent.update_layout(barmode="group", height=400, xaxis_title="Categoría", yaxis_title="Monto ($)")
    st.plotly_chart(fig_rent, use_container_width=True)

    with st.expander("📋 Ver tabla de rentabilidad detallada"):
        st.dataframe(rent, use_container_width=True)


# ============================================================
# PÁGINA 3: PATRONES DE CONSUMO
# ============================================================
elif pagina == "🕐 Patrones de Consumo":
    st.subheader("📊 KPIs del período filtrado")
    mostrar_kpis(df_f)
    st.markdown("---")

    st.subheader("🔥 Mapa de Calor: Día de la Semana × Turno")
    st.caption("💡 Identifica los días y turnos con mayor volumen para optimizar personal y stock.")

    orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    orden_turnos = ["Mañana", "Tarde", "Noche"]

    pivot_dia_turno = df_f.pivot_table(index="Turno", columns="DiaSemana",
                                         values="TotalVenta", aggfunc="sum", fill_value=0)
    pivot_dia_turno = pivot_dia_turno.reindex(index=[t for t in orden_turnos if t in pivot_dia_turno.index])
    pivot_dia_turno = pivot_dia_turno[[d for d in orden_dias if d in pivot_dia_turno.columns]]

    fig_heat2 = px.imshow(pivot_dia_turno, text_auto=".2s", aspect="auto",
                          color_continuous_scale="Reds", labels=dict(color="Ventas ($)"))
    fig_heat2.update_layout(height=350, xaxis_title="Día de la Semana", yaxis_title="Turno")
    st.plotly_chart(fig_heat2, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🕐 Ventas por Turno")
        vt = df_f.groupby("Turno")["TotalVenta"].sum().reset_index()
        vt["Turno"] = pd.Categorical(vt["Turno"], categories=orden_turnos, ordered=True)
        vt = vt.sort_values("Turno")
        fig_vt = px.bar(vt, x="Turno", y="TotalVenta", text_auto=".2s",
                        color="Turno", color_discrete_sequence=["#FFB84D", "#FF7F50", "#4A5FBF"])
        fig_vt.update_layout(height=380, showlegend=False, xaxis_title="", yaxis_title="Ventas ($)")
        st.plotly_chart(fig_vt, use_container_width=True)

    with col2:
        st.subheader("📅 Ventas por Día de la Semana")
        vd = df_f.groupby("DiaSemana")["TotalVenta"].sum().reset_index()
        vd["DiaSemana"] = pd.Categorical(vd["DiaSemana"], categories=orden_dias, ordered=True)
        vd = vd.sort_values("DiaSemana")
        fig_vd = px.bar(vd, x="DiaSemana", y="TotalVenta", text_auto=".2s",
                        color="TotalVenta", color_continuous_scale="Blues")
        fig_vd.update_layout(height=380, coloraxis_showscale=False, xaxis_title="", yaxis_title="Ventas ($)")
        st.plotly_chart(fig_vd, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💳 Método de Pago Preferido")
        vp = df_f.groupby("MetodoPago")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False)
        fig_vp = px.pie(vp, values="TotalVenta", names="MetodoPago", hole=0.5,
                        color_discrete_sequence=px.colors.qualitative.Set2)
        fig_vp.update_traces(textposition="inside", textinfo="percent+label")
        fig_vp.update_layout(height=400)
        st.plotly_chart(fig_vp, use_container_width=True)

    with col2:
        st.subheader("📊 Ventas Mensuales por Año")
        va_mes = df_f.groupby(["Año", "Mes"])["TotalVenta"].sum().reset_index()
        fig_ya = px.line(va_mes, x="Mes", y="TotalVenta", color="Año",
                         markers=False, line_shape="spline")
        fig_ya.update_layout(height=400, xaxis_title="Mes", yaxis_title="Ventas ($)",
                              xaxis=dict(tickmode="linear", tick0=1, dtick=1))
        st.plotly_chart(fig_ya, use_container_width=True)


# ============================================================
# TABLA + DESCARGA
# ============================================================
st.markdown("---")
with st.expander("📋 Ver tabla detallada y descargar datos filtrados"):
    columnas_mostrar = ["Fecha", "NombreSucursal", "Turno", "NombreProducto", "Categoría",
                         "Cantidad", "TotalVenta", "Ganancia", "MargenPct", "MetodoPago"]
    st.dataframe(df_f[columnas_mostrar].head(1000), use_container_width=True, height=350)
    st.caption(f"Mostrando primeras 1,000 filas de {len(df_f):,} transacciones filtradas.")
    csv = df_f[columnas_mostrar].to_csv(index=False).encode("utf-8")
    st.download_button(label="📥 Descargar CSV", data=csv,
                       file_name=f"ventas_filtradas_{fecha_inicio}_{fecha_fin}.csv", mime="text/csv")

st.markdown("---")
st.caption("📊 Dashboard BI v2 • Ricardo Muñoz • G&S Gestión y Sistemas S.A.C. • 2026")