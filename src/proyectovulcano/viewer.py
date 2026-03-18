from __future__ import annotations

import numpy as np
import pandas as pd
import pyvista as pv


def show_drillholes(
    df: pd.DataFrame,
    color_by: str | None = None,
    point_size: float = 8.0,
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

    plotter.add_axes()
    plotter.add_title("Proyecto Vulcano - Sondajes 3D", font_size=16)
    plotter.show_grid()
    plotter.show()
