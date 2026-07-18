
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
st.set_page_config(
    page_title="Dashboard BI v13 - Minimarket | G&S",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .pred-card {
        background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 100%);
        padding: 1rem; border-radius: 12px;
        border-left: 5px solid #9B59B6;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
        min-height: 130px;
    }
    .pred-title {
        font-size: 0.85rem; font-weight: 600; color: #666 !important;
        margin: 0 0 0.3rem 0;
    }
    .pred-value {
        font-size: 1.7rem; font-weight: 700; color: #9B59B6 !important; margin: 0;
    }
    .pred-subtitle {
        font-size: 0.75rem; color: #888; margin: 0.3rem 0 0 0;
    }
    .insight-box {
        background: linear-gradient(135deg, #fff9e6 0%, #fffef7 100%);
        padding: 1rem 1.2rem; border-radius: 10px;
        border-left: 4px solid #FFB84D;
        margin: 0.5rem 0;
    }
    .insight-title {
        font-size: 0.9rem; font-weight: 700; color: #B8860B !important;
        margin: 0 0 0.5rem 0;
    }
    .insight-text {
        font-size: 0.85rem; color: #555 !important; margin: 0.3rem 0;
        line-height: 1.5;
    }
    @media (prefers-color-scheme: dark) {
        .kpi-card {
            background: linear-gradient(135deg, #2b2b2b 0%, #1e1e1e 100%);
            border-left: 4px solid #4A90E2;
        }
        .kpi-title { color: #e0e0e0 !important; }
        .kpi-value { color: #ffffff !important; }
        .pred-card {
            background: linear-gradient(135deg, #2b2b3b 0%, #1e1e2b 100%);
            border-left: 5px solid #BB8FE0;
        }
        .pred-title { color: #e0e0e0 !important; }
        .pred-value { color: #BB8FE0 !important; }
        .insight-box {
            background: linear-gradient(135deg, #3d3520 0%, #2b2820 100%);
            border-left: 4px solid #FFB84D;
        }
        .insight-title { color: #FFB84D !important; }
        .insight-text { color: #e0e0e0 !important; }
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
    if RUTA_LOG.exists():
        try:
            with open(RUTA_LOG, "r", encoding="utf-8") as f:
                primera_linea = f.readline().strip()
            for prefijo in ["Última actualización: ", "Última ejecución ETL: "]:
                primera_linea = primera_linea.replace(prefijo, "")
            return primera_linea
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


def calcular_granularidad(df_datos, fecha_ini, fecha_fin):
    dias_rango = (fecha_fin - fecha_ini).days
    if dias_rango <= 60:
        df_datos = df_datos.copy()
        df_datos["_periodo"] = df_datos["Fecha"].dt.strftime("%Y-%m-%d")
        return df_datos, "_periodo", "día", "Diaria"
    elif dias_rango <= 180:
        df_datos = df_datos.copy()
        df_datos["_periodo"] = df_datos["Fecha"].dt.to_period("W").astype(str)
        return df_datos, "_periodo", "semana", "Semanal"
    else:
        return df_datos, "AñoMes", "mes", "Mensual"


# ============================================================
# 🔮 FUNCIONES DE MACHINE LEARNING
# ============================================================
@st.cache_data
def predecir_metrica_proximo_mes(df_datos, metrica="Ganancia"):
    """
    Predice el valor de una métrica para el próximo mes usando Regresión Lineal.
    metrica: "Ganancia" o "TotalVenta"
    Retorna: dict con toda la información del modelo.
    """
    df_mes = df_datos.groupby(pd.Grouper(key="Fecha", freq="MS")).agg(
        Valor=(metrica, "sum")
    ).reset_index()
    df_mes = df_mes[df_mes["Valor"] > 0].sort_values("Fecha").reset_index(drop=True)

    if len(df_mes) < 3:
        return None

    df_train = df_mes.tail(12).copy().reset_index(drop=True)
    X = np.array(range(len(df_train))).reshape(-1, 1)
    y = df_train["Valor"].values

    modelo = LinearRegression()
    modelo.fit(X, y)

    # Métricas
    y_pred_train = modelo.predict(X)
    r2 = modelo.score(X, y)
    mae = mean_absolute_error(y, y_pred_train)
    coef_tendencia = modelo.coef_[0]

    # Predicción
    x_pred = np.array([[len(df_train)]])
    y_pred = modelo.predict(x_pred)[0]

    std_dev = df_train["Valor"].std()
    rango_min = max(0, y_pred - std_dev)
    rango_max = y_pred + std_dev

    ultima_fecha = df_train["Fecha"].max()
    fecha_futura = ultima_fecha + pd.DateOffset(months=1)

    return {
        "prediccion": y_pred,
        "rango_min": rango_min,
        "rango_max": rango_max,
        "r2": r2,
        "mae": mae,
        "coef_tendencia": coef_tendencia,
        "std_dev": std_dev,
        "df_historico": df_train,
        "fecha_futura": fecha_futura,
        "ultimo_valor": df_train["Valor"].iloc[-1],
        "promedio_historico": df_train["Valor"].mean()
    }


def formatear_mes_es(fecha):
    """Convierte una fecha al formato 'Enero 2026'."""
    meses_es = {"January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
                "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
                "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"}
    texto = fecha.strftime("%B %Y")
    for en, es in meses_es.items():
        texto = texto.replace(en, es)
    return texto


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("### 🛒 Dashboard BI")
st.sidebar.caption("G&S • v13 predicción ejecutiva")

pagina = st.sidebar.radio(
    "📄 Página",
    options=["📊 General", "🏆 Productos", "🕐 Patrones", "🔮 Predicciones"],
    index=0
)

st.sidebar.markdown("---")

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
                with st.spinner("⚙️ Procesando ETL..."):
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
st.markdown(f'<p class="sub-header">🕓 Actualizado: {fecha_upd}</p>', unsafe_allow_html=True)


# ============================================================
# PÁGINA 1: VISTA GENERAL
# ============================================================
if pagina == "📊 General":
    mostrar_kpis(df_f)

    df_grano, col_periodo, unidad, etiqueta_gran = calcular_granularidad(df_f, fecha_inicio, fecha_fin)

    st.markdown(
        f'<p class="section-title">🌊 Evolución de Ventas y Ganancia '
        f'<span style="font-size:0.75rem; color:#888; font-weight:400;">'
        f'(vista {etiqueta_gran.lower()} - agrupado por {unidad})</span></p>',
        unsafe_allow_html=True
    )

    ventas_periodo = df_grano.groupby(col_periodo).agg(
        TotalVenta=("TotalVenta", "sum"), Ganancia=("Ganancia", "sum")
    ).reset_index().sort_values(col_periodo)

    if len(ventas_periodo) < 2:
        st.info(f"ℹ️ El rango seleccionado tiene un solo período ({unidad}). Mostrando como barras.")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=ventas_periodo[col_periodo], y=ventas_periodo["TotalVenta"],
                                   name="Ventas", marker_color="#1f4e79",
                                   text=ventas_periodo["TotalVenta"].apply(lambda x: f"${x:,.0f}"), textposition="outside"))
        fig_bar.add_trace(go.Bar(x=ventas_periodo[col_periodo], y=ventas_periodo["Ganancia"],
                                   name="Ganancia", marker_color="#28a745",
                                   text=ventas_periodo["Ganancia"].apply(lambda x: f"${x:,.0f}"), textposition="outside"))
        fig_bar.update_layout(barmode="group", height=240, margin=dict(l=10, r=10, t=25, b=10),
                                legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
                                xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        idx_max_v = ventas_periodo["TotalVenta"].idxmax()
        idx_max_g = ventas_periodo["Ganancia"].idxmax()
        pico_v_x = ventas_periodo.loc[idx_max_v, col_periodo]
        pico_v_y = ventas_periodo.loc[idx_max_v, "TotalVenta"]
        pico_g_x = ventas_periodo.loc[idx_max_g, col_periodo]
        pico_g_y = ventas_periodo.loc[idx_max_g, "Ganancia"]
        smoothing_val = 1.3 if len(ventas_periodo) >= 6 else 0.8

        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(x=ventas_periodo[col_periodo], y=ventas_periodo["TotalVenta"],
                                        name="Ventas", mode="lines",
                                        line=dict(color="#1f4e79", width=2, shape="spline", smoothing=smoothing_val),
                                        fill="tozeroy", fillcolor="rgba(31,78,121,0.35)",
                                        hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>"))
        fig_area.add_trace(go.Scatter(x=ventas_periodo[col_periodo], y=ventas_periodo["Ganancia"],
                                        name="Ganancia", mode="lines",
                                        line=dict(color="#28a745", width=2, shape="spline", smoothing=smoothing_val),
                                        fill="tozeroy", fillcolor="rgba(40,167,69,0.45)",
                                        hovertemplate="<b>%{x}</b><br>Ganancia: $%{y:,.0f}<extra></extra>"))
        fig_area.add_trace(go.Scatter(x=[pico_v_x], y=[pico_v_y], mode="markers+text",
                                        marker=dict(color="#1f4e79", size=14, symbol="star", line=dict(color="white", width=2)),
                                        text=[f"🔝 ${pico_v_y:,.0f}"], textposition="top center",
                                        textfont=dict(color="#1f4e79", size=11, family="Arial Black"), showlegend=False,
                                        hovertemplate=f"<b>Pico Ventas</b><br>{pico_v_x}<br>${pico_v_y:,.0f}<extra></extra>"))
        fig_area.add_trace(go.Scatter(x=[pico_g_x], y=[pico_g_y], mode="markers+text",
                                        marker=dict(color="#28a745", size=14, symbol="star", line=dict(color="white", width=2)),
                                        text=[f"🔝 ${pico_g_y:,.0f}"], textposition="bottom center",
                                        textfont=dict(color="#28a745", size=11, family="Arial Black"), showlegend=False,
                                        hovertemplate=f"<b>Pico Ganancia</b><br>{pico_g_x}<br>${pico_g_y:,.0f}<extra></extra>"))
        fig_area.update_layout(height=240, hovermode="x unified", margin=dict(l=10, r=10, t=25, b=10),
                                 legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
                                 xaxis_title="", yaxis_title="", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_area, use_container_width=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown('<p class="section-title">🏪 Ventas por Sucursal</p>', unsafe_allow_html=True)
        vs = df_f.groupby("NombreSucursal").agg(TotalVenta=("TotalVenta", "sum")).reset_index().sort_values("TotalVenta", ascending=True)
        total_vs = vs["TotalVenta"].sum()
        vs["Porcentaje"] = (vs["TotalVenta"] / total_vs * 100).round(1)
        vs["Etiqueta"] = vs.apply(lambda r: f"${r['TotalVenta']/1000:.0f}K ({r['Porcentaje']:.1f}%)", axis=1)
        fig_vs = go.Figure()
        fig_vs.add_trace(go.Bar(y=vs["NombreSucursal"], x=vs["TotalVenta"], orientation="h",
                                  marker=dict(color="#1f4e79"),
                                  text=vs["Etiqueta"], textposition="inside",
                                  textfont=dict(color="white", size=11),
                                  customdata=vs["Porcentaje"],
                                  hovertemplate="<b>%{y}</b><br>Ventas: $%{x:,.0f}<br>Participación: %{customdata:.1f}%<extra></extra>"))
        fig_vs.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_vs, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">📦 Ventas por Categoría</p>', unsafe_allow_html=True)
        vc = df_f.groupby("Categoría")["TotalVenta"].sum().reset_index().sort_values("TotalVenta", ascending=False).reset_index(drop=True)
        idx_min = vc["TotalVenta"].idxmin()
        categoria_critica = vc.loc[idx_min, "Categoría"]
        paleta_base = ["#1f4e79", "#2E6BA8", "#4A90E2", "#6BA5D9", "#8FBCE0", "#B3D3E6"]
        colores_cat = []
        for i, cat in enumerate(vc["Categoría"]):
            if cat == categoria_critica:
                colores_cat.append("#E74C3C")
            else:
                colores_cat.append(paleta_base[i % len(paleta_base)])
        fig_vc = go.Figure(data=[go.Pie(labels=vc["Categoría"], values=vc["TotalVenta"], hole=0.55,
                                          marker=dict(colors=colores_cat, line=dict(color="white", width=1)),
                                          textposition="inside", textinfo="percent",
                                          textfont=dict(size=10, color="white"),
                                          hovertemplate="<b>%{label}</b><br>Ventas: $%{value:,.0f}<br>Participación: %{percent}<extra></extra>")])
        fig_vc.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                              legend=dict(font=dict(size=9), orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0),
                              annotations=[dict(text=f"🔴 Crítico:<br><b>{categoria_critica[:15]}{'...' if len(categoria_critica) > 15 else ''}</b>",
                                                  x=0.5, y=0.5, font=dict(size=9, color="#E74C3C"), showarrow=False)])
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
        fig_heat1 = px.imshow(pivot_cat_suc, text_auto=".2s", aspect="auto",
                                color_continuous_scale="Blues", labels=dict(color="Ventas ($)"))
        fig_heat1.update_layout(height=250, margin=dict(l=10, r=50, t=10, b=10),
                                 xaxis_title="", yaxis_title="",
                                 xaxis=dict(tickfont=dict(size=10)), yaxis=dict(tickfont=dict(size=10)),
                                 coloraxis_colorbar=dict(title=dict(text="Ventas<br>($)", font=dict(size=10)),
                                                          thickness=12, len=0.9, tickfont=dict(size=9), tickformat="~s"))
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
    fig_heat2 = px.imshow(pivot_dia_turno, text_auto=".2s", aspect="auto",
                            color_continuous_scale="Reds", labels=dict(color="Ventas ($)"))
    fig_heat2.update_layout(height=200, margin=dict(l=10, r=50, t=10, b=10),
                              xaxis_title="", yaxis_title="",
                              coloraxis_colorbar=dict(title=dict(text="Ventas<br>($)", font=dict(size=10)),
                                                       thickness=12, len=0.9, tickfont=dict(size=9), tickformat="~s"))
    st.plotly_chart(fig_heat2, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<p class="section-title">🕐 Ventas por Turno (%)</p>', unsafe_allow_html=True)
        vt = df_f.groupby("Turno")["TotalVenta"].sum().reset_index()
        vt["Turno"] = pd.Categorical(vt["Turno"], categories=orden_turnos, ordered=True)
        vt = vt.sort_values("Turno")
        total_vt = vt["TotalVenta"].sum()
        vt["Porcentaje"] = (vt["TotalVenta"] / total_vt * 100).round(1)
        fig_vt = go.Figure()
        fig_vt.add_trace(go.Bar(x=vt["Turno"], y=vt["Porcentaje"],
                                  marker_color=["#FFB84D", "#FF7F50", "#4A5FBF"],
                                  text=vt["Porcentaje"].apply(lambda x: f"{x:.1f}%"),
                                  textposition="outside", textfont=dict(size=12),
                                  customdata=vt["TotalVenta"],
                                  hovertemplate="<b>%{x}</b><br>Porcentaje: %{y:.1f}%<br>Ventas: $%{customdata:,.0f}<extra></extra>"))
        fig_vt.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                              showlegend=False, xaxis_title="", yaxis_title="",
                              yaxis=dict(ticksuffix="%", range=[0, max(vt["Porcentaje"]) * 1.2]))
        st.plotly_chart(fig_vt, use_container_width=True)

    with col2:
        st.markdown('<p class="section-title">📅 Ventas por Día (%)</p>', unsafe_allow_html=True)
        vd = df_f.groupby("DiaSemana")["TotalVenta"].sum().reset_index()
        vd["DiaSemana"] = pd.Categorical(vd["DiaSemana"], categories=orden_dias, ordered=True)
        vd = vd.sort_values("DiaSemana")
        vd["DiaAbrev"] = vd["DiaSemana"].astype(str).str[:3]
        total_vd = vd["TotalVenta"].sum()
        vd["Porcentaje"] = (vd["TotalVenta"] / total_vd * 100).round(1)
        colores_dia = {"Lunes": "#1f4e79", "Martes": "#1f4e79", "Miércoles": "#1f4e79",
                        "Jueves": "#1f4e79", "Viernes": "#FF7F50", "Sábado": "#E74C3C", "Domingo": "#9B59B6"}
        colores_barras = [colores_dia.get(str(d), "#1f4e79") for d in vd["DiaSemana"]]
        fig_vd = go.Figure()
        fig_vd.add_trace(go.Bar(x=vd["DiaAbrev"], y=vd["Porcentaje"],
                                  marker=dict(color=colores_barras, line=dict(color="rgba(255,255,255,0.3)", width=1)),
                                  text=vd["Porcentaje"].apply(lambda x: f"{x:.1f}%"),
                                  textposition="outside", textfont=dict(size=11),
                                  customdata=np.stack([vd["DiaSemana"].astype(str), vd["TotalVenta"]], axis=-1),
                                  hovertemplate="<b>%{customdata[0]}</b><br>Porcentaje: %{y:.1f}%<br>Ventas: $%{customdata,.0f}<extra></extra>"))
        fig_vd.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="", yaxis_title="",
                              yaxis=dict(ticksuffix="%", range=[0, max(vd["Porcentaje"]) * 1.25]))
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


# ============================================================
# 🔮 PÁGINA 4: PREDICCIONES (VISTA EJECUTIVA - SIN MÉTRICAS TÉCNICAS)
# ============================================================
elif pagina == "🔮 Predicciones":

    st.markdown('<p class="section-title">🔮 Predicción del Próximo Mes con Machine Learning</p>', unsafe_allow_html=True)
    st.caption("⚙️ Modelo: Regresión Lineal (scikit-learn) | Entrenado con los últimos 12 meses de datos históricos")

    # Predecir ganancia y ventas
    pred_ganancia = predecir_metrica_proximo_mes(df_f, metrica="Ganancia")
    pred_ventas = predecir_metrica_proximo_mes(df_f, metrica="TotalVenta")

    if pred_ganancia is None:
        st.warning("⚠️ Se necesitan al menos 3 meses de datos para generar predicciones.")
    else:
        mes_pred = formatear_mes_es(pred_ganancia["fecha_futura"])

        # === FILA 1: 3 TARJETAS PRINCIPALES ===
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.markdown(f"""
            <div class="pred-card">
                <p class="pred-title">🔮 Ganancia estimada</p>
                <p class="pred-title" style="color:#999;">{mes_pred}</p>
                <p class="pred-value">${pred_ganancia['prediccion']:,.0f}</p>
                <p class="pred-subtitle">📉 Mín: ${pred_ganancia['rango_min']:,.0f} | 📈 Máx: ${pred_ganancia['rango_max']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            variacion = ((pred_ganancia['prediccion'] - pred_ganancia['ultimo_valor']) / pred_ganancia['ultimo_valor'] * 100) if pred_ganancia['ultimo_valor'] > 0 else 0
            emoji_var = "📈" if variacion > 0 else "📉"
            color_var = "#28a745" if variacion > 0 else "#E74C3C"

            st.markdown(f"""
            <div class="pred-card" style="border-left-color:{color_var};">
                <p class="pred-title">{emoji_var} Variación vs mes anterior</p>
                <p class="pred-title" style="color:#999;">Ganancia real vs predicha</p>
                <p class="pred-value" style="color:{color_var};">{variacion:+.1f}%</p>
                <p class="pred-subtitle">Últ. real: ${pred_ganancia['ultimo_valor']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            confianza = pred_ganancia['r2'] * 100
            color_conf = "#28a745" if confianza > 70 else "#FFB84D" if confianza > 40 else "#E74C3C"
            emoji_conf = "✅" if confianza > 70 else "⚠️" if confianza > 40 else "❌"
            texto_conf = "Alta" if confianza > 70 else "Media" if confianza > 40 else "Baja"

            st.markdown(f"""
            <div class="pred-card" style="border-left-color:{color_conf};">
                <p class="pred-title">{emoji_conf} Confianza del modelo</p>
                <p class="pred-title" style="color:#999;">R² Score</p>
                <p class="pred-value" style="color:{color_conf};">{confianza:.1f}%</p>
                <p class="pred-subtitle">Nivel: {texto_conf}</p>
            </div>
            """, unsafe_allow_html=True)

        # === FILA 2: GRÁFICO PRINCIPAL A TODO EL ANCHO ===
        st.markdown('<p class="section-title">📈 Ganancia Histórica + Proyección</p>', unsafe_allow_html=True)

        df_hist = pred_ganancia['df_historico']
        fig_pred = go.Figure()

        # Histórico
        fig_pred.add_trace(go.Scatter(
            x=df_hist["Fecha"], y=df_hist["Valor"],
            name="Histórico", mode="lines+markers",
            line=dict(color="#1f4e79", width=3, shape="spline"),
            marker=dict(size=8),
            fill="tozeroy", fillcolor="rgba(31,78,121,0.2)",
            hovertemplate="<b>%{x|%b %Y}</b><br>Ganancia real: $%{y:,.0f}<extra></extra>"
        ))

        # Banda de rango de confianza
        fig_pred.add_trace(go.Scatter(
            x=[df_hist["Fecha"].iloc[-1], pred_ganancia["fecha_futura"]],
            y=[df_hist["Valor"].iloc[-1], pred_ganancia["rango_max"]],
            mode="lines", line=dict(color="rgba(155,89,182,0)", width=0),
            showlegend=False, hoverinfo="skip"
        ))
        fig_pred.add_trace(go.Scatter(
            x=[df_hist["Fecha"].iloc[-1], pred_ganancia["fecha_futura"]],
            y=[df_hist["Valor"].iloc[-1], pred_ganancia["rango_min"]],
            mode="lines", line=dict(color="rgba(155,89,182,0)", width=0),
            fill="tonexty", fillcolor="rgba(155,89,182,0.15)",
            name="Rango de confianza", hoverinfo="skip"
        ))

        # Línea de predicción
        fig_pred.add_trace(go.Scatter(
            x=[df_hist["Fecha"].iloc[-1], pred_ganancia["fecha_futura"]],
            y=[df_hist["Valor"].iloc[-1], pred_ganancia["prediccion"]],
            name="Predicción", mode="lines+markers",
            line=dict(color="#9B59B6", width=3, dash="dash"),
            marker=dict(size=14, symbol="star", color="#9B59B6"),
            hovertemplate="<b>%{x|%b %Y}</b><br>Predicción: $%{y:,.0f}<extra></extra>"
        ))

        fig_pred.update_layout(
            height=310, hovermode="x unified",
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="right", x=1),
            xaxis_title="", yaxis_title="Ganancia ($)"
        )
        st.plotly_chart(fig_pred, use_container_width=True)

        # === FILA 3: PREDICCIÓN DE VENTAS (COMPLEMENTO) ===
        if pred_ventas is not None:
            st.markdown('<p class="section-title">💰 Complemento: Predicción de Ventas Totales</p>', unsafe_allow_html=True)

            colv1, colv2, colv3 = st.columns([1, 1, 2])

            with colv1:
                st.markdown(f"""
                <div class="pred-card">
                    <p class="pred-title">💰 Ventas estimadas</p>
                    <p class="pred-title" style="color:#999;">{mes_pred}</p>
                    <p class="pred-value">${pred_ventas['prediccion']:,.0f}</p>
                    <p class="pred-subtitle">Rango: ${pred_ventas['rango_min']:,.0f} - ${pred_ventas['rango_max']:,.0f}</p>
                </div>
                """, unsafe_allow_html=True)

            with colv2:
                margen_esperado = (pred_ganancia['prediccion'] / pred_ventas['prediccion'] * 100) if pred_ventas['prediccion'] > 0 else 0
                st.markdown(f"""
                <div class="pred-card" style="border-left-color:#28a745;">
                    <p class="pred-title">💎 Margen esperado</p>
                    <p class="pred-title" style="color:#999;">Ganancia / Ventas</p>
                    <p class="pred-value" style="color:#28a745;">{margen_esperado:.1f}%</p>
                    <p class="pred-subtitle">Rentabilidad proyectada</p>
                </div>
                """, unsafe_allow_html=True)

            with colv3:
                tendencia_txt = "creciente 📈" if pred_ganancia['coef_tendencia'] > 0 else "decreciente 📉" if pred_ganancia['coef_tendencia'] < 0 else "estable ➡️"
                conf_txt = "muy confiable" if confianza > 70 else "moderadamente confiable" if confianza > 40 else "de baja confianza"

                if variacion > 5:
                    recomendacion = "🚀 **Aumento fuerte**: Prepararse para mayor demanda (stock, personal)."
                elif variacion > 0:
                    recomendacion = "✅ **Crecimiento moderado**: Continuar con la estrategia actual."
                elif variacion > -5:
                    recomendacion = "⚠️ **Descenso leve**: Revisar campañas y promociones."
                else:
                    recomendacion = "🚨 **Alerta**: Descenso significativo. Analizar causas urgentemente."

                st.markdown(f"""
                <div class="insight-box">
                    <p class="insight-title">💡 Insights automáticos</p>
                    <p class="insight-text">📊 La tendencia histórica es <b>{tendencia_txt}</b> con un cambio promedio de <b>${abs(pred_ganancia['coef_tendencia']):,.0f}/mes</b>.</p>
                    <p class="insight-text">🎯 El modelo es <b>{conf_txt}</b> (R² = {confianza:.1f}%).</p>
                    <p class="insight-text">{recomendacion}</p>
                </div>
                """, unsafe_allow_html=True)

        # === INFORMACIÓN DEL MODELO (EXPANDIBLE) ===
        with st.expander("ℹ️ Sobre el modelo predictivo"):
            st.markdown("""
            ### 🔮 Modelo: Regresión Lineal (scikit-learn)

            **Entrada:** Últimos 12 meses de datos históricos de Ganancia y Ventas.

            **Cómo funciona:**
            1. Se agrupan las ventas/ganancias por mes.
            2. Se ajusta una línea de tendencia usando `LinearRegression`.
            3. Se proyecta el siguiente punto en el tiempo (próximo mes).
            4. Se calcula un rango de confianza usando ± 1 desviación estándar.

            **Métricas del modelo:**
            - **R² Score**: Qué tan bien explica el modelo los datos (0-100%). Mayor = mejor.
            - **MAE (Mean Absolute Error)**: Error promedio de las predicciones sobre datos históricos.
            - **Coeficiente de tendencia**: Cambio promedio por mes ($/mes).

            **Interpretación de la confianza:**
            - 🟢 R² > 70%: Modelo muy confiable, tendencia clara.
            - 🟡 R² 40-70%: Confianza media, hay variabilidad.
            - 🔴 R² < 40%: Baja confianza, considerar factores externos (estacionalidad, eventos).

            **Casos de uso:**
            - Planificación financiera y de compras.
            - Ajuste de objetivos comerciales mensuales.
            - Detección temprana de tendencias negativas.
            """)