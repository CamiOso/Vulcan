from __future__ import annotations

import argparse
import pandas as pd

from .automation import run_script_file
from .block_model import build_regular_block_model
from .compositing import composite_drillholes
from .io import filter_by_domain, load_drillholes_csv
from .sections import extract_section
from .stats import compare_composites_vs_blocks, format_stats_report
from .viewer import show_block_model, show_drillholes, show_section_2d


def _apply_value_factor(df: pd.DataFrame, value_col: str, factor: float) -> pd.DataFrame:
    if factor == 1.0:
        return df
    if value_col not in df.columns:
        return df

    out = df.copy()
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce") * factor
    return out


def _build_blocks_pipeline(df, args):
    composites_df = composite_drillholes(
        df,
        value_col=args.value_col,
        composite_length=args.composite_length,
    )
    if args.export_composites:
        composites_df.to_csv(args.export_composites, index=False)

    block_df = build_regular_block_model(
        composites_df,
        value_col=args.value_col,
        cell_size=tuple(args.block_size),
        padding=tuple(args.padding),
        power=args.idw_power,
        search_radius=args.search_radius,
        max_samples=args.max_samples,
    )
    if args.export_blocks:
        block_df.to_csv(args.export_blocks, index=False)

    if args.report_stats or args.stats_file:
        report = compare_composites_vs_blocks(
            composites_df,
            block_df,
            value_col=args.value_col,
        )
        text = format_stats_report(report, value_col=args.value_col)
        if args.report_stats:
            print(text)
        if args.stats_file:
            with open(args.stats_file, "w", encoding="utf-8") as f:
                f.write(text + "\n")

    return composites_df, block_df


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MVP de visualizacion de sondajes 3D"
    )
    parser.add_argument(
        "--file",
        default="data/example_drillholes.csv",
        help="Ruta al CSV de sondajes",
    )
    parser.add_argument(
        "--color-by",
        default=None,
        help="Columna numerica para colorear",
    )
    parser.add_argument(
        "--point-size",
        type=float,
        default=8.0,
        help="Tamano de punto en pantalla",
    )
    parser.add_argument(
        "--no-traces",
        action="store_false",
        dest="show_traces",
        help="Oculta las trazas de barrenos por hole_id",
    )
    parser.add_argument(
        "--trace-width",
        type=float,
        default=3.0,
        help="Ancho de linea para las trazas de barreno",
    )
    parser.add_argument(
        "--view",
        choices=["drillholes", "blocks", "section", "gui"],
        default="drillholes",
        help="Tipo de visualizacion a mostrar",
    )
    parser.add_argument(
        "--value-col",
        default="au",
        help="Columna numerica para compositar/estimar",
    )
    parser.add_argument(
        "--value-factor",
        type=float,
        default=1.0,
        help="Factor multiplicativo para editar/ajustar la variable de ley",
    )
    parser.add_argument(
        "--domain-col",
        default=None,
        help="Columna categorica para filtro de dominio",
    )
    parser.add_argument(
        "--domain-values",
        nargs="+",
        default=None,
        help="Valores permitidos del dominio (separados por espacio)",
    )
    parser.add_argument(
        "--composite-length",
        type=float,
        default=10.0,
        help="Longitud de composito por barreno",
    )
    parser.add_argument(
        "--block-size",
        type=float,
        nargs=3,
        metavar=("DX", "DY", "DZ"),
        default=(10.0, 10.0, 5.0),
        help="Tamano de bloque en X Y Z",
    )
    parser.add_argument(
        "--padding",
        type=float,
        nargs=3,
        metavar=("PX", "PY", "PZ"),
        default=(0.0, 0.0, 0.0),
        help="Padding de modelo en X Y Z",
    )
    parser.add_argument(
        "--idw-power",
        type=float,
        default=2.0,
        help="Potencia de ponderacion IDW",
    )
    parser.add_argument(
        "--search-radius",
        type=float,
        default=25.0,
        help="Radio de busqueda para IDW",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=12,
        help="Numero maximo de compuestos usados por bloque",
    )
    parser.add_argument(
        "--export-composites",
        default=None,
        help="Ruta CSV para exportar compositos",
    )
    parser.add_argument(
        "--export-blocks",
        default=None,
        help="Ruta CSV para exportar modelo de bloques",
    )
    parser.add_argument(
        "--report-stats",
        action="store_true",
        help="Imprime comparacion estadistica de composites vs bloques",
    )
    parser.add_argument(
        "--stats-file",
        default=None,
        help="Ruta de salida para guardar el reporte estadistico",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Ejecuta pipeline sin abrir ventana de visualizacion",
    )
    parser.add_argument(
        "--section-source",
        choices=["drillholes", "blocks"],
        default="drillholes",
        help="Fuente de datos para la seccion cuando view=section",
    )
    parser.add_argument(
        "--section-type",
        choices=["longitudinal", "transversal"],
        default="longitudinal",
        help="Tipo de seccion 2D",
    )
    parser.add_argument(
        "--section-center",
        type=float,
        default=None,
        help="Centro de la seccion sobre eje ortogonal (auto si se omite)",
    )
    parser.add_argument(
        "--section-width",
        type=float,
        default=20.0,
        help="Ancho total de la ventana de seccion",
    )
    parser.add_argument(
        "--export-section",
        default=None,
        help="Ruta CSV para exportar puntos de la seccion",
    )
    parser.add_argument(
        "--show-section-window",
        action="store_true",
        help="Muestra en 3D la ventana/plano de seccion",
    )
    parser.add_argument(
        "--script",
        default=None,
        help="Ruta a script JSON de automatizacion",
    )
    parser.add_argument(
        "--qt-gui",
        action="store_true",
        help="Lanzar la interfaz mockup PyQt5 (gui_mockup)",
    )
    parser.add_argument(
        "--pyqt5",
        action="store_true",
        help="Lanzar la interfaz PyQt5 en lugar de tkinter",
    )
    parser.set_defaults(show_traces=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "qt_gui", False):
        import sys
        from proyectovulcano import gui_mockup
        sys.exit(gui_mockup.run_qt_gui())

    if args.script:
        logs = run_script_file(args.script)
        for line in logs:
            print(line)
        return

    if args.view == "gui":
        # Support both tkinter (default) and PyQt5 interfaces
        use_pyqt5 = getattr(args, "pyqt5", False)
        
        if use_pyqt5:
            try:
                from .gui_pyqt5 import launch_pyqt5_interface
                launch_pyqt5_interface()
            except ImportError:
                print("PyQt5 no está instalado. Instalalo con: pip install PyQt5")
                print("Usando interfaz tkinter por defecto...")
                from .gui import launch_main_interface
                launch_main_interface(initial_file=args.file)
        else:
            from .gui import launch_main_interface
            launch_main_interface(initial_file=args.file)
        return

    df = load_drillholes_csv(args.file)
    df = filter_by_domain(
        df,
        domain_col=args.domain_col,
        domain_values=args.domain_values,
    )
    df = _apply_value_factor(df, value_col=args.value_col, factor=args.value_factor)
    if df.empty:
        raise ValueError("No hay datos luego de aplicar el filtro de dominio")

    if args.view == "drillholes":
        section_meta = None
        if args.show_section_window:
            _, section_meta = extract_section(
                df,
                section_type=args.section_type,
                center=args.section_center,
                width=args.section_width,
            )
        if not args.no_show:
            show_drillholes(
                df,
                color_by=args.color_by,
                point_size=args.point_size,
                show_traces=args.show_traces,
                trace_width=args.trace_width,
                section_meta=section_meta,
            )
        return

    if args.view == "blocks":
        _, block_df = _build_blocks_pipeline(df, args)
        section_meta = None
        if args.show_section_window:
            _, section_meta = extract_section(
                block_df,
                section_type=args.section_type,
                center=args.section_center,
                width=args.section_width,
            )
        if not args.no_show:
            show_block_model(
                block_df,
                value_col=args.value_col,
                point_size=max(args.block_size[0], args.block_size[1]) * 0.6,
                section_meta=section_meta,
            )
        return

    if args.section_source == "blocks":
        _, source_df = _build_blocks_pipeline(df, args)
        color_by = args.value_col
        title = "Proyecto Vulcano - Seccion de Bloques"
    else:
        source_df = df
        if args.color_by:
            color_by = args.color_by
        elif args.value_col in source_df.columns:
            color_by = args.value_col
        else:
            color_by = None
        title = "Proyecto Vulcano - Seccion de Sondajes"

    section_df, meta = extract_section(
        source_df,
        section_type=args.section_type,
        center=args.section_center,
        width=args.section_width,
    )
    if section_df.empty:
        raise ValueError("No hay puntos dentro de la ventana de seccion")

    if args.export_section:
        section_df.to_csv(args.export_section, index=False)

    if not args.no_show:
        show_section_2d(
            section_df,
            meta,
            color_by=color_by,
            title=title,
        )


if __name__ == "__main__":
    main()
