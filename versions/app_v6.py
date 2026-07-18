"""
============================================================
DASHBOARD BI - MINIMARKET - VERSIÓN 6
============================================================
Autor: Ricardo Muñoz
Empresa: G&S Gestión y Sistemas
Fecha: Julio 2026
============================================================
MEJORAS RESPECTO A V5:
  ✅ Leyenda de color visible en los mapas de calor
  ✅ Barra de color con título "Ventas ($)" en cada heatmap
  ✅ Interpretación clara de tonos claros → oscuros
============================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import shutil

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="Dashboard BI v6 - Minimarket | G&S",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem; padding-bottom: 0rem;
        padding-left: 2rem; padding-right: 2rem; max-width: 100%;
    }
    .main-header {
        font-size: 1.5rem; font-weight: 700;
        color: #1f4e79; margin: 0; padding: 0;
    }
    .sub-header { font-size: 0.85rem; color: #888; margin-bottom: 0.5rem; }
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 0.7rem 1rem; border-radius: 10px;
        border-left: 4px solid #1f4e79;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08); min-height: 85px;
    }
    .kpi-title {
        font-size: 0.78rem; font-weight: 600; color: #555 !important;
        margin: 0; display: flex; align-items: center; gap: 0.3rem;
    }
    .kpi-value {
        font-size: 1.5rem; font-weight: 700; color: #1f4e79 !important; margin: 0.2rem 0 0 0;
    }
    .kpi-icon { font-size: 1.1rem; }
    @media (prefers-color-scheme: dark) {
        .kpi-card {
            background: linear-gradient(135deg, #2b2b2b 0%, #1e1e1e 100%);
            border-left: 4px solid #4A90E2;
        }
        .kpi-title { color: #e0e0e0 !important; }
        .kpi-value { color: #ffffff !important; }
    }
    .element-container { margin-bottom: 0.3rem; }
    .section-title {
        font-size: 0.9rem; font-weight: 600; color: #1f4e79;
        margin: 0.4rem 0 0.2rem 0; padding-bottom: 0.2rem;
        border-bottom: 1px solid #e0e0e0;
    }
    footer { visibility: hidden; }
    .stRadio > label { font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
RUTA_DATA = BASE_DIR / "data"
RUTA_PROCESADO = BASE_DIR / "data_processed"
RUTA_EXCEL = RUTA_DATA / "base_datos_minimarket_v3.xlsx"
RUTA_PARQUET = RUTA_PROCESADO / "ventas_consolidado.parquet"
RUTA_LOG = RUTA_PROCESADO / "etl_log.txt"

RUTA_DATA.mkdir(exist_ok=True)
RUTA_PROCESADO.mkdir(exist_ok=True)


# ============================================================
# FUNCIONES ETL
# ============================================================
HOJAS_REQUERIDAS = ["Sucursales", "Productos", "Historial_Ventas"]
COLUMNAS_REQUERIDAS = {
    "Sucursales": ["SucursalID", "NombreSucursal", "UbicacionTipo"],
    "Productos": ["ProductoID", "NombreProducto", "Categoría", "PrecioCompra", "PrecioVenta"],
    "Historial_Ventas": ["VentaID", "Fecha", "Año", "Turno", "SucursalID", "ProductoID",
                          "Cantidad", "TotalVenta", "TotalCosto", "Ganancia", "MetodoPago"]
}


def validar_excel(archivo):
    """Valida que el Excel tenga las 3 hojas y columnas requeridas."""
    try:
        xl = pd.ExcelFile(archivo)
        hojas_encontradas = xl.sheet_names

        hojas_faltantes = [h for h in HOJAS_REQUERIDAS if h not in hojas_encontradas]
        if hojas_faltantes:
            return False, f"Faltan las siguientes hojas: {', '.join(hojas_faltantes)}"

        for hoja, cols_req in COLUMNAS_REQUERIDAS.items():
            df_temp = pd.read_excel(archivo, sheet_name=hoja, nrows=1)
            cols_faltantes = [c for c in cols_req if c not in df_temp.columns]
            if cols_faltantes:
                return False, f"En la hoja '{hoja}' faltan las columnas: {', '.join(cols_faltantes)}"

        return True, "Estructura válida ✅"
    except Exception as e:
        return False, f"Error al leer el archivo: {str(e)}"


def procesar_etl(archivo_excel):
    """Ejecuta el ETL completo y guarda el resultado en Parquet."""
    df_sucursales = pd.read_excel(archivo_excel, sheet_name="Sucursales")
    df_productos = pd.read_excel(archivo_excel, sheet_name="Productos")
    df_ventas = pd.read_excel(archivo_excel, sheet_name="Historial_Ventas")

    df_ventas["Fecha"] = pd.to_datetime(df_ventas["Fecha"], errors="coerce")
    df_ventas = df_ventas.dropna(subset=["Fecha"])

    for col in ["Cantidad", "TotalVenta", "TotalCosto", "Ganancia"]:
        df_ventas[col] = pd.to_numeric(df_ventas[col], errors="coerce")

    df_productos["PrecioCompra"] = pd.to_numeric(df_productos["PrecioCompra"], errors="coerce")
    df_productos["PrecioVenta"] = pd.to_numeric(df_productos["PrecioVenta"], errors="coerce")

    for df_t in [df_sucursales, df_productos, df_ventas]:
        for col in df_t.select_dtypes(include="object").columns:
            df_t[col] = df_t[col].astype(str).str.strip()

    df = df_ventas.merge(df_sucursales, on="SucursalID", how="left")
    df = df.merge(df_productos, on="ProductoID", how="left")

    df["Mes"] = df["Fecha"].dt.month
    df["MesNombre"] = df["Fecha"].dt.strftime("%B")
    df["Trimestre"] = df["Fecha"].dt.quarter
    df["DiaSemana"] = df["Fecha"].dt.day_name()
    df["AñoMes"] = df["Fecha"].dt.strftime("%Y-%m")

    dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
    df["DiaSemana"] = df["DiaSemana"].map(dias_es)

    meses_es = {"January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
                "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
                "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"}
    df["MesNombre"] = df["MesNombre"].map(meses_es)

    df["MargenPct"] = np.where(df["TotalVenta"] > 0, (df["Ganancia"] / df["TotalVenta"]) * 100, 0).round(2)
    df["PrecioUnitarioVenta"] = np.where(df["Cantidad"] > 0, df["TotalVenta"] / df["Cantidad"], 0).round(2)

    df = df.sort_values("Fecha").reset_index(drop=True)

    df.to_parquet(RUTA_PARQUET, index=False)

    with open(RUTA_LOG, "w", encoding="utf-8") as f:
        f.write(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de filas: {len(df):,}\n")
        f.write(f"Rango: {df['Fecha'].min()} → {df['Fecha'].max()}\n")

    return len(df), df["Fecha"].min(), df["Fecha"].max()


def obtener_fecha_actualizacion():
    """Lee la fecha de última actualización desde el log."""
    if RUTA_LOG.exists():
        try:
            with open(RUTA_LOG, "r", encoding="utf-8") as f:
                primera_linea = f.readline().strip()
            return primera_linea.replace("Última actualización: ", "")
        except:
            return "Sin registro"
    return "Sin registro"


# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    df = pd.read_parquet(RUTA_PARQUET)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


df = cargar_datos()


def filtro_seguro(seleccion, todas_las_opciones):
    return seleccion if seleccion else todas_las_opciones


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("### 🛒 Dashboard BI")
st.sidebar.caption("G&S • v6 heatmaps con leyenda")

pagina = st.sidebar.radio(
    "📄 Página",
    options=["📊 General", "🏆 Productos", "🕐 Patrones"],
    index=0
)

st.sidebar.markdown("---")

# ==== PANEL DE ADMINISTRACIÓN (upload) ====
with st.sidebar.expander("⚙️ Administración - Subir Excel"):
    st.caption("Sube un nuevo archivo Excel con la misma estructura para actualizar los datos.")

    archivo_subido = st.file_uploader(
        "Selecciona archivo .xlsx",
        type=["xlsx"],
        help="Debe contener las hojas: Sucursales, Productos, Historial_Ventas"
    )

    if archivo_subido is not None:
        with st.spinner("🔍 Validando archivo..."):
            valido, mensaje = validar_excel(archivo_subido)

        if not valido:
            st.error(f"❌ {mensaje}")
        else:
            st.success(mensaje)

            try:
                st.caption(f"📄 **{archivo_subido.name}** ({archivo_subido.size/1024:.1f} KB)")

                info_hojas = []
                for hoja in HOJAS_REQUERIDAS:
                    n = len(pd.read_excel(archivo_subido, sheet_name=hoja))
                    info_hojas.append(f"• {hoja}: {n:,} filas")
                st.caption("\n".join(info_hojas))
            except Exception as e:
                st.warning(f"Vista previa no disponible: {e}")

            if st.button("🚀 Procesar y actualizar dashboard", type="primary", use_container_width=True):
                with st.spinner("⚙️ Procesando ETL... esto puede tardar unos segundos"):
                    try:
                        nombre_archivo = archivo_subido.name
                        ruta_nueva = RUTA_DATA / nombre_archivo
                        with open(ruta_nueva, "wb") as f:
                            f.write(archivo_subido.getbuffer())

                        n_filas, fecha_min_new, fecha_max_new = procesar_etl(ruta_nueva)

                        st.cache_data.clear()

                        st.success(f"✅ ¡Actualizado! {n_filas:,} filas procesadas.")
                        st.caption(f"Rango: {fecha_min_new.date()} → {fecha_max_new.date()}")
                        st.balloons()

                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error durante el ETL: {str(e)}")

    st.caption(f"🕓 Última actualización: {obtener_fecha_actualizacion()}")

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
# KPIs
# ============================================================
def kpi_card(icono, titulo, valor):
    return f"""
    <div class="kpi-card">
        <p class="kpi-title"><span class="kpi-icon">{icono}</span> {titulo}</p>
        <p class="kpi-value">{valor}</p>
    </div>
    """


def mostrar_kpis(df_datos):
    col1, col2, col3, col4, col5 = st.columns(5)
    ventas = df_datos["TotalVenta"].sum()
    ganancia = df_datos["Ganancia"].sum()
    margen = (ganancia / ventas * 100) if ventas > 0 else 0
    n_trans = df_datos["VentaID"].nunique()
    ticket = ventas / n_trans if n_trans > 0 else 0
    with col1:
        st.markdown(kpi_card("💰", "Ventas Totales", f"${ventas:,.0f}"), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_card("📈", "Ganancia Total", f"${ganancia:,.0f}"), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_card("💎", "Margen (%)", f"{margen:.1f}%"), unsafe_allow_html=True)
    with col4:
        st.markdown(kpi_card("🧾", "Transacciones", f"{n_trans:,}"), unsafe_allow_html=True)
    with col5:
        st.markdown(kpi_card("🎫", "Ticket Promedio", f"${ticket:.2f}"), unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================
fecha_upd = obtener_fecha_actualizacion()
st.markdown(f'<p class="main-header">🛒 Dashboard BI - Minimarket &nbsp;|&nbsp; <span style="font-size:1rem; color:#888;">{pagina}</span></p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="sub-header">📅 {fecha_inicio.strftime("%d/%m/%Y")} → {fecha_fin.strftime("%d/%m/%Y")} '
    f'&nbsp;|&nbsp; 🏪 {len(sucursales_f)}/{len(sucursales_all)} sucursales '
    f'&nbsp;|&nbsp; 📦 {len(categorias_f)}/{len(categorias_all)} categorías '
    f'&nbsp;|&nbsp; 🕓 Actualizado: {fecha_upd}</p>',
    unsafe_allow_html=True
)


# ============================================================
# PÁGINA 1: VISTA GENERAL
# ============================================================
if pagina == "📊 General":
    mostrar_kpis(df_f)

    st.markdown('<p class="section-title">🌊 Evolución de Ventas y Ganancia</p>', unsafe_allow_html=True)
    ventas_mensuales = df_f.groupby("AñoMes").agg(
        TotalVenta=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum")
    ).reset_index().sort_values("AñoMes")

    idx_max_v = ventas_mensuales["TotalVenta"].idxmax()
    idx_max_g = ventas_mensuales["Ganancia"].idxmax()
    pico_v_x = ventas_mensuales.loc[idx_max_v, "AñoMes"]
    pico_v_y = ventas_mensuales.loc[idx_max_v, "TotalVenta"]
    pico_g_x = ventas_mensuales.loc[idx_max_g, "AñoMes"]
    pico_g_y = ventas_mensuales.loc[idx_max_g, "Ganancia"]

    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(
        x=ventas_mensuales["AñoMes"], y=ventas_mensuales["TotalVenta"],
        name="Ventas", mode="lines",
        line=dict(color="#1f4e79", width=2, shape="spline", smoothing=1.3),
        fill="tozeroy", fillcolor="rgba(31,78,121,0.35)",
        hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>"
    ))
    fig_area.add_trace(go.Scatter(
        x=ventas_mensuales["AñoMes"], y=ventas_mensuales["Ganancia"],
        name="Ganancia", mode="lines",
        line=dict(color="#28a745", width=2, shape="spline", smoothing=1.3),
        fill="tozeroy", fillcolor="rgba(40,167,69,0.45)",
        hovertemplate="<b>%{x}</b><br>Ganancia: $%{y:,.0f}<extra></extra>"
    ))
    fig_area.add_trace(go.Scatter(
        x=[pico_v_x], y=[pico_v_y], mode="markers+text",
        marker=dict(color="#1f4e79", size=14, symbol="star", line=dict(color="white", width=2)),
        text=[f"🔝 ${pico_v_y:,.0f}"], textposition="top center",
        textfont=dict(color="#1f4e79", size=11, family="Arial Black"), showlegend=False,
        hovertemplate=f"<b>Pico Ventas</b><br>{pico_v_x}<br>${pico_v_y:,.0f}<extra></extra>"
    ))
    fig_area.add_trace(go.Scatter(
        x=[pico_g_x], y=[pico_g_y], mode="markers+text",
        marker=dict(color="#28a745", size=14, symbol="star", line=dict(color="white", width=2)),
        text=[f"🔝 ${pico_g_y:,.0f}"], textposition="bottom center",
        textfont=dict(color="#28a745", size=11, family="Arial Black"), showlegend=False,
        hovertemplate=f"<b>Pico Ganancia</b><br>{pico_g_x}<br>${pico_g_y:,.0f}<extra></extra>"
    ))
    fig_area.update_layout(
        height=240, hovermode="x unified",
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
        xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_area, use_container_width=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown('<p class="section-title">🏪 Ventas por Sucursal</p>', unsafe_allow_html=True)
        vs = df_f.groupby("NombreSucursal").agg(TotalVenta=("TotalVenta", "sum")).reset_index().sort_values("TotalVenta", ascending=True)
        fig_vs = go.Figure()
        fig_vs.add_trace(go.Bar(
            y=vs["NombreSucursal"], x=vs["TotalVenta"], orientation="h",
            marker=dict(color="#1f4e79"),
            text=vs["TotalVenta"].apply(lambda x: f"${x/1000:.0f}K"), textposition="inside",
            textfont=dict(color="white", size=11)
        ))
        fig_vs.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title="", yaxis_title="")
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
# PÁGINA 2: PRODUCTOS
# ============================================================
elif pagina == "🏆 Productos":
    mostrar_kpis(df_f)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="section-title">🥇 Top 10 Productos por Ventas</p>', unsafe_allow_html=True)
        top_v = df_f.groupby("NombreProducto")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False).head(10)
        fig_tv = px.bar(top_v.sort_values("TotalVenta"), x="TotalVenta", y="NombreProducto",
                        orientation="h", text_auto=".2s", color="TotalVenta", color_continuous_scale="Blues")
        fig_tv.update_layout(height=270, margin=dict(l=10, r=10, t=10, b=10),
                              coloraxis_showscale=False, yaxis_title="", xaxis_title="",
                              yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig_tv, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">💎 Top 10 Productos por Ganancia</p>', unsafe_allow_html=True)
        top_g = df_f.groupby("NombreProducto")["Ganancia"].sum().reset_index().sort_values("Ganancia", ascending=False).head(10)
        fig_tg = px.bar(top_g.sort_values("Ganancia"), x="Ganancia", y="NombreProducto",
                        orientation="h", text_auto=".2s", color="Ganancia", color_continuous_scale="Greens")
        fig_tg.update_layout(height=270, margin=dict(l=10, r=10, t=10, b=10),
                              coloraxis_showscale=False, yaxis_title="", xaxis_title="",
                              yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig_tg, use_container_width=True)

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown('<p class="section-title">🔥 Categoría × Sucursal (mapa de calor)</p>', unsafe_allow_html=True)
        pivot_cat_suc = df_f.pivot_table(index="Categoría", columns="NombreSucursal",
                                           values="TotalVenta", aggfunc="sum", fill_value=0)
        fig_heat1 = px.imshow(
            pivot_cat_suc, text_auto=".2s", aspect="auto",
            color_continuous_scale="Blues",
            labels=dict(color="Ventas ($)")
        )
        fig_heat1.update_layout(
            height=250, margin=dict(l=10, r=50, t=10, b=10),
            xaxis_title="", yaxis_title="",
            xaxis=dict(tickfont=dict(size=10)),
            yaxis=dict(tickfont=dict(size=10)),
            coloraxis_colorbar=dict(
                title=dict(text="Ventas<br>($)", font=dict(size=10)),
                thickness=12, len=0.9,
                tickfont=dict(size=9),
                tickformat="~s"
            )
        )
        st.plotly_chart(fig_heat1, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">📊 Ventas vs Ganancia por Categoría</p>', unsafe_allow_html=True)
        rent = df_f.groupby("Categoría").agg(Ventas=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum")).reset_index().sort_values("Ventas", ascending=False)
        fig_rent = go.Figure()
        fig_rent.add_trace(go.Bar(x=rent["Categoría"], y=rent["Ventas"], name="Ventas", marker_color="#1f4e79"))
        fig_rent.add_trace(go.Bar(x=rent["Categoría"], y=rent["Ganancia"], name="Ganancia", marker_color="#28a745"))
        fig_rent.update_layout(barmode="group", height=250, margin=dict(l=10, r=10, t=10, b=10),
                                legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
                                xaxis_title="", yaxis_title="", xaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig_rent, use_container_width=True)


# ============================================================
# PÁGINA 3: PATRONES
# ============================================================
elif pagina == "🕐 Patrones":
    mostrar_kpis(df_f)
    orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    orden_turnos = ["Mañana", "Tarde", "Noche"]

    st.markdown('<p class="section-title">🔥 Día de la Semana × Turno (mapa de calor de ventas)</p>', unsafe_allow_html=True)
    pivot_dia_turno = df_f.pivot_table(index="Turno", columns="DiaSemana", values="TotalVenta", aggfunc="sum", fill_value=0)
    pivot_dia_turno = pivot_dia_turno.reindex(index=[t for t in orden_turnos if t in pivot_dia_turno.index])
    pivot_dia_turno = pivot_dia_turno[[d for d in orden_dias if d in pivot_dia_turno.columns]]

    fig_heat2 = px.imshow(
        pivot_dia_turno, text_auto=".2s", aspect="auto",
        color_continuous_scale="Reds",
        labels=dict(color="Ventas ($)")
    )
    fig_heat2.update_layout(
        height=200, margin=dict(l=10, r=50, t=10, b=10),
        xaxis_title="", yaxis_title="",
        coloraxis_colorbar=dict(
            title=dict(text="Ventas<br>($)", font=dict(size=10)),
            thickness=12, len=0.9,
            tickfont=dict(size=9),
            tickformat="~s"
        )
    )
    st.plotly_chart(fig_heat2, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<p class="section-title">🕐 Ventas por Turno</p>', unsafe_allow_html=True)
        vt = df_f.groupby("Turno")["TotalVenta"].sum().reset_index()
        vt["Turno"] = pd.Categorical(vt["Turno"], categories=orden_turnos, ordered=True)
        vt = vt.sort_values("Turno")
        fig_vt = px.bar(vt, x="Turno", y="TotalVenta", text_auto=".2s",
                        color="Turno", color_discrete_sequence=["#FFB84D", "#FF7F50", "#4A5FBF"])
        fig_vt.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title="", yaxis_title="")
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
                              legend=dict(font=dict(size=9), orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0))
        st.plotly_chart(fig_vp, use_container_width=True)