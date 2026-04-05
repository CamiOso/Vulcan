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
        env_btn = ttk.Button(env_frame, text="Abrir entorno", width=24, command=self._open_env)
        env_btn.pack(side="left")
        ttk.Button(env_frame, text="Guardar", command=self._save).pack(side="left", padx=8)

        self.log = ScrolledText(self.root, height=12)
        self.log.pack(fill="both", expand=True, pady=(10, 0))

    def _log(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

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
        self.initial_file = initial_file
        
        # Frame inferior para mensajes/logs
        self.log_frame = ttk.Frame(self.win)
        self.log_frame.pack(side="bottom", fill="x", padx=0, pady=0)
        self.log_visible = tk.BooleanVar(value=True)
        log_controls = ttk.Frame(self.log_frame)
        log_controls.pack(fill="x", padx=4, pady=2)
        ttk.Label(log_controls, text="Mensajes / Log").pack(side="left")
        ttk.Button(log_controls, text="Limpiar", command=self._clear_log, width=8).pack(side="right", padx=2)
        ttk.Checkbutton(log_controls, text="Mostrar", variable=self.log_visible, command=self._toggle_log).pack(side="right")
        self.log = ScrolledText(self.log_frame, height=8, state="normal")
        self.log.pack(fill="x", padx=8, pady=(0,4))

        # Inicializar todas las variables StringVar y BooleanVar
        self.file_var = tk.StringVar(value=initial_file)
        self.mode_var = tk.StringVar(value="Sondajes 3D")
        self.color_by_var = tk.StringVar(value="")
        self.value_col_var = tk.StringVar(value="au")
        self.value_factor_var = tk.StringVar(value="1.0")
        self.domain_col_var = tk.StringVar(value="")
        self.domain_values_var = tk.StringVar(value="")
        self.trace_width_var = tk.StringVar(value="3.0")
        self.block_dy_var = tk.StringVar(value="10.0")

        self.show_traces_var = tk.BooleanVar(value=True)
        self.show_section_window_var = tk.BooleanVar(value=False)
        self.report_stats_var = tk.BooleanVar(value=False)

        self.point_size_var = tk.StringVar(value="8.0")

        self.composite_length_var = tk.StringVar(value="10.0")
        self.block_dx_var = tk.StringVar(value="10.0")
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
            m["key"]: tk.BooleanVar(value=m["key"] in set(self.config.get("enabled_modules", [])))
            for m in MODULES
        }
        self.module_listbox = None
        self.module_detail = None

        self.color_by_combo = None
        self.value_col_combo = None
        self.domain_combo = None
        self.section_slider = None

        self.status_var = tk.StringVar(value="Listo")
        self.status_bar = ttk.Label(self.win, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.win.title("Proyecto Vulcano - Modelado de Minería")
        self.win.geometry("1400x900")

        self._build_menu()
        self._build_layout()
        self.refresh_variable_lists()

    def _clear_log(self):
        if hasattr(self, "log") and self.log is not None:
            self.log.delete("1.0", "end")

    def _toggle_log(self):
        if self.log_visible.get():
            self.log.pack(fill="x", padx=8, pady=(0,4))
        else:
            self.log.pack_forget()

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
        # Always resolve to 'data/example_drillholes.csv' for default
        if str(p) == "data/example_drillholes.csv":
            return Path("data/example_drillholes.csv").absolute()
        data_folder = self._data_folder()
        if str(data_folder).endswith("data") and str(p).startswith("data/"):
            return data_folder / Path(str(p)[5:])
        return data_folder / p

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

        # ============================================================
        # 1. DATOS - Seleccionar archivo CSV
        # ============================================================
        file_frame = ttk.LabelFrame(top, text="📁 DATOS - Seleccionar archivo CSV", padding=10)
        file_frame.pack(fill="x", pady=5)
        ttk.Entry(file_frame, textvariable=self.file_var, width=96).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(file_frame, text="Examinar", command=self._browse_file).grid(row=0, column=1, padx=2)
        ttk.Button(file_frame, text="Ejemplo", command=self._use_example).grid(row=0, column=2, padx=2)
        ttk.Button(file_frame, text="Recargar", command=self.refresh_variable_lists).grid(row=0, column=3, padx=2)
        file_frame.columnconfigure(0, weight=1)

        # ============================================================
        # 2. VISUALIZACIÓN - Elegir qué gráfico ver
        # ============================================================
        mode_frame = ttk.LabelFrame(top, text="📊 VISUALIZACIÓN - Elige qué ver", padding=10)
        mode_frame.pack(fill="x", pady=5)
        ttk.Label(mode_frame, text="Tipo de gráfico:").grid(row=0, column=0, sticky="w", padx=4)
        ttk.Combobox(mode_frame, textvariable=self.mode_var, values=list(VIEW_MAP.keys()), state="readonly", width=22).grid(row=0, column=1, padx=4, sticky="ew")
        
        ttk.Label(mode_frame, text="Variable:").grid(row=0, column=2, sticky="w", padx=4)
        self.value_col_combo = ttk.Combobox(mode_frame, textvariable=self.value_col_var, width=18)
        self.value_col_combo.grid(row=0, column=3, padx=4, sticky="ew")
        ttk.Button(mode_frame, text="Color por").grid(row=0, column=4, padx=2, sticky="ew")
        
        mode_frame.columnconfigure(1, weight=1)
        mode_frame.columnconfigure(3, weight=1)

        # ============================================================
        # 3. PARÁMETROS DINÁMICOS - Según el tipo de gráfico
        # ============================================================
        
        # 3a. PARAMS SONDAJES
        drillholes_frame = ttk.LabelFrame(top, text="⛏️ SONDAJES 3D - Parámetros", padding=10)
        drillholes_frame.pack(fill="x", pady=5)
        
        ttk.Label(drillholes_frame, text="Colorear por:").grid(row=0, column=0, sticky="w")
        self.color_by_combo = ttk.Combobox(drillholes_frame, textvariable=self.color_by_var, width=16)
        self.color_by_combo.grid(row=0, column=1, padx=4, sticky="ew")
        
        ttk.Label(drillholes_frame, text="Tamaño punto:").grid(row=0, column=2, sticky="w", padx=(20,0))
        ttk.Entry(drillholes_frame, textvariable=self.point_size_var, width=8).grid(row=0, column=3, padx=4)
        
        ttk.Checkbutton(drillholes_frame, text="Mostrar trazas", variable=self.show_traces_var).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(drillholes_frame, text="Ventana de sección", variable=self.show_section_window_var).grid(row=1, column=1, sticky="w")
        
        ttk.Label(drillholes_frame, text="Ancho traza:").grid(row=1, column=2, sticky="w", padx=(20,0))
        ttk.Entry(drillholes_frame, textvariable=self.trace_width_var, width=8).grid(row=1, column=3, padx=4)
        
        drillholes_frame.columnconfigure(1, weight=1)
        drillholes_frame.columnconfigure(3, weight=1)

        # 3b. PARAMS BLOQUES/IDW
        block_frame = ttk.LabelFrame(top, text="🧱 BLOQUES - Parámetros IDW", padding=10)
        block_frame.pack(fill="x", pady=5)
        
        ttk.Label(block_frame, text="Long. composito (m):").grid(row=0, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.composite_length_var, width=10).grid(row=0, column=1, padx=4)
        
        ttk.Label(block_frame, text="Tamaño bloque (dx/dy/dz):").grid(row=0, column=2, sticky="w", padx=(20,0))
        ttk.Entry(block_frame, textvariable=self.block_dx_var, width=8).grid(row=0, column=3, padx=2)
        ttk.Entry(block_frame, textvariable=self.block_dy_var, width=8).grid(row=0, column=4, padx=2)
        ttk.Entry(block_frame, textvariable=self.block_dz_var, width=8).grid(row=0, column=5, padx=4)
        
        ttk.Label(block_frame, text="IDW Power:").grid(row=1, column=0, sticky="w")
        ttk.Entry(block_frame, textvariable=self.idw_power_var, width=10).grid(row=1, column=1, padx=4)
        
        ttk.Label(block_frame, text="Radio búsqueda (m):").grid(row=1, column=2, sticky="w", padx=(20,0))
        ttk.Entry(block_frame, textvariable=self.search_radius_var, width=10).grid(row=1, column=3, padx=4)
        
        ttk.Label(block_frame, text="Max muestras:").grid(row=1, column=4, sticky="w", padx=2)
        ttk.Entry(block_frame, textvariable=self.max_samples_var, width=8).grid(row=1, column=5, padx=4)
        
        ttk.Checkbutton(block_frame, text="Reporte estadístico", variable=self.report_stats_var).grid(row=2, column=0, sticky="w")
        
        block_frame.columnconfigure(1, weight=1)
        block_frame.columnconfigure(3, weight=1)
        block_frame.columnconfigure(5, weight=1)

        # 3c. PARAMS SECCIONES
        section_frame = ttk.LabelFrame(top, text="📈 SECCIONES 2D - Parámetros", padding=10)
        section_frame.pack(fill="x", pady=5)
        
        ttk.Label(section_frame, text="Fuente:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(section_frame, textvariable=self.section_source_var, values=list(SECTION_SOURCE_MAP.keys()), state="readonly", width=12).grid(row=0, column=1, padx=4, sticky="ew")
        
        ttk.Label(section_frame, text="Tipo:").grid(row=0, column=2, sticky="w", padx=(20,0))
        ttk.Combobox(section_frame, textvariable=self.section_type_var, values=list(SECTION_TYPE_MAP.keys()), state="readonly", width=12).grid(row=0, column=3, padx=4, sticky="ew")
        
        ttk.Label(section_frame, text="Centro:").grid(row=0, column=4, sticky="w", padx=(20,0))
        ttk.Entry(section_frame, textvariable=self.section_center_var, width=10).grid(row=0, column=5, padx=4)
        
        ttk.Label(section_frame, text="Ancho (m):").grid(row=0, column=6, sticky="w", padx=2)
        ttk.Entry(section_frame, textvariable=self.section_width_var, width=10).grid(row=0, column=7, padx=4)
        
        section_frame.columnconfigure(1, weight=1)
        section_frame.columnconfigure(3, weight=1)
        section_frame.columnconfigure(5, weight=1)

        # ============================================================
        # 4. BOTÓN EJECUTAR - Grande y visible
        # ============================================================
        actions = ttk.Frame(self.win, padding=(0, 8, 0, 4))
        actions.pack(fill="x")
        run_btn = ttk.Button(actions, text="▶ EJECUTAR VISUALIZACIÓN", command=self.run_selected_view)
        run_btn.pack(side="left", padx=4, pady=4, fill="x", expand=True)

        # Botones secundarios
        ttk.Button(actions, text="Exportar composites", command=self.export_composites).pack(side="left", padx=2)
        ttk.Button(actions, text="Exportar bloques", command=self.export_blocks).pack(side="left", padx=2)
        ttk.Button(actions, text="Exportar estadísticas", command=self.export_stats).pack(side="left", padx=2)

        # ============================================================
        # LOG - Abajo (ya manejado en __init__)
        # ============================================================
        
        self._log("✓ Proyecto Vulcano listo")

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
        if hasattr(self, "log") and self.log is not None:
            self.log.insert("end", text + "\n")
            self.log.see("end")
        else:
            messagebox.showerror("Log error", text)
        # Actualizar barra de estado con el último mensaje breve
        if hasattr(self, "status_var") and self.status_var is not None:
            resumen = text.split("\n")[0]
            self.status_var.set(resumen[:120])

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
                self._log("No se pudo cargar el archivo de datos.")
                return
            df = load_drillholes_csv(p)
            if df is None or df.empty:
                self._log("El archivo de datos está vacío o no se pudo cargar.")
                return
            nums = list_numeric_columns(df)
            cats = list_categorical_columns(df)
            if self.color_by_combo is not None:
                self.color_by_combo["values"] = nums
            if self.value_col_combo is not None:
                self.value_col_combo["values"] = nums
            if self.domain_combo is not None:
                self.domain_combo["values"] = [""] + cats
            if nums and self.color_by_var.get() not in nums:
                self.color_by_var.set(nums[0])
            if nums and self.value_col_var.get() not in nums:
                self.value_col_var.set(nums[0])
            self.calibrate_section_slider(df)
            self._log(f"Variables: {len(nums)} numericas / {len(cats)} categoricas")
        except Exception as exc:
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
        if self.section_slider is not None:
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

    # Si ya está configurada la carpeta de datos, ir directamente a la ventana principal
    if config.get("data_folder"):
        root.withdraw()  # Ocultar ventana raíz
        _open_principal(config, initial_file)
        root.mainloop()
    else:
        # Si no hay carpeta configurada, mostrar StartupWindow
        StartupWindow(root, config=config, on_open_env=_open_principal, initial_file=initial_file)
        root.mainloop()


def main() -> None:
    launch_main_interface()


if __name__ == "__main__":
    main()
