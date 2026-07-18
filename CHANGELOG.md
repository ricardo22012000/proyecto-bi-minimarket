# 📝 CHANGELOG - Dashboard BI Minimarket

Documentación de la evolución del proyecto por versiones.

---

## 🆕 v2.0 - 2026-07-13

### 🎯 Objetivo
Aplicar recomendaciones del analista para mejorar UX y análisis.

### ✨ Nuevas funcionalidades
- **Navegación multi-página**: 3 vistas independientes
  - 📊 Vista General
  - 🏆 Productos y Sucursales
  - 🕐 Patrones de Consumo
- **Mapas de calor (Heatmaps)**:
  - Categoría × Sucursal (Página 2)
  - Día de semana × Turno (Página 3)
- **Filtros con fallback**: si están vacíos, muestran todos los datos
- **Placeholders informativos** en los filtros
- **KPIs visibles en todas las páginas**

### 🔧 Mejoras
- Gráfico de líneas con puntos → reemplazado por **gráfico de área apilada**
- Reorganización de secciones para reducir scroll
- CSS mejorado con badges de página

### 🐛 Correcciones
- Fix: Filtro multiselect vacío ya no rompe la vista

### 📁 Archivo
`versions/app_v2.py`

### ▶️ Ejecución
```powershell
streamlit run versions/app_v2.py