from __future__ import annotations

import argparse

from .block_model import build_regular_block_model
from .compositing import composite_drillholes
from .io import load_drillholes_csv
from .viewer import show_block_model, show_drillholes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MVP de visualizacion de sondajes 3D"
    )
    parser.add_argument(
        "--file",
        required=True,
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
        choices=["drillholes", "blocks"],
        default="drillholes",
        help="Tipo de visualizacion a mostrar",
    )
    parser.add_argument(
        "--value-col",
        default="au",
        help="Columna numerica para compositar/estimar",
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
    parser.set_defaults(show_traces=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    df = load_drillholes_csv(args.file)

    if args.view == "drillholes":
        show_drillholes(
            df,
            color_by=args.color_by,
            point_size=args.point_size,
            show_traces=args.show_traces,
            trace_width=args.trace_width,
        )
        return

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

    show_block_model(
        block_df,
        value_col=args.value_col,
        point_size=max(args.block_size[0], args.block_size[1]) * 0.6,
    )


if __name__ == "__main__":
    main()
