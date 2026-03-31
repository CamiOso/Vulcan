import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QToolBar, QStatusBar, QFileDialog,
    QDockWidget, QTextEdit, QTreeView, QWidget, QVBoxLayout, QLabel, QPushButton, QSlider,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox, QGroupBox, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProyectoVulcano - GUI")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self):
        # Menú principal
        menubar = self.menuBar()
        archivo_menu = menubar.addMenu("Archivo")
        ejecutar_menu = menubar.addMenu("Ejecutar")
        ayuda_menu = menubar.addMenu("Ayuda")

        abrir_action = QAction("Abrir CSV", self)
        abrir_action.triggered.connect(self.open_file)
        archivo_menu.addAction(abrir_action)
        archivo_menu.addAction(QAction("Salir", self))

        ejecutar_menu.addAction(QAction("Correr vista seleccionada", self))
        ayuda_menu.addAction(QAction("Información de la app", self))

        # Toolbars
        toolbar = QToolBar("Main Toolbar")
        toolbar.addAction(abrir_action)
        toolbar.addAction(QAction("Guardar", self))
        toolbar.addAction(QAction("Zoom In", self))
        toolbar.addAction(QAction("Zoom Out", self))
        toolbar.addAction(QAction("Undo", self))
        toolbar.addAction(QAction("Redo", self))
        self.addToolBar(toolbar)

        # Status Bar
        status = QStatusBar()
        status.showMessage("Listo")
        self.setStatusBar(status)

        # Panel principal con todos los widgets fusionados
        main_panel = QWidget()
        main_layout = QHBoxLayout()

        # Left panel: Navigator
        left_panel = QVBoxLayout()
        nav_group = QGroupBox("Navigator")
        nav_layout = QVBoxLayout()
        nav_layout.addWidget(QTreeView())
        nav_group.setLayout(nav_layout)
        left_panel.addWidget(nav_group)

        # Layer Chooser
        layer_group = QGroupBox("Layer Chooser")
        layer_layout = QVBoxLayout()
        layer_layout.addWidget(QTextEdit())
        layer_group.setLayout(layer_layout)
        left_panel.addWidget(layer_group)

        main_layout.addLayout(left_panel)

        # Center panel: viewport and controls
        center_panel = QVBoxLayout()
        viewport = QWidget()
        layout = QVBoxLayout()
        self.viewport_label = QLabel("Visualización 3D/2D (mockup)")
        layout.addWidget(self.viewport_label)

        # Configuración de parámetros y tabla deben estar en el centro
        # Crear widgets una sola vez
        if not hasattr(self, 'col_selector'):
            self.col_selector = QComboBox()
            self.col_selector.addItem("(Cargar CSV primero)")
        if not hasattr(self, 'table'):
            self.table = QTableWidget()

        config_box = QGroupBox("Configuración de parámetros")
        config_layout = QFormLayout()
        config_layout.addRow("Columna de variable:", self.col_selector)
        self.length_spin = QSpinBox()
        self.length_spin.setRange(1, 100)
        self.length_spin.setValue(5)
        config_layout.addRow("Longitud compositado:", self.length_spin)
        self.neighbors_spin = QSpinBox()
        self.neighbors_spin.setRange(1, 20)
        self.neighbors_spin.setValue(5)
        config_layout.addRow("Vecinos IDW:", self.neighbors_spin)
        config_box.setLayout(config_layout)
        # Mejor visualización: usar un layout horizontal para parámetros y tabla
        param_table_layout = QHBoxLayout()
        param_table_layout.addWidget(config_box)
        param_table_layout.addWidget(self.table)
        layout.addLayout(param_table_layout)

        try:
            import pyqtgraph as pg
            self.plot_widget = pg.PlotWidget()
            layout.addWidget(self.plot_widget)
        except ImportError:
            self.plot_widget = None

        btn_composite = QPushButton("Compositar")
        btn_composite.clicked.connect(self.on_composite)
        layout.addWidget(btn_composite)
        btn_idw = QPushButton("Estimar IDW")
        btn_idw.clicked.connect(self.on_idw)
        layout.addWidget(btn_idw)
        btn_drillholes = QPushButton("Visualizar Drillholes")
        btn_drillholes.clicked.connect(self.on_drillholes)
        layout.addWidget(btn_drillholes)
        btn_export = QPushButton("Exportar")
        btn_export.clicked.connect(self.on_export)
        layout.addWidget(btn_export)
        btn_report = QPushButton("Reporte")
        btn_report.clicked.connect(self.on_report)
        layout.addWidget(btn_report)
        btn_hist = QPushButton("Histograma")
        btn_hist.clicked.connect(self.on_hist)
        layout.addWidget(btn_hist)
        btn_box = QPushButton("Boxplot")
        btn_box.clicked.connect(self.on_boxplot)
        layout.addWidget(btn_box)
        layout.addWidget(QSlider(Qt.Horizontal))
        viewport.setLayout(layout)
        center_panel.addWidget(viewport)

        main_layout.addLayout(center_panel, stretch=2)

        # Right panel: Command Chooser
        right_panel = QVBoxLayout()
        cmd_group = QGroupBox("Command Chooser")
        cmd_layout = QVBoxLayout()
        cmd_layout.addWidget(QTextEdit())
        cmd_group.setLayout(cmd_layout)
        right_panel.addWidget(cmd_group)

        main_layout.addLayout(right_panel)

        # Bottom panel: Message Window
        bottom_panel = QVBoxLayout()
        msg_group = QGroupBox("Message Window")
        msg_layout = QVBoxLayout()
        msg_layout.addWidget(QTextEdit())
        msg_group.setLayout(msg_layout)
        bottom_panel.addWidget(msg_group)

        # Wrap everything in a vertical layout
        wrapper = QVBoxLayout()
        wrapper.addLayout(main_layout)
        wrapper.addLayout(bottom_panel)
        main_panel.setLayout(wrapper)
        self.setCentralWidget(main_panel)

    def on_composite(self):
        # Compositar usando composite_by_length
        try:
            from proyectovulcano.geology_estimation import CompositingTools
            if self.df is not None:
                value_col = self.col_selector.currentText()
                length = self.length_spin.value()
                result = CompositingTools.composite_by_length(self.df, length, value_col)
                self.table.setRowCount(len(result))
                self.table.setColumnCount(len(result.columns))
                self.table.setHorizontalHeaderLabels(result.columns)
                # Bloque limpio, sin caracteres invisibles
                # Bloque limpio, sin caracteres invisibles
                # Bloque limpio, sin caracteres invisibles
                for i, row in result.iterrows():
                    for j, val in enumerate(row):
                        item = QTableWidgetItem(str(val))
                        self.table.setItem(i, j, item)
            else:
                QMessageBox.warning(self, "Compositar", "Primero cargue un archivo CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Compositado fallido: {e}")

    def on_idw(self):
        # Estimar IDW para el primer punto
        try:
            from proyectovulcano.geology_estimation import EstimationMethods
            if self.df is not None:
                value_col = self.col_selector.currentText()
                # Usar el primer punto del dataframe
                x = self.df["x"].iloc[0]
                y = self.df["y"].iloc[0]
                z = self.df["z"].iloc[0]
                estimate = EstimationMethods.idw(self.df, x, y, z, value_col)
                self.table.setRowCount(1)
                self.table.setColumnCount(2)
                self.table.setHorizontalHeaderLabels(["Punto", "Estimación IDW"])
                self.table.setItem(0, 0, QTableWidgetItem(f"({x}, {y}, {z})"))
                self.table.setItem(0, 1, QTableWidgetItem(str(estimate)))
            else:
                QMessageBox.warning(self, "IDW", "Primero cargue un archivo CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Estimación IDW fallida: {e}")

    def on_drillholes(self):
        # Visualización 3D de pozos usando PyVista, asegurando tipos correctos
        try:
            if self.df is not None:
                from proyectovulcano.viewer import show_drillholes
                color_by = self.col_selector.currentText() if self.col_selector.currentText() in self.df.columns else None
                df = self.df.copy()
                # Convertir x, y, z a float64
                for col in ["x", "y", "z"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").astype('float64')
                # Convertir columna de color a float64 si es posible, si no, a str básica
                if color_by and color_by in df.columns:
                    try:
                        df[color_by] = pd.to_numeric(df[color_by], errors="coerce").astype('float64')
                    except Exception:
                        df[color_by] = df[color_by].astype(str)
                show_drillholes(df, color_by=color_by)
            else:
                QMessageBox.warning(self, "Visualización", "Primero cargue un archivo CSV.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Visualización 3D fallida: {e}")

    def on_export(self):
        # Exportar la tabla actual a CSV
        try:
            file_name, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", "exported.csv", "CSV Files (*.csv)")
            if file_name:
                # Extraer datos de la tabla
                rows = self.table.rowCount()
                cols = self.table.columnCount()
                headers = [self.table.horizontalHeaderItem(j).text() for j in range(cols)]
                data = []
                for i in range(rows):
                    row = []
                    for j in range(cols):
                        item = self.table.item(i, j)
                        row.append(item.text() if item else "")
                    data.append(row)
                import pandas as pd
                df = pd.DataFrame(data, columns=headers)
                df.to_csv(file_name, index=False)
                QMessageBox.information(self, "Exportar", f"Datos exportados a {file_name}")
            else:
                QMessageBox.warning(self, "Exportar", "No se seleccionó archivo.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Exportación fallida: {e}")

    def on_report(self):
        QMessageBox.information(self, "Reporte", "Función de reporte (mockup)")

    def on_hist(self):
        QMessageBox.information(self, "Histograma", "Función de histograma (mockup)")

    def on_boxplot(self):
        QMessageBox.information(self, "Boxplot", "Función de boxplot (mockup)")

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Abrir archivo CSV", "", "CSV Files (*.csv)")
        if file_name:
            try:
                try:
                    self.df = pd.read_csv(file_name)
                except UnicodeDecodeError:
                    self.df = pd.read_csv(file_name, encoding="latin1")
                self.col_selector.clear()
                self.col_selector.addItems(self.df.columns)
                self.table.setRowCount(len(self.df))
                self.table.setColumnCount(len(self.df.columns))
                self.table.setHorizontalHeaderLabels(self.df.columns)
                for i, row in self.df.iterrows():
                    for j, val in enumerate(row):
                        item = QTableWidgetItem(str(val))
                        self.table.setItem(i, j, item)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo: {e}")

def run_qt_gui():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    return app.exec_()

if __name__ == "__main__":
    run_qt_gui()
