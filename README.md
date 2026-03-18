# Proyecto Vulcano (MVP)

Primer paso para construir un software tipo Vulcan en Python.

## Objetivo de esta fase

- Cargar sondajes desde CSV.
- Visualizar puntos 3D.
- Dibujar trazas de barrenos por `hole_id`.
- Colorear por variable (por ejemplo, ley de Au).
- Generar compositos por intervalo fijo.
- Estimar un modelo de bloques regular con IDW.

## Estructura

- `src/proyectovulcano/app.py`: entrada CLI.
- `src/proyectovulcano/io.py`: carga y validacion de datos.
- `src/proyectovulcano/viewer.py`: visualizacion 3D con PyVista.
- `src/proyectovulcano/compositing.py`: compositado por longitud fija.
- `src/proyectovulcano/block_model.py`: construccion de bloques e IDW.
- `data/example_drillholes.csv`: dataset de ejemplo.

## Requisitos

Instalar dependencias:

```bash
pip install -r requirements.txt
pip install -e .
```

## Uso rapido

```bash
python -m proyectovulcano --file data/example_drillholes.csv --color-by au
```

## Interfaz principal (menus)

Puedes abrir una interfaz de escritorio para seleccionar opciones sin escribir comandos:

```bash
python -m proyectovulcano --view gui
```

Tambien puedes abrirla con un CSV inicial:

```bash
python -m proyectovulcano --view gui --file data/example_drillholes.csv
```

En la UI tienes:

- Menu Archivo: abrir CSV, usar ejemplo, salir.
- Menu Ejecutar: correr la vista seleccionada.
- Menu Ayuda: informacion de la app.
- Paneles de opciones para drillholes, blocks, section, filtros y parametros IDW.
- Gestion de variables con deteccion de columnas numericas/categoricas.
- Slider para mover section-center de forma interactiva.
- Botones de exportacion directa (composites, bloques, seccion, reporte).

## Ventanas y flujo de navegacion

1. Inicio:
- Ventana de presentacion.
- Seleccion de carpeta de datos (explorador integrado).
- Mensajes de estado de configuracion.

2. Seleccion de carpeta de datos:
- Campo de directorio de trabajo + Browse de carpetas.
- Define donde buscar y guardar informacion de mina/proyecto.

3. Asistente inicial (primer uso, 4 pasos):
- Bienvenida.
- Configuracion grafica (resolucion y estilo visual).
- Seleccion de unidades (metros/pies).
- Confirmacion final.

4. Entorno de diseno/modelado:
- Se abre con doble clic en ENVISAJE desde la ventana de inicio.
- Incluye panel de modulos de Vulcan activables/desactivables.
- Incluye visualizacion 3D/2D, modelado de bloques, secciones y exportaciones.

5. Ventana de mensajes/notificaciones:
- Errores de seleccion y confirmaciones de acciones.
- Log de ejecucion de vistas y scripts.

## Catalogo de modulos en la GUI

- Geology & Estimation
- Open Pit Design
- Underground Design
- Multivariate & Simulation
- Open Pit Optimisation
- Scheduling Suite
- Grade Control Suite
- Geotechnical Suite
- Drillhole Optimiser
- Stope Optimiser

## Funcionalidades Principales

- Creacion de modelos de bloques: construccion de block model regular con IDW.
- Verificacion y edicion: reporte estadistico composites vs bloques y ajuste por factor de ley (`value-factor`).
- Estimacion de leyes: IDW configurable (`idw-power`, `search-radius`, `max-samples`).
- Visualizacion y manipulacion: vistas 3D de sondajes y bloques, secciones 2D, y ventana de corte en 3D.
- Automatizacion con scripts: ejecucion de flujos via JSON (`--script` o menu Scripts en GUI).
- Gestion de variables: deteccion y seleccion de variables numericas/categoricas en la UI.
- Indexado y exportacion: bloques con indices `i`, `j`, `k`, `block_id`; exportaciones a CSV/JSON/TXT.

## Automatizacion por script

Ejecutar workflow desde JSON:

```bash
python -m proyectovulcano --script scripts/example_workflow.json
```

Ejemplo listo para usar:

- `scripts/example_workflow.json`

Tambien puedes usar otro campo numerico:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --color-by density
```

Ejecutar sin trazas de barreno:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --color-by au --no-traces
```

Controlar ancho de las trazas:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --color-by au --trace-width 5
```

Visualizar block model IDW:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au
```

Visualizar seccion longitudinal desde sondajes:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view section --section-source drillholes --section-type longitudinal --section-width 25 --color-by au
```

Visualizar seccion transversal desde block model:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view section --section-source blocks --section-type transversal --section-width 20 --value-col au
```

Ver en 3D la ventana de corte antes de abrir seccion 2D:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view drillholes --color-by au --show-section-window --section-type longitudinal --section-width 25
```

Tambien aplica para bloques:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --show-section-window --section-type transversal --section-width 20
```

Filtrar por dominio geologico (ejemplo):

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --domain-col lith --domain-values mineral
```

Ajustar tamano de bloque y parametros IDW:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --composite-length 8 --block-size 8 8 4 --search-radius 30 --idw-power 2
```

Exportar compositos y bloques:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --export-composites outputs/composites.csv --export-blocks outputs/block_model.csv
```

Pipeline sin abrir ventana (ideal para validacion o CI):

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --no-show
```

Reporte estadistico composites vs bloques:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --no-show --report-stats --stats-file outputs/stats_report.txt
```

Exportar puntos de seccion a CSV:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view section --section-source blocks --section-type longitudinal --section-width 20 --no-show --export-section outputs/section_points.csv
```

## Formato CSV esperado

Columnas obligatorias:

- `hole_id`
- `x`
- `y`
- `z`

Columnas opcionales:

- Cualquier variable numerica para colorear (ejemplo: `au`, `density`).
- `depth` para ordenar muestras en compositado (si no existe, se usa geometria 3D).
- Columna categorica de dominio (ejemplo: `lith`) para filtrar con `--domain-col`.

## Siguiente paso recomendado

Agregar comparacion con produccion real y limites geologicos implicitos/explicitos.
