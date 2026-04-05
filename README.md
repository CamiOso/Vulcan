
# Proyecto Vulcano

Primer paso para construir un software tipo Vulcan en Python, con interfaz gráfica inspirada en Surpac.

---

## Objetivos

- ✅ Cargar sondajes desde CSV
- ✅ Visualizar puntos 3D con PyVista
- ✅ Dibujar trazas de barrenos por `hole_id`
- ✅ Colorear por variable (ejemplo: ley de Au)
- ✅ Generar compositos por intervalo fijo
- ✅ Estimar un modelo de bloques regular con IDW
- ✅ Crear secciones 2D longitudinales y transversales
- ✅ Gestión y validación de datos geológicos
- ✅ Exportación a múltiples formatos (CSV, JSON, Excel)
- ✅ Automatización con scripts JSON

---

## Estructura del Proyecto

```
src/proyectovulcano/
├── __init__.py                  # Inicialización del paquete
├── __main__.py                  # Punto de entrada CLI
├── app.py                       # CLI principal y configuración de argumentos
├── gui.py                       # Interfaz tkinter (asistente y panel principal)
├── gui_mockup.py                # Mockup de interfaz avanzada
├── io.py                        # Carga, validación y exportación de datos
├── viewer.py                    # Visualización 3D con PyVista y 2D con matplotlib
├── compositing.py               # Creación de compositos por longitud fija
├── block_model.py               # Construcción de bloques e interpolación IDW
├── sections.py                  # Extracción de secciones 2D
├── stats.py                     # Estadísticas y análisis comparativo
├── geology_estimation.py        # Herramientas de validación y modelado geológico
├── automation.py                # Ejecución de scripts JSON
├── config.py                    # Gestión de configuración de usuario
├── module_catalog.py            # Catálogo de módulos disponibles
└── data/example_drillholes.csv  # Dataset de ejemplo
```

---

## Instalación

### Requisitos
- Python 3.9+
- pip o conda

### Instalación desde repositorio

```bash
# Clonar repositorio
git clone <repo_url>
cd ProyectoVulcano

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar en modo desarrollo
pip install -e .
```

---

## Uso

### Interfaz Gráfica (Recomendado)

```bash
python -m proyectovulcano --view gui
```

### Línea de Comandos (CLI)

#### Ver sondajes 3D
```bash
python -m proyectovulcano \
  --file data/example_drillholes.csv \
  --view drillholes \
  --color-by au \
  --show-traces
```

#### Generar modelo de bloques
```bash
python -m proyectovulcano \
  --file data/example_drillholes.csv \
  --view blocks \
  --value-col au \
  --composite-length 10 \
  --block-size 10 10 5 \
  --idw-power 2.0 \
  --export-composites outputs/composites.csv \
  --export-blocks outputs/blocks.csv \
  --report-stats
```

#### Ver sección 2D
```bash
python -m proyectovulcano \
  --file data/example_drillholes.csv \
  --view section \
  --section-type longitudinal \
  --section-width 30 \
  --color-by au
```

#### Ejecutar script de automatización
```bash
python -m proyectovulcano --script scripts/example_workflow.json
```

### Opciones principales CLI

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--file` | Ruta al CSV de sondajes | `data/example_drillholes.csv` |
| `--view` | Tipo de visualización | `drillholes`, `blocks`, `section`, `gui` |
| `--color-by` | Columna para colorear puntos | `au`, `ag` |
| `--value-col` | Columna a compositar/estimar | `au`, `cu` |
| `--composite-length` | Longitud de composito (m) | `10.0` |
| `--block-size` | Tamaño de bloque X Y Z | `10 10 5` |
| `--idw-power` | Potencia de ponderación IDW | `2.0` |
| `--search-radius` | Radio de búsqueda IDW (m) | `25.0` |
| `--max-samples` | Máximo de compositos por bloque | `12` |
| `--domain-col` | Columna de dominio para filtrar | `lith`, `zone` |
| `--domain-values` | Valores de dominio permitidos | `granite schist` |
| `--export-composites` | Exportar compositos a CSV | `outputs/composites.csv` |
| `--export-blocks` | Exportar bloques a CSV | `outputs/blocks.csv` |
| `--export-section` | Exportar sección a CSV | `outputs/section.csv` |
| `--report-stats` | Imprimir estadísticas | _(flag)_ |
| `--stats-file` | Guardar estadísticas | `outputs/stats.txt` |

---

## Interfaz Gráfica (GUI)

La interfaz gráfica incluye:

### Pestañas principales

1. **Datos & Sondajes:**
   - Cargar archivo CSV
   - Visualizar sondajes 3D
   - Filtros por dominio
   - Opciones de renderizado

2. **Compositos:**
   - Configurar longitud de composito
   - Visualizar distribución
   - Ver estadísticas

3. **Modelo de Bloques:**
   - Configurar tamaño y padding
   - Parámetros de interpolación IDW
   - Exportar modelo

4. **Secciones 2D:**
   - Tipo de sección (longitudinal/transversal)
   - Centro y ancho de ventana
   - Coloración

5. **Estadísticas:**
   - Comparación compositos vs bloques
   - Análisis por barreno
   - Detección de outliers

---

## Formatos de datos

### CSV de entrada (Sondajes)

Columnas requeridas:
- `hole_id`: Identificador único de barreno (string)
- `x`, `y`, `z`: Coordenadas (float)

Columnas opcionales:
- `depth`: Profundidad downhole (float)
- `length`: Longitud de muestra (float)
- `au`, `ag`, `cu`: Leyes (float)
- `lith`: Litología (string)
- `zone`: Zona geológica (string)
- Cualquier otra información relevante

Ejemplo:
```
hole_id,x,y,z,depth,length,au,ag,lith
AH001,1000,2000,100,0,2,0.35,5.2,granite
AH001,1000,2000,98,2,2,0.42,4.8,granite
AH001,1000,2000,96,4,2,0.28,6.1,schist
```

### Exportaciones

- **CSV**: Todos los DataFrames (sondajes, compositos, bloques, secciones)
- **JSON**: Metadata, configuración, datos
- **Excel**: Reportes multi-hoja (requiere openpyxl)
- **TXT**: Reportes formateados

---

## Scripts de Automatización

Los scripts JSON permiten crear flujos de trabajo automáticos:

```json
{
  "file": "data/example_drillholes.csv",
  "view": "blocks",
  "value_col": "au",
  "composite_length": 10.0,
  "block_size": [10.0, 10.0, 5.0],
  "idw_power": 2.0,
  "search_radius": 25.0,
  "max_samples": 12,
  "export_composites": "outputs/composites.csv",
  "export_blocks": "outputs/blocks.csv",
  "report_stats": true,
  "stats_file": "outputs/stats.txt",
  "no_show": false
}
```

Ver `scripts/example_workflow.json` para más ejemplos.

---

## Desarrollo

### Instalar en modo desarrollo

```bash
pip install -e .
```

### Ejecutar tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=proyectovulcano

# Tests específicos
pytest tests/test_compositing.py -v
```

### Estructura de tests

```
tests/
├── test_io.py           # Tests de carga/exportación
├── test_compositing.py  # Tests de compositado
├── test_stats.py        # Tests de estadísticas
└── test_block_model.py  # Tests de modelo de bloques
```

### Agregar nuevas funcionalidades

1. Crear función en módulo correspondiente
2. Agregar docstring con ejemplos
3. Crear tests unitarios
4. Actualizar CLI y/o GUI si es necesario

---

## Módulos principales

### `io.py` - Entrada/Salida de datos
- `load_drillholes_csv()`: Cargar y validar CSV
- `filter_by_domain()`: Filtrar por categoría
- `export_dataframe_csv/json()`: Exportar datos
- `list_numeric_columns()`: Listar variables numéricas

### `compositing.py` - Creación de compositos
- `composite_drillholes()`: Crear compositos por longitud
- Preserva información de barreno y posición

### `block_model.py` - Modelo de bloques
- `build_regular_block_model()`: Construir malla regular
- Interpolación IDW configurable
- Estadísticas de interpolación

### `sections.py` - Secciones 2D
- `extract_section()`: Extraer sección longitudinal/transversal
- Parámetros de centro y ancho variables

### `stats.py` - Análisis estadístico
- `compare_composites_vs_blocks()`: Validación de estimación
- `get_drillhole_statistics()`: Stats por barreno
- `detect_outliers_iqr()`: Detección de anómalos
- `get_data_quality_report()`: Calidad de datos

### `viewer.py` - Visualización
- `show_drillholes()`: 3D con PyVista
- `show_block_model()`: 3D de bloques
- `show_section_2d()`: 2D con matplotlib
- Coloración por variable
- Transparencias y estilos

### `geology_estimation.py` - Herramientas geológicas
- `DrillholeDataManager`: Gestión de datos
- `CompositingTools`: Métodos de compositado
- `StratigraphicModeler`: Modelado estratigráfico

### `automation.py` - Scripts JSON
- `run_script_file()`: Ejecutar flujo desde JSON
- `run_script_config()`: Ejecutar desde dict

---

## Configuración

La aplicación mantiene configuración de usuario en:
- `config.py`: Gestión de preferencias
- Resolución de pantalla, unidades, estilos
- Cargada automáticamente al iniciar

---

## Licencia

MIT License

---

## Autor

Proyecto desarrollado en Python con librerías científicas (pandas, numpy, pyvista).

## Ejemplos de Uso

### CLI

```bash
python -m proyectovulcano --file data/example_drillholes.csv --color-by au
```

### GUI

```bash
python -m proyectovulcano --view gui
python -m proyectovulcano --view gui --file data/example_drillholes.csv
```

En la UI tienes:
- Menú Archivo: abrir CSV, usar ejemplo, salir
- Menú Ejecutar: correr la vista seleccionada
- Menú Ayuda: información de la app
- Paneles de opciones para drillholes, blocks, section, filtros y parámetros IDW
- Gestión de variables con detección de columnas numéricas/categóricas
- Slider para mover section-center de forma interactiva
- Botones de exportación directa (composites, bloques, sección, reporte)

---


## Automatización por Script

Ejecutar workflow desde JSON:

```bash
python -m proyectovulcano --script scripts/example_workflow.json
```

---


- `scripts/example_workflow.json`

Otros ejemplos:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --color-by density
python -m proyectovulcano --file data/example_drillholes.csv --color-by au --no-traces
python -m proyectovulcano --file data/example_drillholes.csv --color-by au --trace-width 5
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au
python -m proyectovulcano --file data/example_drillholes.csv --view section --section-source drillholes --section-type longitudinal --section-width 25 --color-by au
python -m proyectovulcano --file data/example_drillholes.csv --view section --section-source blocks --section-type transversal --section-width 20 --value-col au
python -m proyectovulcano --file data/example_drillholes.csv --view drillholes --color-by au --show-section-window --section-type longitudinal --section-width 25
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --show-section-window --section-type transversal --section-width 20
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --domain-col lith --domain-values mineral
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --composite-length 8 --block-size 8 8 4 --search-radius 30 --idw-power 2
```

---


## Exportación y Reportes

Exportar compositos y bloques:
```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --export-composites outputs/composites.csv --export-blocks outputs/block_model.csv
```

Pipeline sin abrir ventana (ideal para validación o CI):
```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --no-show
```

Reporte estadístico composites vs bloques:
```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --no-show --report-stats --stats-file outputs/stats_report.txt
```

Exportar puntos de sección a CSV:
```bash
python -m proyectovulcano --file data/example_drillholes.csv --view section --section-source blocks --section-type longitudinal --section-width 20 --no-show --export-section outputs/section_points.csv
```

---

## Formato CSV esperado

Columnas obligatorias:
- `hole_id`
- `x`
- `y`
- `z`

Columnas opcionales:
- Cualquier variable numérica para colorear (ejemplo: `au`, `density`)
- `depth` para ordenar muestras en compositado (si no existe, se usa geometría 3D)
- Columna categórica de dominio (ejemplo: `lith`) para filtrar con `--domain-col`

---

## Siguiente paso recomendado

Agregar comparación con producción real y límites geológicos implícitos/explicitos.
