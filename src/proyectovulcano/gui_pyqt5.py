from __future__ import annotations

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QFileDialog, QMessageBox, QTabWidget, QFrame, QScrollArea,
    QTextEdit, QGroupBox, QGridLayout, QSplitter, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor

from .io import load_drillholes_csv, filter_by_domain, list_numeric_columns, list_categorical_columns
from .compositing import composite_drillholes
from .block_model import build_regular_block_model
from .stats import compare_composites_vs_blocks, format_stats_report
from .viewer import show_drillholes, show_block_model, show_section_2d
from .sections import extract_section
from .config import load_user_config, save_user_config


class VulcanoMainWindow(QMainWindow):
    """Main window for Proyecto Vulcano v0.3.0 (PyQt5)"""

    def __init__(self):
        super().__init__()
        self.config = load_user_config()
        self.config.setdefault("data_folder", "data")
        self.config.setdefault("enabled_modules", [])
        
        # Data state
        self.current_data = None
        self.last_composites_df = None
        self.last_block_df = None
        
        self.setWindowTitle("Proyecto Vulcano v0.3.0 - Modelado de Minería")
        self.setGeometry(100, 100, 1600, 1000)
        self.setStyle('Fusion')
        
        # Set application font
        font = QFont("Segoe UI", 9)
        QApplication.instance().setFont(font)
        
        self._build_ui()
        self._load_example_data()

    def _build_ui(self) -> None:
        """Build the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Top toolbar with file selection
        layout.addWidget(self._build_data_section())
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: parameters
        left_panel = QScrollArea()
        left_panel.setWidget(self._build_parameters_panel())
        left_panel.setWidgetResizable(True)
        left_panel.setMaximumWidth(400)
        
        # Right panel: log and controls
        right_panel = QVBoxLayout()
        right_panel.addWidget(self._build_visualization_panel())
        right_panel.addWidget(self._build_log_panel())
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter, 1)
        
        # Bottom status bar
        layout.addWidget(self._build_status_bar())

    def _build_data_section(self) -> QGroupBox:
        """Build data selection section"""
        group = QGroupBox("📁 DATOS - Archivo CSV")
        layout = QHBoxLayout()
        
        self.file_input = QLineEdit()
        self.file_input.setText("data/example_drillholes.csv")
        layout.addWidget(QLabel("CSV:"), 0)
        layout.addWidget(self.file_input, 1)
        
        browse_btn = QPushButton("  Examinar")
        browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(browse_btn)
        
        example_btn = QPushButton("  Ejemplo")
        example_btn.clicked.connect(self._use_example)
        layout.addWidget(example_btn)
        
        reload_btn = QPushButton("  Recargar")
        reload_btn.clicked.connect(self._reload_data)
        layout.addWidget(reload_btn)
        
        group.setLayout(layout)
        return group

    def _build_parameters_panel(self) -> QWidget:
        """Build parameters panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Visualization type
        viz_group = QGroupBox("📊 VISUALIZACIÓN")
        viz_layout = QGridLayout()
        viz_layout.addWidget(QLabel("Tipo:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Sondajes 3D", "Modelo de Bloques", "Seccion 2D"])
        self.mode_combo.currentTextChanged.connect(self._on_viz_type_changed)
        viz_layout.addWidget(self.mode_combo, 0, 1)
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)
        
        # Drillholes parameters
        drillholes_group = QGroupBox("⛏️ SONDAJES 3D")
        dh_layout = QGridLayout()
        
        dh_layout.addWidget(QLabel("Colorear por:"), 0, 0)
        self.color_combo = QComboBox()
        self.color_combo.addItem("au")
        dh_layout.addWidget(self.color_combo, 0, 1)
        
        dh_layout.addWidget(QLabel("Tamaño punto:"), 1, 0)
        self.point_size_spin = QDoubleSpinBox()
        self.point_size_spin.setValue(8.0)
        self.point_size_spin.setRange(1.0, 50.0)
        dh_layout.addWidget(self.point_size_spin, 1, 1)
        
        self.show_traces_check = QCheckBox("Mostrar trazas")
        self.show_traces_check.setChecked(True)
        dh_layout.addWidget(self.show_traces_check, 2, 0)
        
        dh_layout.addWidget(QLabel("Ancho traza:"), 2, 1)
        self.trace_width_spin = QDoubleSpinBox()
        self.trace_width_spin.setValue(3.0)
        self.trace_width_spin.setRange(0.1, 10.0)
        dh_layout.addWidget(self.trace_width_spin, 2, 2)
        
        drillholes_group.setLayout(dh_layout)
        layout.addWidget(drillholes_group)
        
        # Blocks parameters
        blocks_group = QGroupBox("🧱 BLOQUES - Parámetros IDW")
        blocks_layout = QGridLayout()
        
        blocks_layout.addWidget(QLabel("Long. composito (m):"), 0, 0)
        self.composite_length_spin = QDoubleSpinBox()
        self.composite_length_spin.setValue(10.0)
        self.composite_length_spin.setRange(1.0, 100.0)
        blocks_layout.addWidget(self.composite_length_spin, 0, 1)
        
        blocks_layout.addWidget(QLabel("Dx (m):"), 1, 0)
        self.block_dx_spin = QDoubleSpinBox()
        self.block_dx_spin.setValue(10.0)
        blocks_layout.addWidget(self.block_dx_spin, 1, 1)
        
        blocks_layout.addWidget(QLabel("Dy (m):"), 1, 2)
        self.block_dy_spin = QDoubleSpinBox()
        self.block_dy_spin.setValue(10.0)
        blocks_layout.addWidget(self.block_dy_spin, 1, 3)
        
        blocks_layout.addWidget(QLabel("Dz (m):"), 2, 0)
        self.block_dz_spin = QDoubleSpinBox()
        self.block_dz_spin.setValue(5.0)
        blocks_layout.addWidget(self.block_dz_spin, 2, 1)
        
        blocks_layout.addWidget(QLabel("IDW Power:"), 2, 2)
        self.idw_power_spin = QDoubleSpinBox()
        self.idw_power_spin.setValue(2.0)
        self.idw_power_spin.setRange(1.0, 4.0)
        blocks_layout.addWidget(self.idw_power_spin, 2, 3)
        
        blocks_layout.addWidget(QLabel("Radio búsqueda (m):"), 3, 0)
        self.search_radius_spin = QDoubleSpinBox()
        self.search_radius_spin.setValue(25.0)
        blocks_layout.addWidget(self.search_radius_spin, 3, 1)
        
        blocks_layout.addWidget(QLabel("Max muestras:"), 3, 2)
        self.max_samples_spin = QSpinBox()
        self.max_samples_spin.setValue(12)
        self.max_samples_spin.setRange(4, 64)
        blocks_layout.addWidget(self.max_samples_spin, 3, 3)
        
        self.report_stats_check = QCheckBox("Reporte estadístico")
        self.report_stats_check.setChecked(True)
        blocks_layout.addWidget(self.report_stats_check, 4, 0)
        
        blocks_group.setLayout(blocks_layout)
        layout.addWidget(blocks_group)
        
        # Sections parameters
        sections_group = QGroupBox("📈 SECCIONES 2D")
        sections_layout = QGridLayout()
        
        sections_layout.addWidget(QLabel("Fuente:"), 0, 0)
        self.section_source_combo = QComboBox()
        self.section_source_combo.addItems(["Sondajes", "Bloques"])
        sections_layout.addWidget(self.section_source_combo, 0, 1)
        
        sections_layout.addWidget(QLabel("Tipo:"), 0, 2)
        self.section_type_combo = QComboBox()
        self.section_type_combo.addItems(["Longitudinal", "Transversal"])
        sections_layout.addWidget(self.section_type_combo, 0, 3)
        
        sections_layout.addWidget(QLabel("Centro:"), 1, 0)
        self.section_center_spin = QDoubleSpinBox()
        self.section_center_spin.setRange(-1000.0, 1000.0)
        sections_layout.addWidget(self.section_center_spin, 1, 1)
        
        sections_layout.addWidget(QLabel("Ancho (m):"), 1, 2)
        self.section_width_spin = QDoubleSpinBox()
        self.section_width_spin.setValue(20.0)
        sections_layout.addWidget(self.section_width_spin, 1, 3)
        
        sections_group.setLayout(sections_layout)
        layout.addWidget(sections_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _build_visualization_panel(self) -> QGroupBox:
        """Build visualization panel"""
        group = QGroupBox("🎯 CONTROLES")
        layout = QVBoxLayout()
        
        # Main execute button
        execute_btn = QPushButton("▶ EJECUTAR VISUALIZACIÓN")
        execute_btn.setMinimumHeight(50)
        execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        execute_btn.clicked.connect(self._run_visualization)
        layout.addWidget(execute_btn)
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        export_comp_btn = QPushButton("📊 Composites")
        export_comp_btn.clicked.connect(self._export_composites)
        export_layout.addWidget(export_comp_btn)
        
        export_blocks_btn = QPushButton("🧱 Bloques")
        export_blocks_btn.clicked.connect(self._export_blocks)
        export_layout.addWidget(export_blocks_btn)
        
        export_stats_btn = QPushButton("📈 Stats")
        export_stats_btn.clicked.connect(self._export_stats)
        export_layout.addWidget(export_stats_btn)
        
        layout.addLayout(export_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        return group

    def _build_log_panel(self) -> QGroupBox:
        """Build log panel"""
        group = QGroupBox("📝 LOG - Mensajes de progreso")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        clear_btn = QPushButton("Limpiar Log")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)
        
        group.setLayout(layout)
        return group

    def _build_status_bar(self) -> QFrame:
        """Build status bar"""
        frame = QFrame()
        frame.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-top: 1px solid #ccc;")
        layout = QHBoxLayout()
        
        self.status_label = QLabel("✓ Proyecto Vulcano listo")
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.info_label = QLabel("v0.3.0 (PyQt5)")
        layout.addWidget(self.info_label)
        
        frame.setLayout(layout)
        return frame

    def _log(self, message: str) -> None:
        """Add message to log"""
        self.log_text.append(f"• {message}")
        self.status_label.setText(message[:100])

    def _browse_file(self) -> None:
        """Browse for CSV file"""
        file, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar CSV", "data",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if file:
            self.file_input.setText(file)
            self._reload_data()

    def _use_example(self) -> None:
        """Use example data"""
        self.file_input.setText("data/example_drillholes.csv")
        self._reload_data()

    def _reload_data(self) -> None:
        """Reload data from CSV"""
        try:
            file_path = Path(self.file_input.text())
            if not file_path.exists():
                self._log(f"❌ Archivo no encontrado: {file_path}")
                return
            
            self.current_data = load_drillholes_csv(file_path)
            if self.current_data is None or self.current_data.empty:
                self._log("❌ El archivo está vacío")
                return
            
            # Update comboboxes with available columns
            numeric_cols = list_numeric_columns(self.current_data)
            self.color_combo.clear()
            self.color_combo.addItems(numeric_cols)
            
            self._log(f"✓ Datos cargados: {len(self.current_data)} muestras")
        except Exception as e:
            self._log(f"❌ Error al cargar datos: {e}")

    def _on_viz_type_changed(self, text: str) -> None:
        """Handle visualization type change"""
        self._log(f"Tipo de visualización: {text}")

    def _run_visualization(self) -> None:
        """Run the selected visualization"""
        if self.current_data is None:
            QMessageBox.warning(self, "Error", "Carga un archivo CSV primero")
            return
        
        mode = self.mode_combo.currentText()
        self._log(f"Ejecutando: {mode}...")
        
        try:
            if mode == "Sondajes 3D":
                show_drillholes(
                    self.current_data,
                    color_by=self.color_combo.currentText(),
                    point_size=self.point_size_spin.value(),
                    show_traces=self.show_traces_check.isChecked(),
                    trace_width=self.trace_width_spin.value()
                )
            elif mode == "Modelo de Bloques":
                composites_df = composite_drillholes(
                    self.current_data,
                    value_col=self.color_combo.currentText(),
                    composite_length=self.composite_length_spin.value()
                )
                blocks_df = build_regular_block_model(
                    composites_df,
                    grid_size=(self.block_dx_spin.value(), self.block_dy_spin.value(), self.block_dz_spin.value()),
                    value_col=self.color_combo.currentText(),
                    power=self.idw_power_spin.value(),
                    search_radius=self.search_radius_spin.value(),
                    max_samples=self.max_samples_spin.value()
                )
                
                self.last_composites_df = composites_df
                self.last_block_df = blocks_df
                
                if self.report_stats_check.isChecked():
                    report = compare_composites_vs_blocks(composites_df, blocks_df, value_col=self.color_combo.currentText())
                    stats_text = format_stats_report(report, value_col=self.color_combo.currentText())
                    self._log(stats_text)
                
                show_block_model(blocks_df, value_col=self.color_combo.currentText())
            elif mode == "Seccion 2D":
                source = self.current_data
                source_name = "Sondajes"
                
                if self.section_source_combo.currentText() == "Bloques" and self.last_block_df is not None:
                    source = self.last_block_df
                    source_name = "Bloques"
                
                section_df, meta = extract_section(
                    source,
                    section_type=self.section_type_combo.currentText().lower(),
                    center=self.section_center_spin.value() if self.section_center_spin.value() != 0 else None,
                    width=self.section_width_spin.value()
                )
                
                show_section_2d(section_df, meta, color_by=self.color_combo.currentText(), title=f"Sección {source_name}")
            
            self._log(f"✓ {mode} ejecutada exitosamente")
        except Exception as e:
            self._log(f"❌ Error: {e}")
            QMessageBox.critical(self, "Error de ejecución", str(e))

    def _export_composites(self) -> None:
        """Export composites to CSV"""
        if self.current_data is None:
            QMessageBox.warning(self, "Error", "Carga un archivo CSV primero")
            return
        
        try:
            composites_df = composite_drillholes(
                self.current_data,
                value_col=self.color_combo.currentText(),
                composite_length=self.composite_length_spin.value()
            )
            
            output_path = Path("outputs") / "composites_pyqt.csv"
            output_path.parent.mkdir(exist_ok=True)
            composites_df.to_csv(output_path, index=False)
            
            self._log(f"✓ Composites exportados: {output_path}")
        except Exception as e:
            self._log(f"❌ Error al exportar: {e}")

    def _export_blocks(self) -> None:
        """Export blocks to CSV"""
        if self.current_data is None:
            QMessageBox.warning(self, "Error", "Carga un archivo CSV primero")
            return
        
        try:
            if self.last_block_df is None:
                composites_df = composite_drillholes(
                    self.current_data,
                    value_col=self.color_combo.currentText(),
                    composite_length=self.composite_length_spin.value()
                )
                blocks_df = build_regular_block_model(
                    composites_df,
                    grid_size=(self.block_dx_spin.value(), self.block_dy_spin.value(), self.block_dz_spin.value()),
                    value_col=self.color_combo.currentText(),
                    power=self.idw_power_spin.value(),
                    search_radius=self.search_radius_spin.value(),
                    max_samples=self.max_samples_spin.value()
                )
            else:
                blocks_df = self.last_block_df
            
            output_path = Path("outputs") / "blocks_pyqt.csv"
            output_path.parent.mkdir(exist_ok=True)
            blocks_df.to_csv(output_path, index=False)
            
            self._log(f"✓ Bloques exportados: {output_path}")
        except Exception as e:
            self._log(f"❌ Error al exportar: {e}")

    def _export_stats(self) -> None:
        """Export statistics report"""
        if self.current_data is None:
            QMessageBox.warning(self, "Error", "Carga un archivo CSV primero")
            return
        
        try:
            composites_df = composite_drillholes(
                self.current_data,
                value_col=self.color_combo.currentText(),
                composite_length=self.composite_length_spin.value()
            )
            blocks_df = build_regular_block_model(
                composites_df,
                grid_size=(self.block_dx_spin.value(), self.block_dy_spin.value(), self.block_dz_spin.value()),
                value_col=self.color_combo.currentText(),
                power=self.idw_power_spin.value(),
                search_radius=self.search_radius_spin.value(),
                max_samples=self.max_samples_spin.value()
            )
            
            report = compare_composites_vs_blocks(composites_df, blocks_df, value_col=self.color_combo.currentText())
            stats_text = format_stats_report(report, value_col=self.color_combo.currentText())
            
            output_path = Path("outputs") / "stats_pyqt.txt"
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, "w") as f:
                f.write(stats_text)
            
            self._log(f"✓ Estadísticas exportadas: {output_path}")
        except Exception as e:
            self._log(f"❌ Error al exportar: {e}")

    def _load_example_data(self) -> None:
        """Load example data on startup"""
        QTimer.singleShot(500, self._reload_data)


def launch_pyqt5_interface() -> None:
    """Launch the PyQt5 GUI application"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = VulcanoMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch_pyqt5_interface()
