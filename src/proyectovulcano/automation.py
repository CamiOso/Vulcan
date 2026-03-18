from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .block_model import build_regular_block_model
from .compositing import composite_drillholes
from .io import filter_by_domain, load_drillholes_csv
from .sections import extract_section
from .stats import compare_composites_vs_blocks, format_stats_report
from .viewer import show_block_model, show_drillholes, show_section_2d


def _to_tuple3(value, default: tuple[float, float, float]) -> tuple[float, float, float]:
	if value is None:
		return default
	if not isinstance(value, list | tuple) or len(value) != 3:
		raise ValueError("Expected array of length 3")
	return float(value[0]), float(value[1]), float(value[2])


def _apply_value_factor(df: pd.DataFrame, value_col: str, factor: float) -> pd.DataFrame:
	if factor == 1.0:
		return df
	if value_col not in df.columns:
		return df
	out = df.copy()
	out[value_col] = pd.to_numeric(out[value_col], errors="coerce") * factor
	return out


def run_script_config(config: dict) -> list[str]:
	"""Run a full workflow from a JSON-compatible config dictionary."""
	logs: list[str] = []

	file_path = config.get("file", "data/example_drillholes.csv")
	view = config.get("view", "drillholes")
	color_by = config.get("color_by")
	value_col = config.get("value_col", "au")
	value_factor = float(config.get("value_factor", 1.0))

	domain_col = config.get("domain_col")
	domain_values = config.get("domain_values")
	no_show = bool(config.get("no_show", True))

	point_size = float(config.get("point_size", 8.0))
	show_traces = bool(config.get("show_traces", True))
	trace_width = float(config.get("trace_width", 3.0))

	section_source = config.get("section_source", "drillholes")
	section_type = config.get("section_type", "longitudinal")
	section_center = config.get("section_center")
	section_width = float(config.get("section_width", 20.0))
	show_section_window = bool(config.get("show_section_window", False))

	composite_length = float(config.get("composite_length", 10.0))
	block_size = _to_tuple3(config.get("block_size"), (10.0, 10.0, 5.0))
	padding = _to_tuple3(config.get("padding"), (0.0, 0.0, 0.0))
	idw_power = float(config.get("idw_power", 2.0))
	search_radius = float(config.get("search_radius", 25.0))
	max_samples = int(config.get("max_samples", 12))

	export = config.get("export", {}) or {}
	export_composites = export.get("composites")
	export_blocks = export.get("blocks")
	export_section = export.get("section")
	stats_file = export.get("stats")
	report_stats = bool(config.get("report_stats", False) or stats_file)

	df = load_drillholes_csv(file_path)
	df = filter_by_domain(df, domain_col=domain_col, domain_values=domain_values)
	if df.empty:
		raise ValueError("No data after applying domain filter")

	df = _apply_value_factor(df, value_col=value_col, factor=value_factor)

	def build_blocks_from(source_df: pd.DataFrame):
		composites_df = composite_drillholes(
			source_df,
			value_col=value_col,
			composite_length=composite_length,
		)
		if export_composites:
			Path(export_composites).parent.mkdir(parents=True, exist_ok=True)
			composites_df.to_csv(export_composites, index=False)
			logs.append(f"Exported composites: {export_composites}")

		block_df = build_regular_block_model(
			composites_df,
			value_col=value_col,
			cell_size=block_size,
			padding=padding,
			power=idw_power,
			search_radius=search_radius,
			max_samples=max_samples,
		)
		if export_blocks:
			Path(export_blocks).parent.mkdir(parents=True, exist_ok=True)
			block_df.to_csv(export_blocks, index=False)
			logs.append(f"Exported blocks: {export_blocks}")

		if report_stats:
			report = compare_composites_vs_blocks(composites_df, block_df, value_col=value_col)
			text = format_stats_report(report, value_col=value_col)
			logs.append(text)
			if stats_file:
				Path(stats_file).parent.mkdir(parents=True, exist_ok=True)
				Path(stats_file).write_text(text + "\n", encoding="utf-8")
				logs.append(f"Exported stats: {stats_file}")

		return composites_df, block_df

	if view == "drillholes":
		if not no_show:
			section_meta = None
			if show_section_window:
				_, section_meta = extract_section(df, section_type=section_type, center=section_center, width=section_width)
			show_drillholes(
				df,
				color_by=color_by,
				point_size=point_size,
				show_traces=show_traces,
				trace_width=trace_width,
				section_meta=section_meta,
			)
		logs.append("Completed view: drillholes")
		return logs

	if view == "blocks":
		_, block_df = build_blocks_from(df)
		if not no_show:
			section_meta = None
			if show_section_window:
				_, section_meta = extract_section(
					block_df,
					section_type=section_type,
					center=section_center,
					width=section_width,
				)
			show_block_model(
				block_df,
				value_col=value_col,
				point_size=max(block_size[0], block_size[1]) * 0.6,
				section_meta=section_meta,
			)
		logs.append("Completed view: blocks")
		return logs

	if section_source == "blocks":
		_, source_df = build_blocks_from(df)
		section_color = value_col
		section_title = "Proyecto Vulcano - Seccion de Bloques"
	else:
		source_df = df
		section_color = color_by if color_by else (value_col if value_col in source_df.columns else None)
		section_title = "Proyecto Vulcano - Seccion de Sondajes"

	section_df, meta = extract_section(
		source_df,
		section_type=section_type,
		center=section_center,
		width=section_width,
	)
	if export_section:
		Path(export_section).parent.mkdir(parents=True, exist_ok=True)
		section_df.to_csv(export_section, index=False)
		logs.append(f"Exported section: {export_section}")

	if not no_show:
		show_section_2d(section_df, meta, color_by=section_color, title=section_title)

	logs.append(f"Completed view: section ({len(section_df)} points)")
	return logs


def run_script_file(script_path: str | Path) -> list[str]:
	"""Load and execute a workflow script from JSON file."""
	path = Path(script_path)
	if not path.exists():
		raise FileNotFoundError(f"Script file not found: {path}")

	config = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(config, dict):
		raise ValueError("Script JSON must be an object")
	return run_script_config(config)

