from __future__ import annotations

import numpy as np
import pandas as pd
import pyvista as pv


def _iter_hole_traces(df: pd.DataFrame):
    """Yield one ordered polyline per hole_id."""
    for _, hole_df in df.groupby("hole_id", sort=False):
        if "depth" in hole_df.columns:
            ordered = hole_df.sort_values("depth", ascending=True)
        else:
            ordered = hole_df.sort_values("z", ascending=False)

        points = ordered[["x", "y", "z"]].to_numpy(dtype=float)
        if len(points) < 2:
            continue
        yield pv.lines_from_points(points, close=False)


def show_drillholes(
    df: pd.DataFrame,
    color_by: str | None = None,
    point_size: float = 8.0,
    show_traces: bool = True,
    trace_width: float = 3.0,
) -> None:
    """Render drillhole points in 3D using PyVista."""
    points = df[["x", "y", "z"]].to_numpy(dtype=float)
    cloud = pv.PolyData(points)

    scalars_name = None
    if color_by and color_by in df.columns:
        if np.issubdtype(df[color_by].dtype, np.number):
            cloud[color_by] = df[color_by].to_numpy()
            scalars_name = color_by

    plotter = pv.Plotter(window_size=(1200, 800))
    plotter.set_background("#f5f7fa")

    plotter.add_points(
        cloud,
        render_points_as_spheres=True,
        point_size=point_size,
        scalars=scalars_name,
        cmap="viridis",
        scalar_bar_args={"title": scalars_name} if scalars_name else None,
        color="#d1495b" if scalars_name is None else None,
    )

    if show_traces:
        for line in _iter_hole_traces(df):
            plotter.add_mesh(line, color="#1f2a44", line_width=trace_width)

    plotter.add_axes()
    plotter.add_title("Proyecto Vulcano - Sondajes 3D", font_size=16)
    plotter.show_grid()
    plotter.show()
