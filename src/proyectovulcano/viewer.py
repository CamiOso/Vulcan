from __future__ import annotations

import matplotlib.pyplot as plt
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


def _expanded_bounds(df: pd.DataFrame) -> tuple[float, float, float, float, float, float]:
    x_min, x_max = float(df["x"].min()), float(df["x"].max())
    y_min, y_max = float(df["y"].min()), float(df["y"].max())
    z_min, z_max = float(df["z"].min()), float(df["z"].max())

    # Ensure non-degenerate box when data has tiny spread on one axis.
    eps = 1.0
    if x_min == x_max:
        x_min -= eps
        x_max += eps
    if y_min == y_max:
        y_min -= eps
        y_max += eps
    if z_min == z_max:
        z_min -= eps
        z_max += eps

    return (x_min, x_max, y_min, y_max, z_min, z_max)


def _add_section_window_overlay(
    plotter: pv.Plotter,
    df: pd.DataFrame,
    section_meta: dict[str, float | str],
) -> None:
    center = float(section_meta["center"])
    width = float(section_meta["width"])
    section_type = str(section_meta["section_type"])
    half = width / 2.0

    x_min, x_max, y_min, y_max, z_min, z_max = _expanded_bounds(df)
    if section_type == "longitudinal":
        bounds = (
            center - half,
            center + half,
            y_min,
            y_max,
            z_min,
            z_max,
        )
    else:
        bounds = (
            x_min,
            x_max,
            center - half,
            center + half,
            z_min,
            z_max,
        )

    slab = pv.Box(bounds=bounds)
    plotter.add_mesh(
        slab,
        color="#f4a261",
        opacity=0.17,
        show_edges=True,
        edge_color="#e76f51",
        line_width=1.0,
    )


def show_drillholes(
    df: pd.DataFrame,
    color_by: str | None = None,
    point_size: float = 8.0,
    show_traces: bool = True,
    trace_width: float = 3.0,
    section_meta: dict[str, float | str] | None = None,
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

    if section_meta is not None:
        _add_section_window_overlay(plotter, df, section_meta)

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
    section_meta: dict[str, float | str] | None = None,
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

    if section_meta is not None:
        _add_section_window_overlay(plotter, valid, section_meta)

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


def show_section_2d(
    section_df: pd.DataFrame,
    meta: dict[str, float | str],
    color_by: str | None = None,
    title: str = "Proyecto Vulcano - Seccion 2D",
) -> None:
    """Render longitudinal/transversal section as a 2D scatter."""
    if section_df.empty:
        raise ValueError("No hay puntos dentro de la ventana de seccion")

    horiz_col = str(meta["horiz_col"])
    horiz_label = str(meta["horiz_label"])
    center = float(meta["center"])
    width = float(meta["width"])
    orth_col = str(meta["orth_col"])

    fig, ax = plt.subplots(figsize=(10, 6))

    use_color = None
    if color_by and color_by in section_df.columns:
        series = pd.to_numeric(section_df[color_by], errors="coerce")
        if series.notna().any():
            use_color = series

    if use_color is not None:
        sc = ax.scatter(
            section_df[horiz_col],
            section_df["z"],
            c=use_color,
            cmap="viridis",
            s=45,
            edgecolors="none",
        )
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label(color_by)
    else:
        ax.scatter(
            section_df[horiz_col],
            section_df["z"],
            color="#1f2a44",
            s=45,
            edgecolors="none",
        )

    ax.set_xlabel(horiz_label)
    ax.set_ylabel("Z")
    ax.set_title(
        f"{title} | {orth_col.upper()}={center:.2f} +/- {width / 2.0:.2f}"
    )
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    plt.show()
