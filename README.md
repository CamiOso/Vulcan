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

Ajustar tamano de bloque y parametros IDW:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --composite-length 8 --block-size 8 8 4 --search-radius 30 --idw-power 2
```

Exportar compositos y bloques:

```bash
python -m proyectovulcano --file data/example_drillholes.csv --view blocks --value-col au --export-composites outputs/composites.csv --export-blocks outputs/block_model.csv
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

## Siguiente paso recomendado

Agregar secciones, filtros por dominio y validacion estadistica del modelo.
