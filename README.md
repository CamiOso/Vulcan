# Proyecto Vulcano (MVP)

Primer paso para construir un software tipo Vulcan en Python.

## Objetivo de esta fase

- Cargar sondajes desde CSV.
- Visualizar puntos 3D.
- Dibujar trazas de barrenos por `hole_id`.
- Colorear por variable (por ejemplo, ley de Au).

## Estructura

- `src/proyectovulcano/app.py`: entrada CLI.
- `src/proyectovulcano/io.py`: carga y validacion de datos.
- `src/proyectovulcano/viewer.py`: visualizacion 3D con PyVista.
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

## Formato CSV esperado

Columnas obligatorias:

- `hole_id`
- `x`
- `y`
- `z`

Columnas opcionales:

- Cualquier variable numerica para colorear (ejemplo: `au`, `density`).

## Siguiente paso recomendado

Implementar compositado por intervalo y primer modelo de bloques (IDW).
