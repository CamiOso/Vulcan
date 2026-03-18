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
    scalar_bar_args = None
    if color_by and color_by in df.columns:
        if np.issubdtype(df[color_by].dtype, np.number):
            cloud[color_by] = df[color_by].to_numpy()
            scalars_name = color_by
            scalar_bar_args = {
                "title": scalars_name,
                "vertical": False,
                "position_x": 0.28,
                "position_y": 0.06,
                "height": 0.06,
                "width": 0.45,
                "title_font_size": 11,
                "label_font_size": 10,
                "fmt": "%.2f",
            }

    plotter = pv.Plotter(window_size=(1200, 800))
    plotter.set_background("#f5f7fa")

    plotter.add_points(
        cloud,
        render_points_as_spheres=True,
        point_size=point_size,
        scalars=scalars_name,
        cmap="viridis",
        scalar_bar_args=scalar_bar_args,
        color="#d1495b" if scalars_name is None else None,
    )

    if show_traces:
        for line in _iter_hole_traces(df):
            plotter.add_mesh(line, color="#1f2a44", line_width=trace_width)

    plotter.add_axes()
    plotter.add_title("Proyecto Vulcano - Sondajes 3D", font_size=16)
    plotter.show_grid(
        grid="back",
        location="outer",
        ticks="outside",
        n_xlabels=3,
        n_ylabels=3,
        n_zlabels=4,
        fmt="%.0f",
        font_size=10,
        xtitle="X",
        ytitle="Y",
        ztitle="Z",
    )
    plotter.show()


def show_block_model(
    block_df: pd.DataFrame,
    value_col: str,
    point_size: float = 12.0,
) -> None:
    """Render block centers with estimated values."""
    valid = block_df.dropna(subset=[value_col]).copy()
    if valid.empty:
        raise ValueError("No estimated blocks to visualize")

    points = valid[["x", "y", "z"]].to_numpy(dtype=float)
    cloud = pv.PolyData(points)
    cloud[value_col] = valid[value_col].to_numpy(dtype=float)

    plotter = pv.Plotter(window_size=(1200, 800))
    plotter.set_background("#f5f7fa")

    plotter.add_points(
        cloud,
        render_points_as_spheres=False,
        point_size=point_size,
        scalars=value_col,
        cmap="plasma",
        scalar_bar_args={
            "title": f"{value_col} (IDW)",
            "vertical": False,
            "position_x": 0.28,
            "position_y": 0.06,
            "height": 0.06,
            "width": 0.45,
            "title_font_size": 11,
            "label_font_size": 10,
            "fmt": "%.2f",
        },
    )

    plotter.add_axes()
    plotter.add_title("Proyecto Vulcano - Block Model IDW", font_size=16)
    plotter.show_grid(
        grid="back",
        location="outer",
        ticks="outside",
        n_xlabels=3,
        n_ylabels=3,
        n_zlabels=4,
        fmt="%.0f",
        font_size=10,
        xtitle="X",
        ytitle="Y",
        ztitle="Z",
    )
    plotter.show()
