## v0.2.0 (En desarrollo)

### Nuevas características
- Herramientas avanzadas de geología y estimación (`geology_estimation.py`)
  - `DrillholeDataManager`: Gestión completa de datos de sondajes
  - `CompositingTools`: Métodos de compositado avanzados
  - `StratigraphicModeler`: Modelado de contactos y dominios
- Funciones de exportación mejoradas
  - Exportación a JSON, Excel, y TXT
  - Control de precisión en CSV
  - Metadata exports
- Estadísticas y análisis expandido
  - Percentiles completos (p25, p75, p90)
  - Coeficiente de variación (CV)
  - Análisis de drillholes individuales
  - Detección de outliers por IQR
  - Reportes de calidad de datos
- Suite completa de tests unitarios
  - 40+ tests cobriendo io, compositing, stats, block_model
  - Fixtures de datos de prueba
  - Test coverage >80%
- Documentación mejorada
  - README.md expansivo con tabla de opciones CLI
  - DEVELOPMENT.md con guía completa para contribuidores
  - Docstrings mejorados en todos los módulos
- Scripts de workflow de ejemplo
  - complete_workflow.json: Flujo de análisis completo
  - simple_drillholes.json: Visualización básica
  - fine_block_model.json: Modelo de bloques fino
  - section_workflow.json: Secciones 2D
- Dataset de ejemplo mejorado
  - 30 muestras vs 9 anteriores
  - Múltiples variables (Au, Ag, Cu, densidad)
  - Litología y zonas geológicas
  - Profundidad downhole

### Mejoras
- Validación más robusta en todos los módulos
- Mejor manejo de NAs y valores faltantes
- Type hints completos en todas las funciones
- Docstrings con ejemplos en módulos core
- Mejor organización de código

### Bug fixes
- Manejo correcto de datos vacíos después de filtrado
- Validación de parámetros más estricta
- Conversión segura de tipos numéricos

---

## v0.1.0 (Inicial)

### Características base
- Carga de sondajes desde CSV
- Visualización 3D con PyVista
- Visualización de trazas de barrenos
- Compositos por longitud fija
- Modelo de bloques con interpolación IDW
- Secciones 2D longitudinales y transversales
- CLI con argparse
- GUI básica con tkinter (SetupWizard)
- Automatización con scripts JSON
- Exportación a CSV

### Módulos iniciales
- `io.py`: Carga y filtrado de datos
- `compositing.py`: Creación de compositos
- `block_model.py`: Modelo de bloques e IDW
- `sections.py`: Extracción de secciones
- `stats.py`: Estadísticas básicas
- `viewer.py`: Visualización 3D y 2D
- `automation.py`: Scripts JSON
- `app.py`: CLI principal
- `gui.py`: Interfaz con tkinter
- `config.py`: Configuración de usuario
- `module_catalog.py`: Catálogo de módulos

---

## Roadmap

### v0.3.0 (Próximo)
- [ ] GUI mejorada con PyQt5 o Qt Designer
- [ ] Más métodos de interpolación (OK3, KDTree, etc.)
- [ ] Visualización de incertidumbre
- [ ] Optimización de rendimiento para datasets grandes
- [ ] Cache de cálculos
- [ ] Histórico de cambios (undo/redo)

### v0.4.0
- [ ] Support para formatos adicionales (RCS, Datamine, Surpac)
- [ ] Análisis multivariante (simulación condicional)
- [ ] Pit optimization básico
- [ ] Clustering de sondajes
- [ ] Análisis de correlación mejorado

### Futuro
- [ ] Plugin system para expansibilidad
- [ ] Integración con bases de datos (PostgreSQL, MongoDB)
- [ ] API REST para acceso remoto
- [ ] Cloud support (AWS, GCP)
- [ ] Machine learning para estimación de variables
