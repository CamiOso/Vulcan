# Proyecto Vulcano (MVP)

Primer paso para construir un software tipo Vulcan en Python.

## Objetivo de esta fase

- Cargar sondajes desde CSV.
- Visualizar puntos 3D.
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

## Formato CSV esperado

Columnas obligatorias:

- `hole_id`
- `x`
- `y`
- `z`

Columnas opcionales:

- Cualquier variable numerica para colorear (ejemplo: `au`, `density`).

## Siguiente paso recomendado

Implementar compositado por intervalo y traza de barrenos (lineas por `hole_id`).
