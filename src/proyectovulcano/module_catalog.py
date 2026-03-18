from __future__ import annotations

MODULES = [
    {
        "key": "geology_estimation",
        "name": "Geology & Estimation",
        "description": (
            "Incluye herramientas de geologia, geoestadistica base y estimacion "
            "para minas estratigraficas y metaliferas a cielo abierto."
        ),
    },
    {
        "key": "open_pit_design",
        "name": "Open Pit Design",
        "description": (
            "Incluye herramientas de diseno de pit y perforacion/voladura "
            "para minas metaliferas y estratigraficas a cielo abierto."
        ),
    },
    {
        "key": "underground_design",
        "name": "Underground Design",
        "description": (
            "Incluye herramientas de diseno subte y diseno de perforacion/voladura "
            "subterranea."
        ),
    },
    {
        "key": "multivariate_simulation",
        "name": "Multivariate & Simulation",
        "description": (
            "Incluye herramientas de simulacion y estimacion multivariable."
        ),
    },
    {
        "key": "open_pit_optimisation",
        "name": "Open Pit Optimisation",
        "description": (
            "Incluye optimizador de pit, optimizacion de ley de corte y perfiles "
            "de transporte."
        ),
    },
    {
        "key": "scheduling_suite",
        "name": "Scheduling Suite",
        "description": (
            "Incluye Gantt Scheduler y Short Term Planner integrados."
        ),
    },
    {
        "key": "grade_control_suite",
        "name": "Grade Control Suite",
        "description": (
            "Permite definir con precision mineral/esteril para optimizar ley y "
            "tonelaje al molino."
        ),
    },
    {
        "key": "geotechnical_suite",
        "name": "Geotechnical Suite",
        "description": (
            "Permite analisis y reportes geotecnicos para guiar decisiones de "
            "planificacion y diseno."
        ),
    },
    {
        "key": "drillhole_optimiser",
        "name": "Drillhole Optimiser",
        "description": (
            "Permite generar planes de perforacion infill para maximizar la "
            "recuperacion de recursos."
        ),
    },
    {
        "key": "stope_optimiser",
        "name": "Stope Optimiser",
        "description": (
            "Incluye herramientas para evaluar escenarios subte y producir regiones "
            "minables optimizadas."
        ),
    },
]


MODULE_NAME_BY_KEY = {m["key"]: m["name"] for m in MODULES}
MODULE_DESC_BY_KEY = {m["key"]: m["description"] for m in MODULES}
