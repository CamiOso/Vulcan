from __future__ import annotations

import argparse

from .io import load_drillholes_csv
from .viewer import show_drillholes


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
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    df = load_drillholes_csv(args.file)
    show_drillholes(df, color_by=args.color_by, point_size=args.point_size)


if __name__ == "__main__":
    main()
