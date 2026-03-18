from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .automation import run_script_file
from .block_model import build_regular_block_model
from .compositing import composite_drillholes
from .io import (
    filter_by_domain,
    list_categorical_columns,
    list_numeric_columns,
    load_drillholes_csv,
)
from .sections import extract_section
from .stats import compare_composites_vs_blocks, format_stats_report
from .viewer import show_block_model, show_drillholes, show_section_2d


class VulcanoMainWindow:
    def __init__(self, root: tk.Tk, initial_file: str = "data/example_drillholes.csv"):
        self.root = root
        self.root.title("Proyecto Vulcano - Interfaz Principal")
        self.root.geometry("1080x820")

        self.file_var = tk.StringVar(value=initial_file)
        self.view_var = tk.StringVar(value="drillholes")
        self.color_by_var = tk.StringVar(value="au")
        self.value_col_var = tk.StringVar(value="au")
        self.value_factor_var = tk.StringVar(value="1.0")

        self.show_traces_var = tk.BooleanVar(value=True)
        self.show_section_window_var = tk.BooleanVar(value=False)
        self.report_stats_var = tk.BooleanVar(value=False)

        self.trace_width_var = tk.StringVar(value="3.0")
        self.point_size_var = tk.StringVar(value="8.0")

        self.domain_col_var = tk.StringVar(value="")
        self.domain_values_var = tk.StringVar(value="")

        self.composite_length_var = tk.StringVar(value="10.0")
        self.block_dx_var = tk.StringVar(value="10.0")
        self.block_dy_var = tk.StringVar(value="10.0")
        self.block_dz_var = tk.StringVar(value="5.0")
        self.pad_x_var = tk.StringVar(value="0.0")
        self.pad_y_var = tk.StringVar(value="0.0")
        self.pad_z_var = tk.StringVar(value="0.0")
        self.idw_power_var = tk.StringVar(value="2.0")
        self.search_radius_var = tk.StringVar(value="25.0")
        self.max_samples_var = tk.StringVar(value="12")

        self.section_source_var = tk.StringVar(value="drillholes")
        self.section_type_var = tk.StringVar(value="longitudinal")
        self.section_center_var = tk.StringVar(value="")
        self.section_width_var = tk.StringVar(value="20.0")
        self.section_slider_var = tk.DoubleVar(value=0.0)

        self.last_composites_df = None
        self.last_block_df = None
        self.last_section_df = None
        self.last_stats_text = ""

        self.color_by_combo: ttk.Combobox | None = None
        self.value_col_combo: ttk.Combobox | None = None
        self.domain_col_combo: ttk.Combobox | None = None
        self.section_slider: tk.Scale | None = None

        self._build_menu()
        self._build_layout()
        self.refresh_variable_lists()

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)

        archivo = tk.Menu(menu, tearoff=0)
        archivo.add_command(label="Abrir CSV...", command=self._browse_file)
        archivo.add_command(label="Usar CSV de ejemplo", command=self._use_example)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.root.quit)
        menu.add_cascade(label="Archivo", menu=archivo)

        ejecutar = tk.Menu(menu, tearoff=0)
        ejecutar.add_command(label="Ejecutar visualizacion", command=self.run_selected_view)
        menu.add_cascade(label="Ejecutar", menu=ejecutar)

        scripts = tk.Menu(menu, tearoff=0)
        scripts.add_command(label="Ejecutar script JSON...", command=self._run_script_json)
        menu.add_cascade(label="Scripts", menu=scripts)

        ayuda = tk.Menu(menu, tearoff=0)
        ayuda.add_command(label="Acerca de", command=self._show_about)
        menu.add_cascade(label="Ayuda", menu=ayuda)

        self.root.config(menu=menu)

    def _build_layout(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="both", expand=True)

        file_frame = ttk.LabelFrame(top, text="Datos", padding=10)
        file_frame.pack(fill="x", pady=5)

        ttk.Label(file_frame, text="CSV:").grid(row=0, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.file_var, width=85).grid(
            row=0, column=1, padx=6, sticky="ew"
        )
        ttk.Button(file_frame, text="Abrir", command=self._browse_file).grid(row=0, column=2)
        ttk.Button(file_frame, text="Recargar columnas", command=self.refresh_variable_lists).grid(
            row=0, column=3, padx=4
        )
        file_frame.columnconfigure(1, weight=1)

        vars_frame = ttk.LabelFrame(top, text="Variables", padding=10)
        vars_frame.pack(fill="x", pady=5)

        ttk.Label(vars_frame, text="color-by:").grid(row=0, column=0, sticky="w")
        self.color_by_combo = ttk.Combobox(vars_frame, textvariable=self.color_by_var, width=18)
        self.color_by_combo.grid(row=0, column=1, padx=5, sticky="w")

        ttk.Label(vars_frame, text="value-col:").grid(row=0, column=2, sticky="w")
        self.value_col_combo = ttk.Combobox(vars_frame, textvariable=self.value_col_var, width=18)
        self.value_col_combo.grid(row=0, column=3, padx=5, sticky="w")

        ttk.Label(vars_frame, text="factor ley:").grid(row=0, column=4, sticky="w")
        ttk.Entry(vars_frame, textvariable=self.value_factor_var, width=10).grid(row=0, column=5, padx=5)

        ttk.Label(vars_frame, text="domain-col:").grid(row=1, column=0, sticky="w")
        self.domain_col_combo = ttk.Combobox(vars_frame, textvariable=self.domain_col_var, width=18)
        self.domain_col_combo.grid(row=1, column=1, padx=5, sticky="w")
        ttk.Label(vars_frame, text="domain-values:").grid(row=1, column=2, sticky="w")
        ttk.Entry(vars_frame, textvariable=self.domain_values_var, width=40).grid(row=1, column=3, padx=5, sticky="w")
        ttk.Label(vars_frame, text="(coma separada)").grid(row=1, column=4, sticky="w")

        mode_frame = ttk.LabelFrame(top, text="Vista", padding=10)
        mode_frame.pack(fill="x", pady=5)

        ttk.Label(mode_frame, text="Modo:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            mode_frame,
            textvariable=self.view_var,
            values=["drillholes", "blocks", "section"],
            state="readonly",
            width=16,
        ).grid(row=0, column=1, padx=5, sticky="w")

        ttk.Checkbutton(mode_frame, text="Trazas", variable=self.show_traces_var).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(mode_frame, text="Ventana de seccion en 3D", variable=self.show_section_window_var).grid(
            row=1, column=1, columnspan=2, sticky="w"
        )
        ttk.Checkbutton(mode_frame, text="Reporte estadistico", variable=self.report_stats_var).grid(
            row=1, column=3, columnspan=2, sticky="w"
        )

        ttk.Label(mode_frame, text="point-size:").grid(row=2, column=0, sticky="w")
        ttk.Entry(mode_frame, textvariable=self.point_size_var, width=10).grid(row=2, column=1, sticky="w")
        ttk.Label(mode_frame, text="trace-width:").grid(row=2, column=2, sticky="w")
        ttk.Entry(mode_frame, textvariable=self.trace_width_var, width=10).grid(row=2, column=3, sticky="w")

        block_frame = ttk.LabelFrame(top, text="Bloques / IDW", padding=10)
        block_frame.pack(fill="x", pady=5)

        ttk.Label(block_frame, text="composite-length").grid(row=0, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.composite_length_var, width=10).grid(row=0, column=1, padx=4)

        ttk.Label(block_frame, text="block-size (dx dy dz)").grid(row=0, column=2, sticky="w")
        ttk.Entry(block_frame, textvariable=self.block_dx_var, width=8).grid(row=0, column=3)
        ttk.Entry(block_frame, textvariable=self.block_dy_var, width=8).grid(row=0, column=4)
        ttk.Entry(block_frame, textvariable=self.block_dz_var, width=8).grid(row=0, column=5)

        ttk.Label(block_frame, text="padding (px py pz)").grid(row=1, column=2, sticky="w")
        ttk.Entry(block_frame, textvariable=self.pad_x_var, width=8).grid(row=1, column=3)
        ttk.Entry(block_frame, textvariable=self.pad_y_var, width=8).grid(row=1, column=4)
        ttk.Entry(block_frame, textvariable=self.pad_z_var, width=8).grid(row=1, column=5)

        ttk.Label(block_frame, text="idw-power").grid(row=1, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.idw_power_var, width=10).grid(row=1, column=1, padx=4)
        ttk.Label(block_frame, text="search-radius").grid(row=2, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.search_radius_var, width=10).grid(row=2, column=1, padx=4)
        ttk.Label(block_frame, text="max-samples").grid(row=2, column=2, sticky="w")
        ttk.Entry(block_frame, textvariable=self.max_samples_var, width=10).grid(row=2, column=3, padx=4)

        section_frame = ttk.LabelFrame(top, text="Seccion", padding=10)
        section_frame.pack(fill="x", pady=5)

        ttk.Label(section_frame, text="source:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            section_frame,
            textvariable=self.section_source_var,
            values=["drillholes", "blocks"],
            state="readonly",
            width=14,
        ).grid(row=0, column=1, padx=4)

        ttk.Label(section_frame, text="type:").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            section_frame,
            textvariable=self.section_type_var,
            values=["longitudinal", "transversal"],
            state="readonly",
            width=14,
        ).grid(row=0, column=3, padx=4)

        ttk.Label(section_frame, text="center:").grid(row=0, column=4, sticky="w")
        ttk.Entry(section_frame, textvariable=self.section_center_var, width=10).grid(row=0, column=5, padx=4)

        ttk.Label(section_frame, text="width:").grid(row=0, column=6, sticky="w")
        ttk.Entry(section_frame, textvariable=self.section_width_var, width=10).grid(row=0, column=7, padx=4)

        self.section_slider = tk.Scale(
            section_frame,
            from_=0.0,
            to=100.0,
            orient="horizontal",
            resolution=0.5,
            variable=self.section_slider_var,
            command=self._on_section_slider,
            length=520,
            label="section-center slider",
        )
        self.section_slider.grid(row=1, column=0, columnspan=7, sticky="ew", pady=4)
        ttk.Button(section_frame, text="Calibrar slider", command=self.calibrate_section_slider).grid(
            row=1, column=7, padx=4
        )

        export_frame = ttk.LabelFrame(top, text="Exportacion", padding=10)
        export_frame.pack(fill="x", pady=5)

        ttk.Button(export_frame, text="Exportar composites", command=self.export_composites).grid(row=0, column=0, padx=4)
        ttk.Button(export_frame, text="Exportar bloques", command=self.export_blocks).grid(row=0, column=1, padx=4)
        ttk.Button(export_frame, text="Exportar seccion", command=self.export_section).grid(row=0, column=2, padx=4)
        ttk.Button(export_frame, text="Exportar reporte", command=self.export_stats).grid(row=0, column=3, padx=4)

        actions = ttk.Frame(top, padding=(0, 8, 0, 4))
        actions.pack(fill="x")
        ttk.Button(actions, text="Ejecutar vista", command=self.run_selected_view).pack(side="left")
        ttk.Button(actions, text="Refrescar variables", command=self.refresh_variable_lists).pack(side="left", padx=6)

        self.log = ScrolledText(top, height=11)
        self.log.pack(fill="both", expand=True)
        self._log("Interfaz lista. Selecciona opciones y pulsa 'Ejecutar vista'.")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "Acerca de",
            "Proyecto Vulcano\nInterfaz principal para visualizar sondajes, bloques y secciones.",
        )

    def _browse_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Seleccionar CSV",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
        )
        if selected:
            self.file_var.set(selected)
            self.refresh_variable_lists()

    def _use_example(self) -> None:
        self.file_var.set("data/example_drillholes.csv")
        self.refresh_variable_lists()

    def _run_script_json(self) -> None:
        selected = filedialog.askopenfilename(
            title="Seleccionar script JSON",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not selected:
            return
        try:
            logs = run_script_file(selected)
            self._log(f"Script ejecutado: {selected}")
            for line in logs:
                self._log(line)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error script", str(exc))
            self._log(f"ERROR script: {exc}")

    def _log(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def refresh_variable_lists(self) -> None:
        try:
            file_path = Path(self.file_var.get().strip())
            if not file_path.exists():
                return
            df = load_drillholes_csv(file_path)
            num_cols = list_numeric_columns(df)
            cat_cols = list_categorical_columns(df)

            if self.color_by_combo is not None:
                self.color_by_combo["values"] = num_cols
            if self.value_col_combo is not None:
                self.value_col_combo["values"] = num_cols
            if self.domain_col_combo is not None:
                self.domain_col_combo["values"] = [""] + cat_cols

            if self.color_by_var.get() not in num_cols and num_cols:
                self.color_by_var.set(num_cols[0])
            if self.value_col_var.get() not in num_cols and num_cols:
                self.value_col_var.set(num_cols[0])

            self.calibrate_section_slider(df)
            self._log(f"Variables cargadas: {len(num_cols)} numericas, {len(cat_cols)} categoricas")
        except Exception as exc:  # noqa: BLE001
            self._log(f"No se pudieron refrescar variables: {exc}")

    def _get_float(self, var: tk.StringVar, name: str, allow_empty: bool = False) -> float | None:
        raw = var.get().strip()
        if allow_empty and not raw:
            return None
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(f"Valor invalido para {name}: {raw}") from exc

    def _get_int(self, var: tk.StringVar, name: str) -> int:
        raw = var.get().strip()
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"Valor invalido para {name}: {raw}") from exc

    def _get_domain_values(self) -> list[str] | None:
        raw = self.domain_values_var.get().strip()
        if not raw:
            return None
        return [x.strip() for x in raw.split(",") if x.strip()]

    def _current_orth_col(self) -> str:
        return "x" if self.section_type_var.get().strip() == "longitudinal" else "y"

    def calibrate_section_slider(self, df=None) -> None:
        if self.section_slider is None:
            return
        if df is None:
            file_path = Path(self.file_var.get().strip())
            if not file_path.exists():
                return
            df = load_drillholes_csv(file_path)
            df = filter_by_domain(
                df,
                domain_col=self.domain_col_var.get().strip() or None,
                domain_values=self._get_domain_values(),
            )
            if df.empty:
                return

        orth_col = self._current_orth_col()
        min_v = float(df[orth_col].min())
        max_v = float(df[orth_col].max())
        if min_v == max_v:
            min_v -= 1.0
            max_v += 1.0

        self.section_slider.configure(from_=min_v, to=max_v)
        if not self.section_center_var.get().strip():
            center = (min_v + max_v) / 2.0
            self.section_slider_var.set(center)
            self.section_center_var.set(f"{center:.2f}")

    def _on_section_slider(self, _value: str) -> None:
        self.section_center_var.set(f"{self.section_slider_var.get():.2f}")

    def _build_block_pipeline(self, df):
        value_col = self.value_col_var.get().strip()
        value_factor = self._get_float(self.value_factor_var, "value-factor")
        if value_col and value_col in df.columns and value_factor != 1.0:
            df = df.copy()
            df[value_col] = df[value_col].astype(float) * value_factor

        composites_df = composite_drillholes(
            df,
            value_col=value_col,
            composite_length=self._get_float(self.composite_length_var, "composite-length"),
        )
        block_df = build_regular_block_model(
            composites_df,
            value_col=value_col,
            cell_size=(
                self._get_float(self.block_dx_var, "block-dx"),
                self._get_float(self.block_dy_var, "block-dy"),
                self._get_float(self.block_dz_var, "block-dz"),
            ),
            padding=(
                self._get_float(self.pad_x_var, "pad-x"),
                self._get_float(self.pad_y_var, "pad-y"),
                self._get_float(self.pad_z_var, "pad-z"),
            ),
            power=self._get_float(self.idw_power_var, "idw-power"),
            search_radius=self._get_float(self.search_radius_var, "search-radius"),
            max_samples=self._get_int(self.max_samples_var, "max-samples"),
        )
        return composites_df, block_df

    def _save_df(self, df, default_name: str) -> None:
        if df is None:
            messagebox.showinfo("Exportacion", "No hay datos para exportar todavia")
            return
        path = filedialog.asksaveasfilename(
            title="Guardar archivo",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json")],
        )
        if not path:
            return
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix.lower() == ".json":
            df.to_json(p, orient="records", indent=2)
        else:
            df.to_csv(p, index=False)
        self._log(f"Exportado: {p}")

    def export_composites(self) -> None:
        self._save_df(self.last_composites_df, "composites.csv")

    def export_blocks(self) -> None:
        self._save_df(self.last_block_df, "block_model.csv")

    def export_section(self) -> None:
        self._save_df(self.last_section_df, "section_points.csv")

    def export_stats(self) -> None:
        if not self.last_stats_text:
            messagebox.showinfo("Exportacion", "No hay reporte estadistico para exportar")
            return
        path = filedialog.asksaveasfilename(
            title="Guardar reporte estadistico",
            initialfile="stats_report.txt",
            defaultextension=".txt",
            filetypes=[("TXT", "*.txt")],
        )
        if not path:
            return
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.last_stats_text + "\n", encoding="utf-8")
        self._log(f"Exportado: {p}")

    def run_selected_view(self) -> None:
        try:
            self.last_section_df = None
            self.last_block_df = None
            self.last_composites_df = None
            self.last_stats_text = ""

            file_path = Path(self.file_var.get().strip())
            if not file_path.exists():
                raise FileNotFoundError(f"No existe el archivo: {file_path}")

            df = load_drillholes_csv(file_path)
            df = filter_by_domain(
                df,
                domain_col=self.domain_col_var.get().strip() or None,
                domain_values=self._get_domain_values(),
            )
            if df.empty:
                raise ValueError("No hay datos luego de aplicar el filtro de dominio")

            value_col = self.value_col_var.get().strip()
            value_factor = self._get_float(self.value_factor_var, "value-factor")
            if value_col and value_col in df.columns and value_factor != 1.0:
                df = df.copy()
                df[value_col] = df[value_col].astype(float) * value_factor

            view = self.view_var.get().strip()
            section_meta = None
            if self.show_section_window_var.get() or view == "section":
                _, section_meta = extract_section(
                    df,
                    section_type=self.section_type_var.get().strip(),
                    center=self._get_float(self.section_center_var, "section-center", allow_empty=True),
                    width=self._get_float(self.section_width_var, "section-width"),
                )

            if view == "drillholes":
                show_drillholes(
                    df,
                    color_by=self.color_by_var.get().strip() or None,
                    point_size=self._get_float(self.point_size_var, "point-size"),
                    show_traces=self.show_traces_var.get(),
                    trace_width=self._get_float(self.trace_width_var, "trace-width"),
                    section_meta=section_meta if self.show_section_window_var.get() else None,
                )
                self._log("Vista drillholes ejecutada.")
                return

            if view == "blocks":
                composites_df, block_df = self._build_block_pipeline(df)
                self.last_composites_df = composites_df
                self.last_block_df = block_df
                if self.report_stats_var.get():
                    report = compare_composites_vs_blocks(
                        composites_df,
                        block_df,
                        value_col=value_col,
                    )
                    text = format_stats_report(report, value_col=value_col)
                    self.last_stats_text = text
                    self._log(text)

                meta_for_overlay = None
                if self.show_section_window_var.get():
                    _, meta_for_overlay = extract_section(
                        block_df,
                        section_type=self.section_type_var.get().strip(),
                        center=self._get_float(self.section_center_var, "section-center", allow_empty=True),
                        width=self._get_float(self.section_width_var, "section-width"),
                    )

                show_block_model(
                    block_df,
                    value_col=value_col,
                    point_size=max(self._get_float(self.block_dx_var, "block-dx"), self._get_float(self.block_dy_var, "block-dy")) * 0.6,
                    section_meta=meta_for_overlay,
                )
                self._log("Vista blocks ejecutada.")
                return

            if self.section_source_var.get().strip() == "blocks":
                composites_df, source_df = self._build_block_pipeline(df)
                self.last_composites_df = composites_df
                self.last_block_df = source_df
                if self.report_stats_var.get():
                    report = compare_composites_vs_blocks(
                        composites_df,
                        source_df,
                        value_col=value_col,
                    )
                    text = format_stats_report(report, value_col=value_col)
                    self.last_stats_text = text
                    self._log(text)
                color_by = value_col
                title = "Proyecto Vulcano - Seccion de Bloques"
            else:
                source_df = df
                color_by = self.color_by_var.get().strip() or None
                title = "Proyecto Vulcano - Seccion de Sondajes"

            section_df, meta = extract_section(
                source_df,
                section_type=self.section_type_var.get().strip(),
                center=self._get_float(self.section_center_var, "section-center", allow_empty=True),
                width=self._get_float(self.section_width_var, "section-width"),
            )
            self.last_section_df = section_df
            show_section_2d(section_df, meta, color_by=color_by, title=title)
            self._log(f"Vista section ejecutada. Puntos en corte: {len(section_df)}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            self._log(f"ERROR: {exc}")


def launch_main_interface(initial_file: str = "data/example_drillholes.csv") -> None:
    root = tk.Tk()
    VulcanoMainWindow(root, initial_file=initial_file)
    root.mainloop()


def main() -> None:
    launch_main_interface()


if __name__ == "__main__":
    main()
