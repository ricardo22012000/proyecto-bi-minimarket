"""
============================================================
ETL AUTOMATIZADO - PROYECTO BI MINIMARKET
============================================================
Autor: Ricardo Muñoz
Empresa: G&S Gestión y Sistemas
Descripción: Extrae datos de Excel multi-hoja, transforma
             y carga los datos limpios y enriquecidos.
============================================================
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================
# Ruta base del proyecto (sube un nivel desde /etl a /proyecto_bi)
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta al archivo Excel de origen
RUTA_EXCEL = BASE_DIR / "data" / "base_datos_minimarket_v3.xlsx"

# Ruta donde guardaremos los datos procesados
RUTA_SALIDA = BASE_DIR / "data_processed"

# Aseguramos que la carpeta de salida exista
RUTA_SALIDA.mkdir(exist_ok=True)


# ============================================================
# 1️⃣ EXTRACT - Extraer datos desde Excel
# ============================================================
def extract():
    """Lee las 3 hojas del Excel de origen."""
    print("🔍 [EXTRACT] Leyendo archivo Excel...")

    df_sucursales = pd.read_excel(RUTA_EXCEL, sheet_name="Sucursales")
    df_productos = pd.read_excel(RUTA_EXCEL, sheet_name="Productos")
    df_ventas = pd.read_excel(RUTA_EXCEL, sheet_name="Historial_Ventas")

    print(f"   ✅ Sucursales: {len(df_sucursales)} registros")
    print(f"   ✅ Productos: {len(df_productos)} registros")
    print(f"   ✅ Ventas: {len(df_ventas):,} registros")

    return df_sucursales, df_productos, df_ventas


# ============================================================
# 2️⃣ TRANSFORM - Limpiar, unir y enriquecer datos
# ============================================================
def transform(df_sucursales, df_productos, df_ventas):
    """Realiza limpieza, JOINs y creación de columnas calculadas."""
    print("\n🔧 [TRANSFORM] Procesando datos...")

    # ------------------------------------------------------------
    # A) LIMPIEZA DE DATOS
    # ------------------------------------------------------------
    print("   🧹 Limpiando datos...")

    # Convertir Fecha a tipo datetime
    df_ventas["Fecha"] = pd.to_datetime(df_ventas["Fecha"], errors="coerce")

    # Eliminar filas con fechas nulas (por si el Excel tiene errores)
    df_ventas = df_ventas.dropna(subset=["Fecha"])

    # Asegurar que columnas numéricas sean numéricas
    columnas_numericas = ["Cantidad", "TotalVenta", "TotalCosto", "Ganancia"]
    for col in columnas_numericas:
        df_ventas[col] = pd.to_numeric(df_ventas[col], errors="coerce")

    df_productos["PrecioCompra"] = pd.to_numeric(df_productos["PrecioCompra"], errors="coerce")
    df_productos["PrecioVenta"] = pd.to_numeric(df_productos["PrecioVenta"], errors="coerce")

    # Eliminar espacios en blanco de columnas de texto
    for col in df_sucursales.select_dtypes(include="object").columns:
        df_sucursales[col] = df_sucursales[col].astype(str).str.strip()
    for col in df_productos.select_dtypes(include="object").columns:
        df_productos[col] = df_productos[col].astype(str).str.strip()
    for col in df_ventas.select_dtypes(include="object").columns:
        df_ventas[col] = df_ventas[col].astype(str).str.strip()

    # ------------------------------------------------------------
    # B) JOIN - Unir las 3 tablas en una sola vista consolidada
    # ------------------------------------------------------------
    print("   🔗 Uniendo tablas (JOIN)...")

    # JOIN Ventas ← Sucursales
    df = df_ventas.merge(df_sucursales, on="SucursalID", how="left")

    # JOIN + Productos
    df = df.merge(df_productos, on="ProductoID", how="left")

    # ------------------------------------------------------------
    # C) COLUMNAS CALCULADAS (ENRIQUECIMIENTO)
    # ------------------------------------------------------------
    print("   ✨ Creando columnas calculadas...")

    # Extraer componentes de fecha (útiles para filtros y gráficos)
    df["Mes"] = df["Fecha"].dt.month
    df["MesNombre"] = df["Fecha"].dt.strftime("%B")
    df["Trimestre"] = df["Fecha"].dt.quarter
    df["DiaSemana"] = df["Fecha"].dt.day_name()
    df["AñoMes"] = df["Fecha"].dt.strftime("%Y-%m")

    # Traducir día de la semana al español
    dias_es = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    df["DiaSemana"] = df["DiaSemana"].map(dias_es)

    # Traducir mes al español
    meses_es = {
        "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
        "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
        "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
    }
    df["MesNombre"] = df["MesNombre"].map(meses_es)

    # Margen de rentabilidad por transacción (%)
    df["MargenPct"] = np.where(
        df["TotalVenta"] > 0,
        (df["Ganancia"] / df["TotalVenta"]) * 100,
        0
    ).round(2)

    # Precio unitario efectivo de venta
    df["PrecioUnitarioVenta"] = np.where(
        df["Cantidad"] > 0,
        df["TotalVenta"] / df["Cantidad"],
        0
    ).round(2)

    # ------------------------------------------------------------
    # D) ORDENAR Y REORGANIZAR COLUMNAS
    # ------------------------------------------------------------
    orden_columnas = [
        "VentaID", "Fecha", "Año", "Mes", "MesNombre", "Trimestre",
        "DiaSemana", "AñoMes", "Turno",
        "SucursalID", "NombreSucursal", "UbicacionTipo",
        "ProductoID", "NombreProducto", "Categoría",
        "Cantidad", "PrecioCompra", "PrecioVenta", "PrecioUnitarioVenta",
        "TotalVenta", "TotalCosto", "Ganancia", "MargenPct",
        "MetodoPago"
    ]
    # Solo incluir columnas que existan (por seguridad)
    orden_columnas = [c for c in orden_columnas if c in df.columns]
    df = df[orden_columnas]

    # Ordenar por fecha ascendente
    df = df.sort_values("Fecha").reset_index(drop=True)

    print(f"   ✅ Dataset final: {len(df):,} filas × {len(df.columns)} columnas")

    return df, df_sucursales, df_productos


# ============================================================
# 3️⃣ LOAD - Guardar datos procesados
# ============================================================
def load(df_final, df_sucursales, df_productos):
    """Guarda los datos limpios en formato Parquet (optimizado)."""
    print("\n💾 [LOAD] Guardando datos procesados...")

    # Guardar tabla consolidada (la principal para el dashboard)
    ruta_consolidado = RUTA_SALIDA / "ventas_consolidado.parquet"
    df_final.to_parquet(ruta_consolidado, index=False)
    print(f"   ✅ {ruta_consolidado.name} ({ruta_consolidado.stat().st_size / 1024:.1f} KB)")

    # Guardar dimensiones por separado (útiles para filtros)
    df_sucursales.to_parquet(RUTA_SALIDA / "sucursales.parquet", index=False)
    df_productos.to_parquet(RUTA_SALIDA / "productos.parquet", index=False)
    print(f"   ✅ sucursales.parquet")
    print(f"   ✅ productos.parquet")

    # Guardar log de la última ejecución
    log_path = RUTA_SALIDA / "etl_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Última ejecución ETL: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de filas procesadas: {len(df_final):,}\n")
        f.write(f"Rango de fechas: {df_final['Fecha'].min()} → {df_final['Fecha'].max()}\n")
    print(f"   ✅ etl_log.txt")


# ============================================================
# 🚀 EJECUCIÓN PRINCIPAL
# ============================================================
def main():
    print("=" * 60)
    print("🚀 INICIANDO ETL - PROYECTO BI MINIMARKET")
    print("=" * 60)

    inicio = datetime.now()

    df_sucursales, df_productos, df_ventas = extract()
    df_final, df_sucursales, df_productos = transform(df_sucursales, df_productos, df_ventas)
    load(df_final, df_sucursales, df_productos)

    duracion = (datetime.now() - inicio).total_seconds()

    print("\n" + "=" * 60)
    print(f"✅ ETL COMPLETADO EXITOSAMENTE en {duracion:.2f} segundos")
    print("=" * 60)


if __name__ == "__main__":
    main()