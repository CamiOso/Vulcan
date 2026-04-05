# Guía de Desarrollo - Proyecto Vulcano

Documentación para contribuidores y desarrolladores.

---

## Setup de Desarrollo

### Clonar y configurar

```bash
git clone <repo_url>
cd ProyectoVulcano

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar en modo editable
pip install -e ".[dev]"

# Instalar herramientas de desarrollo
pip install pytest pytest-cov black flake8 mypy
```

### requirements.txt (actualizado)

```
numpy>=1.26
pandas>=2.2
pyvista>=0.44
vtk>=9.3
pytest>=7.0
pytest-cov>=4.0
```

---

## Estructura de módulos

### Core

**`io.py`** - Entrada/salida de datos
- Validación de columnas requeridas
- Filtrado por dominio
- Exportación múltiples formatos
- Funciones públicas bien documentadas

**`compositing.py`** - Compositos por longitud fija
- Cálculo de profundidad downhole
- Agrupamiento por intervalo
- Preservación de metadatos

**`block_model.py`** - Estimación IDW
- Construcción de malla regular
- Interpolación por distancia inversa
- Control de radio de búsqueda y muestras

**`sections.py`** - Extracción de secciones 2D
- Soporte longitudinal y transversal
- Parámetros de centro y ancho
- Metadatos de sección

**`stats.py`** - Análisis estadístico
- Cuantiles y distribuciones
- Comparación compositos vs bloques
- Detección de outliers
- Reportes de calidad

### Geológicas

**`geology_estimation.py`** - Herramientas avanzadas
- `DrillholeDataManager`: Gestión de datos
- `CompositingTools`: Métodos compositado
- `StratigraphicModeler`: Modelado de contactos

### Visualización

**`viewer.py`** - Renderizado 3D y 2D
- PyVista para 3D
- Matplotlib para 2D
- Coloración por variable
- Ventanas de sección

### Interfaz

**`gui.py`** - Tkinter GUI
- Asistente de configuración
- Interfaz principal multi-pestañas
- Gestión de estado

**`gui_mockup.py`** - Interfaz avanzada (PyQt5)
- Mockup inspirado en Surpac
- No implementado completamente

### Automatización

**`automation.py`** - Scripts JSON
- Carga de configuración
- Ejecución de flujos
- Logging de operaciones

**`app.py`** - CLI principal
- Parser de argumentos
- Orquestación de pipeline
- Puntos de entrada

---

## Patrones de código

### Validación de entrada

```python
# Siempre validar en la entrada de función
def composite_drillholes(
    df: pd.DataFrame,
    value_col: str,
    composite_length: float = 10.0,
) -> pd.DataFrame:
    if composite_length <= 0:
        raise ValueError("composite_length must be > 0")
    if value_col not in df.columns:
        raise ValueError(f"Column not found for compositing: {value_col}")
    
    # ... resto de lógica
```

### Tipo de datos transparentes

```python
# Usar type hints completos
def filter_by_domain(
    df: pd.DataFrame,
    domain_col: str | None = None,
    domain_values: list[str] | None = None,
) -> pd.DataFrame:
    """Filter dataframe by categorical domain values."""
```

### Handling de NAs

```python
# Limpiar NAs de forma explícita
valid = df[["x", "y", "z", value_col]].copy()
valid[value_col] = pd.to_numeric(valid[value_col], errors="coerce")
valid = valid.dropna(subset=["x", "y", "z", value_col])
```

### Docstrings

```python
def my_function(param1: str, param2: float) -> dict:
    """Brief description of what the function does.
    
    Extended description with details, assumptions, or notes.
    
    Args:
        param1: Description of param1 (type in hint, not here)
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is invalid
        FileNotFoundError: When file not found
        
    Example:
        >>> result = my_function("test", 3.14)
        >>> print(result)
    """
```

---

## Testing

### Estructura

```
tests/
├── __init__.py
├── test_io.py           # Tests de carga/exportación
├── test_compositing.py  # Tests de compositado
├── test_stats.py        # Tests de estadísticas
└── test_block_model.py  # Tests de modelo de bloques
```

### Escribir tests

```python
import pytest
from proyectovulcano.module import function

@pytest.fixture
def sample_data():
    """Crear datos de prueba."""
    return pd.DataFrame({...})

def test_function_basic(sample_data):
    """Test descripción clara."""
    result = function(sample_data)
    assert result is not None
    assert len(result) > 0

def test_function_error_handling():
    """Test manejo de errores."""
    with pytest.raises(ValueError, match="Expected message"):
        function(invalid_data)
```

### Ejecutar tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_compositing.py::test_composite_drillholes_basic

# Con cobertura
pytest --cov=proyectovulcano --cov-report=html

# Modo verbose
pytest -v

# Mostrar prints
pytest -s
```

---

## Estilo de código

### Black (formatter)

```bash
black src/proyectovulcano/
```

### Flake8 (linter)

```bash
flake8 src/proyectovulcano/ --max-line-length=100
```

### MyPy (type checking)

```bash
mypy src/proyectovulcano/ --ignore-missing-imports
```

---

## CLI Reference

### Ver helpsobre argumentos

```bash
python -m proyectovulcano --help
```

### Debugging

```bash
# Debug con prints
python -m proyectovulcano --file data/example_drillholes.csv --no-show

# Con variables de entorno
DEBUG=1 python -m proyectovulcano ...
```

---

## Agregar nuevas funcionalidades

### 1. Crear función en módulo

```python
# En stats.py
def new_analysis(df: pd.DataFrame, param: float) -> dict:
    """Description."""
    # Implementación
    return results
```

### 2. Crear test

```python
# En tests/test_stats.py
def test_new_analysis():
    df = sample_data()
    result = new_analysis(df, 1.0)
    assert result is not None
```

### 3. Exponer en CLI (si aplica)

```python
# En app.py -> build_parser()
parser.add_argument(
    "--my-param",
    type=float,
    default=1.0,
    help="Description of parameter"
)

# En main()
if args.my_param:
    result = new_analysis(df, args.my_param)
```

### 4. Documentar

- Actualizar docstring de función
- Agregar ejemplos si es complejo
- Actualizar README.md si es feature pública

---

## Checklist para Pull Request

- [ ] Tests escritos y pasando (`pytest`)
- [ ] Código formateado (`black`)
- [ ] Sin warnings de linter (`flake8`)
- [ ] Type hints completos (`mypy`)
- [ ] Docstrings actualizados
- [ ] README.md si aplica
- [ ] Commit messages claros

---

## Troubleshooting

### ImportError con pyvista/vtk

```bash
# Reinstalar
pip install --upgrade --force-reinstall pyvista vtk
```

### Tests fallando por data

```bash
# Verificar que el archivo de datos existe
ls -la data/example_drillholes.csv
```

### GUI no se abre

```bash
# En Linux, puede necesitar:
sudo apt-get install python3-tk

# En Mac
brew install python-tk
```

---

## Performance

### Optimizaciones comunes

```python
# Usar pandas operaciones vectorizadas, no loops
# ❌ Lento
for idx, row in df.iterrows():
    values.append(process(row))

# ✅ Rápido
df['new_col'] = df.apply(lambda x: process(x), axis=1)
```

### Profiling

```bash
# Con cProfile
python -m cProfile -s cumulative -m proyectovulcano ...

# Con memory_profiler
pip install memory-profiler
python -m memory_profiler script.py
```

---

## Documentación adicional

- [Pandas docs](https://pandas.pydata.org)
- [NumPy docs](https://numpy.org)
- [PyVista docs](https://docs.pyvista.org)
- [Python typing](https://typing.readthedocs.io)
