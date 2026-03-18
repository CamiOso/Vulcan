from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .automation import run_script_file
from .block_model import build_regular_block_model
from .compositing import composite_drillholes
from .config import load_user_config, save_user_config
from .io import (
    filter_by_domain,
    list_categorical_columns,
    list_numeric_columns,
    load_drillholes_csv,
)
from .module_catalog import MODULE_DESC_BY_KEY, MODULE_NAME_BY_KEY, MODULES
from .sections import extract_section
from .stats import compare_composites_vs_blocks, format_stats_report
from .viewer import show_block_model, show_drillholes, show_section_2d

VIEW_MAP = {
    "Sondajes 3D": "drillholes",
    "Modelo de Bloques": "blocks",
    "Seccion 2D": "section",
}
SECTION_SOURCE_MAP = {"Sondajes": "drillholes", "Bloques": "blocks"}
SECTION_TYPE_MAP = {"Longitudinal": "longitudinal", "Transversal": "transversal"}


class SetupWizard:
    """Asistente de configuracion inicial (primer uso)."""

    def __init__(self, parent: tk.Tk, config: dict):
        self.config = config
        self.step = 0
        self.done = False

        self.win = tk.Toplevel(parent)
        self.win.title("Asistente Inicial")
        self.win.geometry("720x420")
        self.win.resizable(False, False)

        self.resolution_var = tk.StringVar(value=str(config.get("ui_resolution", "1280x800")))
        self.style_var = tk.StringVar(value=str(config.get("ui_style", "Claro")))
        self.units_var = tk.StringVar(value=str(config.get("units", "metros")))

        self.body = ttk.Frame(self.win, padding=16)
        self.body.pack(fill="both", expand=True)

        nav = ttk.Frame(self.win, padding=(12, 4, 12, 12))
        nav.pack(fill="x")
        self.back_btn = ttk.Button(nav, text="Atras", command=self._back)
        self.back_btn.pack(side="left")
        ttk.Button(nav, text="Cancelar", command=self._cancel).pack(side="right")
        self.next_btn = ttk.Button(nav, text="Siguiente", command=self._next)
        self.next_btn.pack(side="right", padx=6)

        self._render_step()

    def show_modal(self) -> bool:
        self.win.grab_set()
        self.win.wait_window()
        return self.done

    def _clear(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()

    def _render_step(self) -> None:
        self._clear()
        self.back_btn.configure(state="normal" if self.step > 0 else "disabled")

        if self.step == 0:
            ttk.Label(self.body, text="Bienvenido al asistente", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
            ttk.Label(
                self.body,
                text=(
                    "1) Bienvenida\n"
                    "2) Configuracion grafica\n"
                    "3) Seleccion de unidades\n"
                    "4) Confirmacion final"
                ),
                justify="left",
            ).pack(anchor="w", pady=(10, 0))
        elif self.step == 1:
            ttk.Label(self.body, text="Configuracion de interfaz grafica", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
            frm = ttk.Frame(self.body)
            frm.pack(anchor="w", pady=12)
            ttk.Label(frm, text="Resolucion:").grid(row=0, column=0, sticky="w")
            ttk.Combobox(
                frm,
                textvariable=self.resolution_var,
                values=["1280x800", "1366x768", "1600x900", "1920x1080"],
                state="readonly",
                width=18,
            ).grid(row=0, column=1, padx=8)
            ttk.Label(frm, text="Estilo visual:").grid(row=1, column=0, sticky="w", pady=6)
            ttk.Combobox(
                frm,
                textvariable=self.style_var,
                values=["Claro", "Oscuro", "Tecnico"],
                state="readonly",
                width=18,
            ).grid(row=1, column=1, padx=8)
        elif self.step == 2:
            ttk.Label(self.body, text="Seleccion de unidades", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
            ttk.Label(self.body, text="Unidad principal para modelado:").pack(anchor="w", pady=(12, 8))
            ttk.Combobox(
                self.body,
                textvariable=self.units_var,
                values=["metros", "pies"],
                state="readonly",
                width=18,
            ).pack(anchor="w")
        else:
            ttk.Label(self.body, text="Pantalla final", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
            ttk.Label(
                self.body,
                text=(
                    f"Resolucion: {self.resolution_var.get()}\n"
                    f"Estilo: {self.style_var.get()}\n"
                    f"Unidades: {self.units_var.get()}\n\n"
                    "Pulsa Finalizar para entrar al entorno de diseño."
                ),
                justify="left",
            ).pack(anchor="w", pady=(12, 0))
            self.next_btn.configure(text="Finalizar")
            return

        self.next_btn.configure(text="Siguiente")

    def _back(self) -> None:
        if self.step > 0:
            self.step -= 1
            self._render_step()

    def _next(self) -> None:
        if self.step < 3:
            self.step += 1
            self._render_step()
            return

        self.config["ui_resolution"] = self.resolution_var.get()
        self.config["ui_style"] = self.style_var.get()
        self.config["units"] = self.units_var.get()
        self.config["setup_completed"] = True
        save_user_config(self.config)
        self.done = True
        self.win.destroy()

    def _cancel(self) -> None:
        self.done = False
        self.win.destroy()


class StartupWindow:
    """Ventana de inicio sin licencia: carpeta de datos + acceso a entorno principal."""

    def __init__(self, root: tk.Tk, config: dict, on_open_env, initial_file: str):
        self.root = root
        self.config = config
        self.on_open_env = on_open_env
        self.initial_file = initial_file

        self.root.title("Proyecto Vulcano - Inicio")
        self.root.geometry("860x560")

        self.data_folder_var = tk.StringVar(value=str(config.get("data_folder", "")))

        self._build_ui()
        self._status_boot_messages()

    def _build_ui(self) -> None:
        wrap = ttk.Frame(self.root, padding=14)
        wrap.pack(fill="both", expand=True)

        ttk.Label(wrap, text="Ventana de Presentacion", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        ttk.Label(
            wrap,
            text="Selecciona carpeta de datos. Para abrir el entorno: doble clic en el botón.",
        ).pack(anchor="w", pady=(4, 12))

        data_frame = ttk.LabelFrame(wrap, text="Carpeta de datos", padding=10)
        data_frame.pack(fill="x", pady=6)
        ttk.Label(data_frame, text="Directorio de trabajo:").grid(row=0, column=0, sticky="w")
        ttk.Entry(data_frame, textvariable=self.data_folder_var, width=78).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(data_frame, text="Explorar", command=self._browse_data_folder).grid(row=0, column=2)
        data_frame.columnconfigure(1, weight=1)

        env_frame = ttk.LabelFrame(wrap, text="Entorno de diseño", padding=10)
        env_frame.pack(fill="x", pady=6)
        env_btn = ttk.Button(env_frame, text="Abrir entorno", width=24)
        env_btn.pack(side="left")
        env_btn.bind("<Double-Button-1>", self._open_env)
        ttk.Button(env_frame, text="Guardar", command=self._save).pack(side="left", padx=8)

        self.msg = ScrolledText(wrap, height=12)
        self.msg.pack(fill="both", expand=True, pady=(10, 0))

    def _log(self, text: str) -> None:
        self.msg.insert("end", text + "\n")
        self.msg.see("end")

    def _status_boot_messages(self) -> None:
        if not self.data_folder_var.get().strip():
            self._log("Mensaje: carpeta de datos no configurada")
        else:
            self._log(f"Carpeta de datos: {self.data_folder_var.get()}")

    def _save(self) -> None:
        self.config["data_folder"] = self.data_folder_var.get().strip()
        save_user_config(self.config)

    def _browse_data_folder(self) -> None:
        start = self.data_folder_var.get().strip() or str(Path.home())
        selected = filedialog.askdirectory(title="Seleccionar carpeta de datos", initialdir=start)
        if selected:
            self.data_folder_var.set(selected)
            self._save()
            self._log(f"Carpeta de datos seleccionada: {selected}")

    def _open_env(self, _event=None) -> None:
        self._save()

        data_folder = self.data_folder_var.get().strip()
        if not data_folder:
            self._log("Error: carpeta de datos no configurada")
            messagebox.showwarning("Configuracion", "Debes seleccionar carpeta de datos")
            return

        if not Path(data_folder).exists():
            self._log("Error: carpeta de datos invalida")
            messagebox.showerror("Configuracion", "La carpeta de datos no existe")
            return

        self._log("Abriendo entorno...")
        self.on_open_env(self.config, self.initial_file)


class VulcanoMainWindow:
    """Ventana principal de diseño/modelado."""

    def __init__(self, win: tk.Toplevel, config: dict, initial_file: str):
        self.win = win
        self.config = config
        self.win.title("Proyecto Vulcano")
        self.win.geometry(str(config.get("ui_resolution", "1280x800")))

        # Log panel for user feedback and error messages
        self.log = ScrolledText(self.win, height=8, state="normal")
        self.log.pack(fill="x", padx=8, pady=4)

        data_folder = str(config.get("data_folder", "")).strip()
        self.file_var = tk.StringVar(value=str(Path(data_folder) / initial_file) if data_folder else initial_file)

        self.mode_var = tk.StringVar(value="Sondajes 3D")
        self.color_by_var = tk.StringVar(value="au")
        self.value_col_var = tk.StringVar(value="au")
        self.value_factor_var = tk.StringVar(value="1.0")

        self.domain_col_var = tk.StringVar(value="")
        self.domain_values_var = tk.StringVar(value="")

        self.show_traces_var = tk.BooleanVar(value=True)
        self.show_section_window_var = tk.BooleanVar(value=False)
        self.report_stats_var = tk.BooleanVar(value=False)

        self.point_size_var = tk.StringVar(value="8.0")
        self.trace_width_var = tk.StringVar(value="3.0")

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

        self.section_source_var = tk.StringVar(value="Sondajes")
        self.section_type_var = tk.StringVar(value="Longitudinal")
        self.section_center_var = tk.StringVar(value="")
        self.section_width_var = tk.StringVar(value="20.0")
        self.section_slider_var = tk.DoubleVar(value=0.0)

        self.last_composites_df = None
        self.last_block_df = None
        self.last_section_df = None
        self.last_stats_text = ""

        self.module_enabled_vars: dict[str, tk.BooleanVar] = {
            m["key"]: tk.BooleanVar(value=m["key"] in set(config.get("enabled_modules", [])))
            for m in MODULES
        }
        self.module_listbox = None
        self.module_detail = None

        self.color_by_combo = None
        self.value_col_combo = None
        self.domain_combo = None
        self.section_slider = None

        self._build_menu()
        self._build_layout()
        self.refresh_variable_lists()

    def _data_folder(self) -> Path:
        raw = str(self.config.get("data_folder", "")).strip()
        return Path(raw) if raw else Path.cwd()

    def _resolve_file(self) -> Path:
        p = Path(self.file_var.get().strip())
        if p.is_absolute():
            return p
        # Fix: ensure correct path for example CSV
        if str(p) == "data/data/example_drillholes.csv":
            return Path("data/example_drillholes.csv").absolute()
        return self._data_folder() / p

    def _save_enabled_modules(self) -> None:
        enabled = [k for k, var in self.module_enabled_vars.items() if var.get()]
        self.config["enabled_modules"] = enabled
        save_user_config(self.config)

    def _enabled(self, key: str) -> bool:
        return self.module_enabled_vars.get(key, tk.BooleanVar(value=False)).get()

    def _build_menu(self) -> None:
        menu = tk.Menu(self.win)

        archivo = tk.Menu(menu, tearoff=0)
        archivo.add_command(label="Seleccionar carpeta de datos...", command=self._select_data_folder)
        archivo.add_command(label="Abrir CSV...", command=self._browse_file)
        archivo.add_command(label="Usar CSV de ejemplo", command=self._use_example)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.win.destroy)
        menu.add_cascade(label="Archivo", menu=archivo)

        ejecutar = tk.Menu(menu, tearoff=0)
        ejecutar.add_command(label="Ejecutar visualizacion", command=self.run_selected_view)
        menu.add_cascade(label="Ejecutar", menu=ejecutar)

        scripts = tk.Menu(menu, tearoff=0)
        scripts.add_command(label="Ejecutar script JSON...", command=self._run_script_json)
        menu.add_cascade(label="Scripts", menu=scripts)

        ayuda = tk.Menu(menu, tearoff=0)
        ayuda.add_command(label="Acerca de", command=self._about)
        menu.add_cascade(label="Ayuda", menu=ayuda)

        self.win.config(menu=menu)

    def _build_layout(self) -> None:
        top = ttk.Frame(self.win, padding=10)
        top.pack(fill="both", expand=True)

        file_frame = ttk.LabelFrame(top, text="Datos", padding=10)
        file_frame.pack(fill="x", pady=5)
        ttk.Label(file_frame, text="CSV:").grid(row=0, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.file_var, width=96).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(file_frame, text="Abrir", command=self._browse_file).grid(row=0, column=2)
        ttk.Button(file_frame, text="Recargar columnas", command=self.refresh_variable_lists).grid(row=0, column=3, padx=4)
        file_frame.columnconfigure(1, weight=1)

        modules_frame = ttk.LabelFrame(top, text="Modulos de Vulcan", padding=10)
        modules_frame.pack(fill="x", pady=5)

        checks = ttk.Frame(modules_frame)
        checks.pack(side="left", fill="y", padx=(0, 10))
        for idx, m in enumerate(MODULES):
            cb = ttk.Checkbutton(
                checks,
                text=m["name"],
                variable=self.module_enabled_vars[m["key"]],
                command=self._save_enabled_modules,
            )
            cb.grid(row=idx, column=0, sticky="w")

        detail_wrap = ttk.Frame(modules_frame)
        detail_wrap.pack(side="left", fill="both", expand=True)
        ttk.Label(detail_wrap, text="Detalles del producto:").pack(anchor="w")
        self.module_listbox = tk.Listbox(detail_wrap, height=6)
        self.module_listbox.pack(fill="x", pady=(2, 4))
        for m in MODULES:
            self.module_listbox.insert("end", m["name"])
        self.module_listbox.bind("<<ListboxSelect>>", self._on_module_select)

        self.module_detail = ScrolledText(detail_wrap, height=5)
        self.module_detail.pack(fill="both", expand=True)
        self.module_detail.insert("end", "Selecciona un modulo para ver su detalle.")
        self.module_detail.configure(state="disabled")

        # Panel Geology & Estimation
        geology_frame = ttk.LabelFrame(top, text="Geology & Estimation", padding=10)
        geology_frame.pack(fill="x", pady=5)
        ttk.Button(geology_frame, text="Validar datos de barrenos", command=self._validate_drillholes).pack(side="left", padx=4)
        ttk.Button(geology_frame, text="Compositar por longitud", command=self._composite_drillholes).pack(side="left", padx=4)
        ttk.Button(geology_frame, text="Modelado estratigráfico", command=self._stratigraphic_model).pack(side="left", padx=4)
        ttk.Button(geology_frame, text="Estimación IDW", command=self._estimate_idw).pack(side="left", padx=4)
        ttk.Button(geology_frame, text="Variograma", command=self._show_variogram).pack(side="left", padx=4)
    def _validate_drillholes(self):
        from .geology_estimation import DrillholeDataManager
        try:
            df = load_drillholes_csv(self._resolve_file())
            manager = DrillholeDataManager(df)
            result = manager.validate_columns()
            msg = f"Validación: {'OK' if result['valid'] else 'Faltan columnas: ' + ', '.join(result['missing'])}"
            self._log(msg)
        except Exception as exc:
            self._log(f"Error validando barrenos: {exc}")

    def _composite_drillholes(self):
        from .geology_estimation import CompositingTools
        try:
            df = load_drillholes_csv(self._resolve_file())
            composites = CompositingTools.composite_by_length(df, length=self._get_float(self.composite_length_var, "longitud-composito"), value_col=self.value_col_var.get())
            self._log(f"Compositado: {len(composites)} intervalos")
        except Exception as exc:
            self._log(f"Error compositando: {exc}")

    def _stratigraphic_model(self):
        from .geology_estimation import StratigraphicModeler
        try:
            df = load_drillholes_csv(self._resolve_file())
            domain_col = self.domain_col_var.get().strip() or "lith"
            model = StratigraphicModeler.explicit_model(df, domain_col=domain_col)
            self._log(f"Modelado estratigráfico: {len(model)} dominios")
        except Exception as exc:
            self._log(f"Error modelando estratigrafía: {exc}")

    def _estimate_idw(self):
        from .geology_estimation import EstimationMethods
        try:
            df = load_drillholes_csv(self._resolve_file())
            x = self._get_float(self.block_dx_var, "dx")
            y = self._get_float(self.block_dy_var, "dy")
            z = self._get_float(self.block_dz_var, "dz")
            val = EstimationMethods.idw(df, x, y, z, self.value_col_var.get())
            self._log(f"Estimación IDW en ({x},{y},{z}): {val:.3f}")
        except Exception as exc:
            self._log(f"Error en IDW: {exc}")

    def _show_variogram(self):
        from .geology_estimation import VariogramAnalyzer
        try:
            df = load_drillholes_csv(self._resolve_file())
            vario = VariogramAnalyzer.experimental_variogram(df, self.value_col_var.get(), lag=10, n_lags=5)
            self._log(f"Variograma generado: {len(vario)} lags")
        except Exception as exc:
            self._log(f"Error generando variograma: {exc}")

        vars_frame = ttk.LabelFrame(top, text="Gestion de variables", padding=10)
        vars_frame.pack(fill="x", pady=5)
        ttk.Label(vars_frame, text="Variable visual:").grid(row=0, column=0, sticky="w")
        self.color_by_combo = ttk.Combobox(vars_frame, textvariable=self.color_by_var, width=18)
        self.color_by_combo.grid(row=0, column=1, padx=5)
        ttk.Label(vars_frame, text="Variable de modelo:").grid(row=0, column=2, sticky="w")
        self.value_col_combo = ttk.Combobox(vars_frame, textvariable=self.value_col_var, width=18)
        self.value_col_combo.grid(row=0, column=3, padx=5)
        ttk.Label(vars_frame, text="Factor ley:").grid(row=0, column=4, sticky="w")
        ttk.Entry(vars_frame, textvariable=self.value_factor_var, width=10).grid(row=0, column=5)

        ttk.Label(vars_frame, text="Columna dominio:").grid(row=1, column=0, sticky="w")
        self.domain_combo = ttk.Combobox(vars_frame, textvariable=self.domain_col_var, width=18)
        self.domain_combo.grid(row=1, column=1, padx=5)
        ttk.Label(vars_frame, text="Valores dominio:").grid(row=1, column=2, sticky="w")
        ttk.Entry(vars_frame, textvariable=self.domain_values_var, width=32).grid(row=1, column=3, padx=5)

        mode_frame = ttk.LabelFrame(top, text="Vista", padding=10)
        mode_frame.pack(fill="x", pady=5)
        ttk.Label(mode_frame, text="Modo:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(mode_frame, textvariable=self.mode_var, values=list(VIEW_MAP.keys()), state="readonly", width=18).grid(row=0, column=1, padx=4)
        ttk.Checkbutton(mode_frame, text="Trazas", variable=self.show_traces_var).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(mode_frame, text="Ventana de seccion 3D", variable=self.show_section_window_var).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(mode_frame, text="Reporte estadistico", variable=self.report_stats_var).grid(row=1, column=2, sticky="w")
        ttk.Label(mode_frame, text="Tamano punto:").grid(row=2, column=0, sticky="w")
        ttk.Entry(mode_frame, textvariable=self.point_size_var, width=10).grid(row=2, column=1, sticky="w")
        ttk.Label(mode_frame, text="Ancho traza:").grid(row=2, column=2, sticky="w")
        ttk.Entry(mode_frame, textvariable=self.trace_width_var, width=10).grid(row=2, column=3, sticky="w")

        block_frame = ttk.LabelFrame(top, text="Bloques/IDW", padding=10)
        block_frame.pack(fill="x", pady=5)
        ttk.Label(block_frame, text="Long composito:").grid(row=0, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.composite_length_var, width=10).grid(row=0, column=1)
        ttk.Label(block_frame, text="Bloque dx dy dz:").grid(row=0, column=2, sticky="w")
        ttk.Entry(block_frame, textvariable=self.block_dx_var, width=8).grid(row=0, column=3)
        ttk.Entry(block_frame, textvariable=self.block_dy_var, width=8).grid(row=0, column=4)
        ttk.Entry(block_frame, textvariable=self.block_dz_var, width=8).grid(row=0, column=5)
        ttk.Label(block_frame, text="Padding px py pz:").grid(row=1, column=2, sticky="w")
        ttk.Entry(block_frame, textvariable=self.pad_x_var, width=8).grid(row=1, column=3)
        ttk.Entry(block_frame, textvariable=self.pad_y_var, width=8).grid(row=1, column=4)
        ttk.Entry(block_frame, textvariable=self.pad_z_var, width=8).grid(row=1, column=5)
        ttk.Label(block_frame, text="Potencia IDW:").grid(row=1, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.idw_power_var, width=10).grid(row=1, column=1)
        ttk.Label(block_frame, text="Radio busqueda:").grid(row=2, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.search_radius_var, width=10).grid(row=2, column=1)
        ttk.Label(block_frame, text="Max muestras:").grid(row=2, column=2, sticky="w")
        ttk.Entry(block_frame, textvariable=self.max_samples_var, width=10).grid(row=2, column=3)

        section_frame = ttk.LabelFrame(top, text="Secciones", padding=10)
        section_frame.pack(fill="x", pady=5)
        ttk.Label(section_frame, text="Fuente:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(section_frame, textvariable=self.section_source_var, values=list(SECTION_SOURCE_MAP.keys()), state="readonly", width=14).grid(row=0, column=1)
        ttk.Label(section_frame, text="Tipo:").grid(row=0, column=2, sticky="w")
        ttk.Combobox(section_frame, textvariable=self.section_type_var, values=list(SECTION_TYPE_MAP.keys()), state="readonly", width=14).grid(row=0, column=3)
        ttk.Label(section_frame, text="Centro:").grid(row=0, column=4, sticky="w")
        ttk.Entry(section_frame, textvariable=self.section_center_var, width=10).grid(row=0, column=5)
        ttk.Label(section_frame, text="Ancho:").grid(row=0, column=6, sticky="w")
        ttk.Entry(section_frame, textvariable=self.section_width_var, width=10).grid(row=0, column=7)

        self.section_slider = tk.Scale(
            section_frame,
            from_=0.0,
            to=100.0,
            orient="horizontal",
            resolution=0.5,
            variable=self.section_slider_var,
            command=self._on_section_slider,
            label="Control rapido de centro",
            length=520,
        )
        self.section_slider.grid(row=1, column=0, columnspan=7, sticky="ew", pady=4)
        ttk.Button(section_frame, text="Calibrar", command=self.calibrate_section_slider).grid(row=1, column=7)

        export_frame = ttk.LabelFrame(top, text="Indexado y exportacion", padding=10)
        export_frame.pack(fill="x", pady=5)
        ttk.Button(export_frame, text="Exportar composites", command=self.export_composites).grid(row=0, column=0, padx=4)
        ttk.Button(export_frame, text="Exportar bloques", command=self.export_blocks).grid(row=0, column=1, padx=4)
        ttk.Button(export_frame, text="Exportar seccion", command=self.export_section).grid(row=0, column=2, padx=4)
        ttk.Button(export_frame, text="Exportar reporte", command=self.export_stats).grid(row=0, column=3, padx=4)

        actions = ttk.Frame(top, padding=(0, 8, 0, 4))
        actions.pack(fill="x")
        ttk.Button(actions, text="Ejecutar vista", command=self.run_selected_view).pack(side="left")

        self.log = ScrolledText(top, height=10)
        self.log.pack(fill="both", expand=True)
        self._log("Proyecto Vulcano listo")

    def _on_module_select(self, _event=None) -> None:
        if self.module_listbox is None or self.module_detail is None:
            return
        selection = self.module_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = MODULES[idx]["key"]
        name = MODULE_NAME_BY_KEY[key]
        desc = MODULE_DESC_BY_KEY[key]
        enabled = "Activo" if self.module_enabled_vars[key].get() else "Inactivo"

        self.module_detail.configure(state="normal")
        self.module_detail.delete("1.0", "end")
        self.module_detail.insert("end", f"{name}\nEstado: {enabled}\n\nDetalles del producto:\n{desc}")
        self.module_detail.configure(state="disabled")

    def _about(self) -> None:
        messagebox.showinfo("Acerca de", "Proyecto Vulcano: área principal de diseño y modelado")

    def _select_data_folder(self) -> None:
        selected = filedialog.askdirectory(title="Seleccionar carpeta de datos", initialdir=str(self._data_folder()))
        if not selected:
            return
        self.config["data_folder"] = selected
        save_user_config(self.config)
        self._log(f"Carpeta de datos actualizada: {selected}")

    def _browse_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Seleccionar CSV",
            initialdir=str(self._data_folder()),
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
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
            initialdir=str(self._data_folder()),
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not selected:
            return
        try:
            for line in run_script_file(selected):
                self._log(line)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error script", str(exc))

    def _log(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

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

    def _domain_values(self) -> list[str] | None:
        raw = self.domain_values_var.get().strip()
        if not raw:
            return None
        return [x.strip() for x in raw.split(",") if x.strip()]

    def _mode(self) -> str:
        return VIEW_MAP[self.mode_var.get()]

    def _section_source(self) -> str:
        return SECTION_SOURCE_MAP[self.section_source_var.get()]

    def _section_type(self) -> str:
        return SECTION_TYPE_MAP[self.section_type_var.get()]

    def _require_module(self, key: str) -> None:
        if not self._enabled(key):
            raise ValueError(f"Modulo desactivado: {MODULE_NAME_BY_KEY[key]}")

    def refresh_variable_lists(self) -> None:
        try:
            p = self._resolve_file()
            if not p.exists():
                return
            df = load_drillholes_csv(p)
            nums = list_numeric_columns(df)
            cats = list_categorical_columns(df)
            self.color_by_combo["values"] = nums
            self.value_col_combo["values"] = nums
            self.domain_combo["values"] = [""] + cats
            if nums and self.color_by_var.get() not in nums:
                self.color_by_var.set(nums[0])
            if nums and self.value_col_var.get() not in nums:
                self.value_col_var.set(nums[0])
            self.calibrate_section_slider(df)
            self._log(f"Variables: {len(nums)} numericas / {len(cats)} categoricas")
        except Exception as exc:  # noqa: BLE001
            self._log(f"No se pudieron refrescar variables: {exc}")

    def calibrate_section_slider(self, df=None) -> None:
        if df is None:
            p = self._resolve_file()
            if not p.exists():
                return
            df = load_drillholes_csv(p)
        orth_col = "x" if self._section_type() == "longitudinal" else "y"
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

    def _save_df(self, df, default_name: str) -> None:
        if df is None:
            messagebox.showinfo("Exportacion", "No hay datos para exportar")
            return
        path = filedialog.asksaveasfilename(
            title="Guardar archivo",
            initialdir=str(self._data_folder()),
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
            messagebox.showinfo("Exportacion", "No hay reporte estadistico")
            return
        path = filedialog.asksaveasfilename(
            title="Guardar reporte",
            initialdir=str(self._data_folder()),
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

    def _build_block_pipeline(self, df):
        value_col = self.value_col_var.get().strip()
        value_factor = self._get_float(self.value_factor_var, "factor-ley")
        if value_col in df.columns and value_factor != 1.0:
            df = df.copy()
            df[value_col] = df[value_col].astype(float) * value_factor

        composites_df = composite_drillholes(
            df,
            value_col=value_col,
            composite_length=self._get_float(self.composite_length_var, "longitud-composito"),
        )
        block_df = build_regular_block_model(
            composites_df,
            value_col=value_col,
            cell_size=(
                self._get_float(self.block_dx_var, "dx"),
                self._get_float(self.block_dy_var, "dy"),
                self._get_float(self.block_dz_var, "dz"),
            ),
            padding=(
                self._get_float(self.pad_x_var, "px"),
                self._get_float(self.pad_y_var, "py"),
                self._get_float(self.pad_z_var, "pz"),
            ),
            power=self._get_float(self.idw_power_var, "potencia-idw"),
            search_radius=self._get_float(self.search_radius_var, "radio-busqueda"),
            max_samples=self._get_int(self.max_samples_var, "max-samples"),
        )
        return composites_df, block_df

    def run_selected_view(self) -> None:
        try:
            self._save_enabled_modules()
            self.last_composites_df = None
            self.last_block_df = None
            self.last_section_df = None
            self.last_stats_text = ""

            file_path = self._resolve_file()
            if not file_path.exists():
                raise FileNotFoundError(f"No existe el archivo: {file_path}")

            df = load_drillholes_csv(file_path)
            df = filter_by_domain(
                df,
                domain_col=self.domain_col_var.get().strip() or None,
                domain_values=self._domain_values(),
            )
            if df.empty:
                raise ValueError("No hay datos despues de filtrar dominio")

            mode = self._mode()
            section_type = self._section_type()
            section_center = self._get_float(self.section_center_var, "centro-seccion", allow_empty=True)
            section_width = self._get_float(self.section_width_var, "ancho-seccion")

            if mode == "drillholes":
                self._require_module("geology_estimation")
                section_meta = None
                if self.show_section_window_var.get():
                    _, section_meta = extract_section(df, section_type=section_type, center=section_center, width=section_width)
                show_drillholes(
                    df,
                    color_by=self.color_by_var.get().strip() or None,
                    point_size=self._get_float(self.point_size_var, "tamano-punto"),
                    show_traces=self.show_traces_var.get(),
                    trace_width=self._get_float(self.trace_width_var, "ancho-traza"),
                    section_meta=section_meta,
                )
                self._log("Vista sondajes ejecutada")
                return

            if mode == "blocks":
                self._require_module("geology_estimation")
                composites_df, block_df = self._build_block_pipeline(df)
                self.last_composites_df = composites_df
                self.last_block_df = block_df

                if self.report_stats_var.get():
                    value_col = self.value_col_var.get().strip()
                    report = compare_composites_vs_blocks(composites_df, block_df, value_col=value_col)
                    self.last_stats_text = format_stats_report(report, value_col=value_col)
                    self._log(self.last_stats_text)

                section_meta = None
                if self.show_section_window_var.get():
                    _, section_meta = extract_section(block_df, section_type=section_type, center=section_center, width=section_width)

                show_block_model(
                    block_df,
                    value_col=self.value_col_var.get().strip(),
                    point_size=max(self._get_float(self.block_dx_var, "dx"), self._get_float(self.block_dy_var, "dy")) * 0.6,
                    section_meta=section_meta,
                )
                self._log("Vista bloques ejecutada")
                return

            if self._section_source() == "blocks":
                self._require_module("geology_estimation")
                composites_df, source_df = self._build_block_pipeline(df)
                self.last_composites_df = composites_df
                self.last_block_df = source_df
                color_by = self.value_col_var.get().strip()
                title = "Proyecto Vulcano - Seccion de Bloques"
            else:
                self._require_module("geology_estimation")
                source_df = df
                color_by = self.color_by_var.get().strip() or None
                title = "Proyecto Vulcano - Seccion de Sondajes"

            section_df, meta = extract_section(source_df, section_type=section_type, center=section_center, width=section_width)
            self.last_section_df = section_df
            show_section_2d(section_df, meta, color_by=color_by, title=title)
            self._log(f"Vista seccion ejecutada ({len(section_df)} puntos)")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            self._log(f"ERROR: {exc}")


def _open_principal(config: dict, initial_file: str) -> None:
    win = tk.Toplevel()
    VulcanoMainWindow(win, config=config, initial_file=initial_file)


def launch_main_interface(initial_file: str = "data/example_drillholes.csv") -> None:
    root = tk.Tk()
    config = load_user_config()

    if not config.get("setup_completed", False):
        wizard = SetupWizard(root, config)
        if not wizard.show_modal():
            root.destroy()
            return

    StartupWindow(root, config=config, on_open_env=_open_principal, initial_file=initial_file)
    root.mainloop()


def main() -> None:
    launch_main_interface()


if __name__ == "__main__":
    main()
