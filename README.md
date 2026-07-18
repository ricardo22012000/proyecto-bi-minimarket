# 🛒 Dashboard BI - Minimarket

Dashboard interactivo de Business Intelligence para análisis de ventas de un minimarket, con carga dinámica de datos, visualizaciones interactivas y modelo predictivo con Machine Learning.

**Autor:** Ricardo Muñoz  
**Empresa:** G&S Gestión y Sistemas S.A.C.  
**Fecha:** Julio 2026

---

## 🌐 Demo en vivo

👉 **https://minimarket-bi-ricardo.streamlit.app**

---

## 🎯 Características

### 📊 Análisis Descriptivo
- 5 KPIs principales (Ventas, Ganancia, Margen, Transacciones, Ticket Promedio)
- Evolución temporal con granularidad adaptativa (día/semana/mes)
- Análisis por Sucursal, Categoría y Año
- Detección automática de categoría crítica

### 🏆 Análisis por Productos
- Top 10 productos por ventas y ganancia
- Heatmap Categoría × Sucursal
- Análisis de rentabilidad

### 🕐 Patrones de Consumo
- Heatmap Día × Turno
- Distribución por turnos, días y método de pago
- Identificación de picos de venta

### 🔮 Predicciones con Machine Learning
- Predicción de ganancia del próximo mes
- Predicción complementaria de ventas totales
- Margen esperado proyectado
- Insights automáticos para gerencia
- Modelo: Regresión Lineal (scikit-learn)

### ⚙️ Panel de Administración
- Carga dinámica de Excel con validación automática
- ETL integrado (extract, transform, load)
- Actualización automática de datos sin recargar el navegador

---

## 🛠️ Stack Tecnológico

- **Python 3.14**
- **Streamlit** - Framework del dashboard
- **Pandas** - Manipulación de datos
- **Plotly** - Visualizaciones interactivas
- **Scikit-learn** - Machine Learning
- **openpyxl** - Lectura de Excel
- **PyArrow** - Formato de datos optimizado (Parquet)

---

## 📁 Estructura del proyecto