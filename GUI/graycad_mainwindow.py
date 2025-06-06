#Python 3.10.2
# -*- coding: utf-8 -*-
"""
@author: Jens Gumm, TU Darmstadt, LQO-Group
Main window implementation for the GRay-CAD application.
Handles the primary UI and window management.
"""

# PyQt5 imports for GUI components
from PyQt5 import uic
from pyqtgraph import *
from os import path
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem
import json
import pyqtgraph as pg
import numpy as np

# Custom module imports
from src_resonator.resonators import Resonator
from src_libraries.libraries import Libraries
from src_libraries.select_items import ItemSelector
from src_modematcher.modematcher_parameters import ModematcherParameters
from src_physics.beam import Beam
from src_physics.matrices import Matrices
from src_physics.value_converter import ValueConverter
from GUI.actions import Action
from GUI.setupList import SetupList
from GUI.componentList import ComponentList

class MainWindow(QMainWindow):
    """
    Main application window class.
    Handles the primary user interface and window management.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the main window and set up the UI components.
        Creates instances of Resonator and Matrices classes.
        Sets up menu actions and button connections.
        """
        super().__init__(*args, **kwargs)
        
        # Create instances of helper classes
        self.res = Resonator()
        self.beam = Beam()
        self.modematcher = ModematcherParameters(self)
        self.lib = Libraries(self)
        self.item_selector_modematcher = ItemSelector(self)
        self.matrices = Matrices()
        self.beam = Beam()
        self.vc = ValueConverter()
        self.action = Action()

        # Variable, um den Kontext zu speichern
        self.current_context = None
        self.wavelength = None  # Default wavelength
        self._last_component_item = None

        # Set application window icon
        self.setWindowIcon(QIcon(path.abspath(path.join(path.dirname(__file__), 
                         "../../assets/TaskbarIcon.png"))))

        # Load the main UI from .ui file
        self.ui = uic.loadUi(path.abspath(path.join(path.dirname(__file__), "../assets/mainwindow.ui")), self)

        # Connect menu items to their respective handlers
        self.ui.action_Open.triggered.connect(lambda: self.action.action_open(self))
        self.ui.action_Save.triggered.connect(lambda: self.action.action_save(self))
        self.ui.action_Save_as.triggered.connect(lambda: self.action.action_save_as(self))
        self.ui.action_Exit.triggered.connect(lambda: self.action.action_exit(self))
        self.ui.action_Tips_and_tricks.triggered.connect(lambda: self.action.action_tips_and_tricks(self))
        self.ui.action_About.triggered.connect(lambda: self.action.action_about(self))

        # Connect library menu item to the library window
        self.ui.action_Library.triggered.connect(self.lib.open_library_window)
        
        # Plot from resonator setup
        self.res.setup_generated.connect(self.plot_optical_system_from_resonator)
        
        # Connect buttons to their respective handlers
        self.ui.action_Cavity_Designer.triggered.connect(lambda: self.action.handle_build_resonator(self))
        self.ui.action_Modematcher.triggered.connect(lambda: self.action.handle_modematcher(self))

        # Library and component list setup
        old_component_list = self.findChild(QtWidgets.QListWidget, "componentList")
        old_setup_list = self.findChild(QtWidgets.QListWidget, "setupList")

        self.componentList = ComponentList(self)
        self.componentList.setObjectName("componentList")
        self.setupList = SetupList(self)
        self.setupList.setObjectName("setupList")

        # Im Layout ersetzen
        parent1 = old_component_list.parent()
        parent2 = old_setup_list.parent()
        layout1 = parent1.layout()
        layout2 = parent2.layout()
        layout1.replaceWidget(old_component_list, self.componentList)
        layout2.replaceWidget(old_setup_list, self.setupList)
        old_component_list.deleteLater()
        old_setup_list.deleteLater()

        self.load_library_list_from_folder("Library")
        self.componentList.itemClicked.connect(self.on_component_clicked)
        self.setupList.itemClicked.connect(self.on_component_clicked)
        self.libraryList.itemClicked.connect(self.on_library_selected)

        #self.ui.pushButton_create_setup.clicked.connect(self.new_setup)
        #self.ui.pushButton_delete_setup.clicked.connect(self.delete_setup)

        # Connect buttons in the setupTree
        self.ui.buttonDeleteItem.clicked.connect(lambda: self.action.delete_selected_setup_item(self))
        self.ui.buttonMoveUp.clicked.connect(lambda: self.action.move_selected_setup_item_up(self))
        self.ui.buttonMoveDown.clicked.connect(lambda: self.action.move_selected_setup_item_down(self))
        self.ui.buttonAddComponent.clicked.connect(lambda: self.action.move_selected_component_to_setupList(self))
        self.update_live_plot()
        
        # Live update for the optical system plot
        self.setupList.itemChanged.connect(lambda _: self.update_live_plot())
        self.setupList.model().rowsInserted.connect(lambda *_: self.update_live_plot())
        self.setupList.model().rowsRemoved.connect(lambda *_: self.update_live_plot())
        self.setupList.model().modelReset.connect(lambda *_: self.update_live_plot())

        self.cursor_vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', width=1, style=Qt.DashLine))
        self.plotWidget.addItem(self.cursor_vline, ignoreBounds=True)
        self.cursor_vline.setZValue(100)  # Damit sie immer oben liegt

        def mouseMoved(evt):
            pos = evt
            if self.plotWidget.sceneBoundingRect().contains(pos):
                mousePoint = self.plotWidget.getViewBox().mapSceneToView(pos)
                z = mousePoint.x()
                self.cursor_vline.setPos(z)
                idx = np.searchsorted(self.z_data, z)
                if idx == 0:
                    z_val = self.z_data[0]
                    w_sag_val = self.w_sag_data[0]
                    w_tan_val = self.w_tan_data[0]
                elif idx == len(self.z_data):
                    z_val = self.z_data[-1]
                    w_sag_val = self.w_sag_data[-1]
                    w_tan_val = self.w_tan_data[-1]
                else:
                    # Interpolation zwischen idx-1 und idx
                    z0, z1 = self.z_data[idx-1], self.z_data[idx]
                    w0_sag, w1_sag = self.w_sag_data[idx-1], self.w_sag_data[idx]
                    w0_tan, w1_tan = self.w_tan_data[idx-1], self.w_tan_data[idx]
                    t = (z - z0) / (z1 - z0) if z1 != z0 else 0
                    z_val = z
                    w_sag_val = w0_sag + t * (w1_sag - w0_sag)
                    w_tan_val = w0_tan + t * (w1_tan - w0_tan)
                self.ui.label_z_position.setText(f"{self.vc.convert_to_nearest_string(z_val, self)}")
                self.ui.label_w_sag.setText(f"{self.vc.convert_to_nearest_string(w_sag_val, self)}")
                self.ui.label_w_tan.setText(f"{self.vc.convert_to_nearest_string(w_tan_val, self)}")
                #TODO
                self.ui.label_roc_sag.setText(f"{self.vc.convert_to_nearest_string(self.beam.radius_of_curvature(z_val, w_sag_val, self.wavelength))}")
                self.ui.label_roc_tan.setText(f"{self.vc.convert_to_nearest_string(self.beam.radius_of_curvature(z_val, w_tan_val, self.wavelength))}")
                
        # Connect signal to function
        self.plotWidget.scene().sigMouseMoved.connect(mouseMoved)
        
    
    def show_properties(self, properties: dict):
        layout: QtWidgets.QGridLayout = self.propertyLayout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        is_beam = "Wavelength" in properties and "Waist radius" in properties
        self._property_fields = {}

        # Verzögerungs-Timer für dynamische Updates
        self._property_update_timer = QtCore.QTimer(self)
        self._property_update_timer.setSingleShot(True)
        self._property_update_timer.setInterval(500)  # 500 ms

        def update_rayleigh_delayed():
            self._property_update_timer.stop()
            self._property_update_timer.start()

        def update_rayleigh():
            try:
                wavelength = self.vc.convert_to_float(self._property_fields["Wavelength"].text(), self)
                waist = self.vc.convert_to_float(self._property_fields["Waist radius"].text(), self)
                n = 1
                rayleigh = self.beam.rayleigh_length(wavelength, waist, n)
                value_str = self.vc.convert_to_nearest_string(rayleigh, self)
                self._property_fields["Rayleigh range"].setText(value_str)
            except Exception:
                self._property_fields["Rayleigh range"].setText("")

        self._property_update_timer.timeout.connect(update_rayleigh)

        for row, (key, value) in enumerate(properties.items()):
            label = QtWidgets.QLabel(key + ":")
            if key.upper() == "IS_ROUND":
                checkbox = QtWidgets.QCheckBox()
                checkbox.setChecked(float(value) == 1.0)
                checkbox.setEnabled(True)
                layout.addWidget(label, row, 0)
                layout.addWidget(checkbox, row, 1)
                self._property_fields[key] = checkbox
                # Live-Plot-Update für Checkbox
                checkbox.stateChanged.connect(lambda _: self.update_live_plot())
            elif is_beam and key == "Rayleigh range":
                field = QtWidgets.QLineEdit()
                field.setReadOnly(True)
                field.setStyleSheet("background-color: #eee; color: #888;")
                layout.addWidget(label, row, 0)
                layout.addWidget(field, row, 1)
                self._property_fields[key] = field
                # Kein Live-Plot nötig, da berechnet
            else:
                if isinstance(value, (int, float)):
                    value_str = self.vc.convert_to_nearest_string(value, self)
                else:
                    value_str = str(value)
                field = QtWidgets.QLineEdit(value_str)
                field.setReadOnly(False)
                field.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                layout.addWidget(label, row, 0)
                layout.addWidget(field, row, 1)
                self._property_fields[key] = field
                # Live-Plot-Update für LineEdit
                field.textChanged.connect(lambda _: self.update_live_plot())
                if is_beam and key in ("Wavelength", "Waist radius"):
                    field.textChanged.connect(update_rayleigh_delayed)

        # Initial berechnen
        if is_beam and "Rayleigh range" in self._property_fields:
            update_rayleigh()

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer, layout.rowCount(), 0, 1, 2)

    def on_component_clicked(self, item):
        # Vorherigen Eintrag speichern
        if hasattr(self, "_last_component_item") and self._last_component_item is not None:
            last_component = self._last_component_item.data(QtCore.Qt.UserRole)
            if isinstance(last_component, dict):
                self.save_properties_to_component(last_component)
        # Neuen Eintrag anzeigen
        component = item.data(QtCore.Qt.UserRole)
        if not isinstance(component, dict):
            return
        self.labelType.setText(component.get("type", ""))
        self.labelName.setText(component.get("name", ""))
        self.labelManufacturer.setText(component.get("manufacturer", ""))
        props = component.get("properties", {})
        self.show_properties(props)
        # Merke aktuellen Eintrag
        self._last_component_item = item

    def load_library_list_from_folder(self, folder_path):
        self.libraryList.clear()
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                lib_name = filename[:-5]  # Entfernt ".json"
                self.libraryList.addItem(lib_name)
    
    def on_library_selected(self, item):
        # Name der Bibliothek aus dem Listeneintrag
        lib_name = item.text()
        # Lade die entsprechende JSON-Datei
        lib_path = path.join("Library", lib_name + ".json")
        try:
            with open(lib_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            components = data.get("components", [])
            self.componentList.clear()
            for comp in components:
                name = comp.get("name", "Unnamed")
                list_item = QtWidgets.QListWidgetItem(name)
                list_item.setData(QtCore.Qt.UserRole, comp)
                self.componentList.addItem(list_item)
        except Exception as e:
            self.componentList.clear()
            QtWidgets.QMessageBox.warning(self, "Fehler", f"Bibliothek konnte nicht geladen werden:\n{e}")

    def build_optical_system_from_setup_list(self):
        """
        Baut das optische System aus den Komponenten in setupList.
        Gibt eine Liste von (matrix_funktion, parameter) zurück.
        """
        optical_system = []
        for i in range(self.setupList.count()):
            item = self.setupList.item(i)
            component = item.data(QtCore.Qt.UserRole)
            if not isinstance(component, dict):
                continue
            ctype = component.get("type", "").strip().upper()
            props = component.get("properties", {})

            # Beispiel für verschiedene Komponenten
            if ctype == "GENERIC" and component.get("name", "").strip().lower() == "beam":
                # Beam ist nur Startparameter, kein optisches Element
                continue
            elif ctype == "GENERIC" and component.get("name", "").strip().lower() == "propagation":
                length = props.get("Length", 0.1)
                n = props.get("refractive index", 1)
                optical_system.append((self.matrices.free_space, (length, n)))
            elif ctype == "GENERIC" and component.get("name", "").strip().lower() == "lens":
                f = props.get("Focal length", 0.1)
                optical_system.append((self.matrices.lens, (f,)))
            elif ctype == "GENERIC" and component.get("name", "").strip().lower() == "abcd":
                # ABCD-Matrix direkt
                A = props.get("A tangential", 1.0)
                B = props.get("B tangential", 0.0)
                C = props.get("C tangential", 0.0)
                D = props.get("D tangential", 1.0)
                optical_system.append((self.matrices.ABCD, (A, B, C, D)))
            # ... weitere Typen nach Bedarf ergänzen ...
            # Für Spiegel, Kristalle, etc. kannst du analog vorgehen

        return optical_system
    
    def update_live_plot(self):
        optical_system = self.build_optical_system_from_setup_list()
        # Hole Startparameter aus dem Beam (immer an Position 0)
        beam_item = self.setupList.item(0)
        beam = beam_item.data(QtCore.Qt.UserRole)
        props = beam.get("properties", {})
        wavelength = props.get("Wavelength", 514E-9)
        waist = props.get("Waist radius", 1E-3)
        waist_pos = props.get("Waist position", 0.0)
        n = 1  # Optional: aus Beam-Properties holen
        self.plot_optical_system(z_start=waist_pos, wavelength=wavelength, beam_radius=waist, n=n, optical_system=optical_system)
    
    def save_properties_to_component(self, component):
        for key, field in self._property_fields.items():
            if isinstance(field, QtWidgets.QLineEdit):
                text = field.text()
                try:
                    value = self.vc.convert_to_float(text, self)
                except Exception:
                    value = text
                component["properties"][key] = value
            elif isinstance(field, QtWidgets.QCheckBox):
                component["properties"][key] = 1.0 if field.isChecked() else 0.0
        
    def plot_optical_system_from_resonator(self, optical_system):
        self.plot_optical_system(optical_system=optical_system)
        
    def plot_optical_system(self, z_start, wavelength, beam_radius, n, optical_system):
        """
        Plots the given optical system.
        """
        self.wavelength = wavelength
        self.beam_radius = beam_radius
        self.z_start = z_start
        
        self.plotWidget.clear()
        self.z_data, self.w_sag_data = self.beam.propagate_through_system(
            wavelength, self.beam.q_value(z_start, beam_radius, wavelength, n), optical_system
        )
        self.w_tan_data = self.w_sag_data

        self.z_data = np.array(self.z_data)
        self.w_sag_data = np.array(self.w_sag_data)
        self.w_tan_data = np.array(self.w_tan_data)

        self.plotWidget.setBackground('w')
        self.plotWidget.addLegend()
        self.plotWidget.showGrid(x=True, y=True)

        self.plotWidget.setLabel('left', 'Waist radius', units='m', color='#333333')
        self.plotWidget.setLabel('bottom', 'z', units='m', color='#333333')
        self.plotWidget.setTitle("Gaussian Beam Propagation", color='#333333')
        axis_pen = pg.mkPen(color='#333333')
        self.plotWidget.getAxis('left').setTextPen(axis_pen)
        self.plotWidget.getAxis('bottom').setTextPen(axis_pen)

        self.plotWidget.plot(self.z_data, self.w_sag_data, pen=pg.mkPen(color='b', width=2))
        self.plotWidget.plot(self.z_data, self.w_tan_data, pen=pg.mkPen(color='r', width=2))

        z_element = 0
        for element, param in optical_system:
            # Prüfe, ob das Element KEINE Propagation ist
            if not (hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__):
                self.plotWidget.addLine(x=z_element, pen=pg.mkPen(color='#333333'))
            # Bei Propagation z_element erhöhen
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                z_element += param[0]