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
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow
import json
import pyqtgraph as pg
import numpy as np
import copy, time

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
from GUI.errorHandler import CustomMessageBox

class PlotWorker(QObject):
    finished = pyqtSignal(tuple)  # (z_data, w_data)

    def __init__(self, beam, wavelength, q_value, optical_system, n=1):
        super().__init__()
        self.beam = beam
        self.wavelength = wavelength
        self.q_value = q_value
        self.optical_system = optical_system
        self.n = n

    def run(self):
        z_data, w_data, z_setup = self.beam.propagate_through_system(
            self.wavelength, self.q_value, self.optical_system, n=self.n
        )
        self.finished.emit((z_data, w_data, z_setup))

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
        
        # Timer vor allen Verbindungen initialisieren
        self._live_plot_update_timer = QtCore.QTimer(self)
        self._live_plot_update_timer.setSingleShot(True)
        self._live_plot_update_timer.setInterval(10)
        self._live_plot_update_timer.timeout.connect(self.update_live_plot)

        self._property_update_timer = QtCore.QTimer(self)
        self._property_update_timer.setSingleShot(True)
        self._property_update_timer.setInterval(100)
        self._property_update_timer.timeout.connect(self.update_rayleigh)

        self._property_fields = {}
        # Create instances of helper classes
        self.res = Resonator()
        self.beam = Beam()
        self.modematcher = ModematcherParameters(self)
        self.lib = Libraries(self)
        self.item_selector_modematcher = ItemSelector(self)
        self.item_selector_res = ItemSelector(self)
        self.matrices = Matrices()
        self.beam = Beam()
        self.vc = ValueConverter()
        self.action = Action()

        self.vlines = []
        self.curves = []
        self.z_setup = 0
        
        self._plot_busy = False

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
        self.ui.buttonScaleToSetup.clicked.connect(lambda: self.scale_visible_setup())
        self.update_live_plot()
        
        # Live update for the optical system plot
        #self.setupList.itemChanged.connect(lambda _: self.update_live_plot_delayed())
        self.setupList.model().rowsInserted.connect(lambda *_: self.update_live_plot_delayed())
        self.setupList.model().rowsRemoved.connect(lambda *_: self.update_live_plot_delayed())
        self.setupList.model().modelReset.connect(lambda *_: self.update_live_plot_delayed())
        self.setupList.model().rowsMoved.connect(lambda *args: self.update_live_plot_delayed())
        
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
        self.plotWidget.getViewBox().sigXRangeChanged.connect(self.update_plot_for_visible_range)
        self.plotWidget.hideButtons()

    def closeEvent(self, event):
        try:
            self.setupList.model().modelReset.disconnect()
            self.setupList.itemChanged.disconnect()
            self.setupList.model().rowsInserted.disconnect()
            self.setupList.model().rowsRemoved.disconnect()
        except Exception:
            pass
        super().closeEvent(event)
        
    def make_field_slot(self, key, comp):
        def slot():
            self.save_properties_to_component(comp)
            self.update_live_plot_delayed()
        return slot
    
    def make_checkbox_slot(self, key, comp):
        def slot():
            self.save_properties_to_component(comp)
            self.update_live_plot_delayed()
        return slot
    
    def update_rayleigh_delayed(self):
        self._property_update_timer.stop()
        self._property_update_timer.start()

    def update_live_plot_delayed(self):
        if hasattr(self, '_live_plot_update_timer'):
            self._live_plot_update_timer.stop()
            self._live_plot_update_timer.start()

    def update_rayleigh(self):
        try:
            wavelength = self.vc.convert_to_float(self._property_fields["Wavelength"].text(), self)
            waist_tan = self.vc.convert_to_float(self._property_fields["Waist radius tangential"].text(), self)
            waist_sag = self.vc.convert_to_float(self._property_fields["Waist radius sagittal"].text(), self)
            n = 1
            rayleigh_sag = self.beam.rayleigh_length(wavelength, waist_sag, n)
            rayleigh_tan = self.beam.rayleigh_length(wavelength, waist_tan, n)
            value_str_sag = self.vc.convert_to_nearest_string(rayleigh_sag, self)
            value_str_tan = self.vc.convert_to_nearest_string(rayleigh_tan, self)
            self._property_fields["Rayleigh range sagittal"].setText(value_str_sag)
            self._property_fields["Rayleigh range tangential"].setText(value_str_tan)
        except Exception:
            self._property_fields["Rayleigh range sagittal"].setText("")
            self._property_fields["Rayleigh range tangential"].setText("")

        self._property_update_timer.timeout.connect(self.update_rayleigh)    
    
    def show_properties(self, properties: dict, component=None):
        layout: QtWidgets.QGridLayout = self.propertyLayout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._property_fields = {}

        row = 1

        # IS_ROUND Checkbox als erstes Feld (immer anzeigen)
        is_round_value = float(properties.get("IS_ROUND", 0.0))
        label = QtWidgets.QLabel("Spherical:")
        layout.addWidget(label, row, 0)
        checkbox = QtWidgets.QCheckBox()
        checkbox.setChecked(is_round_value == 1.0)
        layout.addWidget(checkbox, row, 1, 1, 2)
        self._property_fields["IS_ROUND"] = checkbox
        checkbox.stateChanged.connect(self.make_checkbox_slot("IS_ROUND", component))
        row += 1

        is_beam = "Wavelength" in properties

        # Gemeinsame Properties (wie Wavelength)
        common_props = ["Wavelength", "Refractive index", "Length", "Thickness"]
        for key in common_props:
            if key in properties:
                label = QtWidgets.QLabel(key + ":")
                value = properties[key]
                if key == "Refractive index":
                    value_str = str(value)  # Kein ValueConverter!
                else:
                    value_str = self.vc.convert_to_nearest_string(value, self)
                field = QtWidgets.QLineEdit(value_str)
                layout.addWidget(label, row, 0)
                layout.addWidget(field, row, 1, 1, 2)
                self._property_fields[key] = field
                field.textChanged.connect(self.make_field_slot(key, component))
                if key == "Wavelength":
                    field.textChanged.connect(self.update_rayleigh_delayed)
                if not field.isReadOnly():
                    field.textChanged.connect(self.update_live_plot_delayed)
                row += 1

        # Jetzt die Header-Zeile für sagittal/tangential
        empty_label = QtWidgets.QLabel("")
        sag_label = QtWidgets.QLabel("Sagittal")
        tan_label = QtWidgets.QLabel("Tangential")
        layout.addWidget(empty_label, row, 0)
        layout.addWidget(sag_label, row, 1)
        layout.addWidget(tan_label, row, 2)
        row += 1

        # Sagittal/Tangential Paare
        paired_props = [
            ("Waist radius sagittal", "Waist radius tangential", "Waist radius"),
            ("Waist position sagittal", "Waist position tangential", "Waist position"),
            ("Rayleigh range sagittal", "Rayleigh range tangential", "Rayleigh range"),
            ("Focal length sagittal", "Focal length tangential", "Focal length"),
            ("Radius of curvature sagittal", "Radius of curvature tangential", "Radius of curvature"),
            ("A sagittal", "A tangential", "A"),
            ("B sagittal", "B tangential", "B"),
            ("C sagittal", "C tangential", "C"),
            ("D sagittal", "D tangential", "D")
        ]

        for sag_key, tan_key, display_name in paired_props:
            if sag_key in properties or tan_key in properties:
                label = QtWidgets.QLabel(display_name + ":")
                layout.addWidget(label, row, 0)
                # Sagittal Field
                if sag_key in properties:
                    # ValueConverter für die Anzeige nutzen
                    value_str = self.vc.convert_to_nearest_string(properties.get(sag_key, 0), self)
                    field_sag = QtWidgets.QLineEdit(value_str)
                    if "Rayleigh range" in sag_key:
                        field_sag.setReadOnly(True)
                        field_sag.setStyleSheet("background-color: #eee; color: #888;")
                    layout.addWidget(field_sag, row, 1)
                    self._property_fields[sag_key] = field_sag
                    field_sag.textChanged.connect(self.make_field_slot(sag_key, component))
                    if "Waist radius" in sag_key:
                        field_sag.textChanged.connect(self.update_rayleigh_delayed)
                    if not field_sag.isReadOnly():
                        field_sag.textChanged.connect(self.update_live_plot_delayed)
                # Tangential Field
                if tan_key in properties:
                    # ValueConverter für die Anzeige nutzen
                    value_str = self.vc.convert_to_nearest_string(properties.get(tan_key, 0), self)
                    field_tan = QtWidgets.QLineEdit(value_str)
                    if "Rayleigh range" in tan_key:
                        field_tan.setReadOnly(True)
                        field_tan.setStyleSheet("background-color: #eee; color: #888;")
                    layout.addWidget(field_tan, row, 2)
                    self._property_fields[tan_key] = field_tan
                    field_tan.textChanged.connect(self.make_field_slot(tan_key, component))
                    if "Waist radius" in tan_key:
                        field_tan.textChanged.connect(self.update_rayleigh_delayed)
                    if not field_tan.isReadOnly():
                        field_tan.textChanged.connect(self.update_live_plot_delayed)

                row += 1

        # Andere Properties (wie IS_ROUND)
        for key, value in properties.items():
            if key not in [item for sublist in paired_props for item in sublist[:2]] and key not in common_props and key.upper() != "IS_ROUND":
                label = QtWidgets.QLabel(key + ":")
                layout.addWidget(label, row, 0)
                str_value = self.vc.convert_to_nearest_string(value, self)
                field = QtWidgets.QLineEdit(str_value)
                layout.addWidget(field, row, 1, 1, 2)
                self._property_fields[key] = field
                field.textChanged.connect(self.make_field_slot(key, component))
                if isinstance(field, QtWidgets.QLineEdit) and not field.isReadOnly():
                    field.textChanged.connect(self.update_live_plot_delayed)
                
                row += 1

        # Initial Rayleigh-Berechnung
        if is_beam:
            self.update_rayleigh()

        # Spacer am Ende
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer, row, 0, 1, 3)
        
        # ...nachdem alle Felder angelegt wurden...
        
        self._syncing_focal_curvature = False

        def make_focal_to_curvature_slot(focal_key, curvature_key):
            def slot():
                if self._syncing_focal_curvature:
                    return
                try:
                    self._syncing_focal_curvature = True
                    focal_field = self._property_fields.get(focal_key)
                    curvature_field = self._property_fields.get(curvature_key)
                    if focal_field and curvature_field:
                        focal_val = self.vc.convert_to_float(focal_field.text(), self)
                        if focal_val is not None:
                            curvature_val = 2 * focal_val
                            curvature_field.setText(self.vc.convert_to_nearest_string(curvature_val, self))
                finally:
                    self._syncing_focal_curvature = False
            return slot

        def make_curvature_to_focal_slot(curvature_key, focal_key):
            def slot():
                if self._syncing_focal_curvature:
                    return
                try:
                    self._syncing_focal_curvature = True
                    curvature_field = self._property_fields.get(curvature_key)
                    focal_field = self._property_fields.get(focal_key)
                    if curvature_field and focal_field:
                        curvature_val = self.vc.convert_to_float(curvature_field.text(), self)
                        if curvature_val is not None:
                            focal_val = curvature_val / 2
                            focal_field.setText(self.vc.convert_to_nearest_string(focal_val, self))
                finally:
                    self._syncing_focal_curvature = False
            return slot

        # Verbinde die Felder
        if "Focal length sagittal" in self._property_fields and "Radius of curvature sagittal" in self._property_fields:
            self._property_fields["Focal length sagittal"].textChanged.connect(
                make_focal_to_curvature_slot("Focal length sagittal", "Radius of curvature sagittal")
            )
            self._property_fields["Radius of curvature sagittal"].textChanged.connect(
                make_curvature_to_focal_slot("Radius of curvature sagittal", "Focal length sagittal")
            )

        if "Focal length tangential" in self._property_fields and "Radius of curvature tangential" in self._property_fields:
            self._property_fields["Focal length tangential"].textChanged.connect(
                make_focal_to_curvature_slot("Focal length tangential", "Radius of curvature tangential")
            )
            self._property_fields["Radius of curvature tangential"].textChanged.connect(
                make_curvature_to_focal_slot("Radius of curvature tangential", "Focal length tangential")
            )

        def update_spherical_state():
            is_spherical = self._property_fields["IS_ROUND"].isChecked()
            for sag_key, tan_key, _ in paired_props:
                if tan_key in self._property_fields and sag_key in self._property_fields:
                    tan_field = self._property_fields[tan_key]
                    sag_field = self._property_fields[sag_key]
                    if is_spherical:
                        # Synchronisieren und ausgrauen
                        tan_field.setReadOnly(True)
                        tan_field.setStyleSheet("background-color: #eee; color: #888;")
                        tan_field.setText(sag_field.text())
                    else:
                        # Wieder bearbeitbar machen
                        tan_field.setReadOnly(False)
                        tan_field.setStyleSheet("")

        # Beim Ändern der Checkbox ausführen
        self._property_fields["IS_ROUND"].stateChanged.connect(update_spherical_state)

        # Beim Ändern eines Sagittal-Feldes synchronisieren, falls Spherical aktiv
        for sag_key, tan_key, _ in paired_props:
            if sag_key in self._property_fields and tan_key in self._property_fields:
                def make_sync_slot(sag_field, tan_field):
                    def slot():
                        if self._property_fields["IS_ROUND"].isChecked():
                            tan_field.setText(sag_field.text())
                    return slot
                self._property_fields[sag_key].textChanged.connect(
                    make_sync_slot(self._property_fields[sag_key], self._property_fields[tan_key])
                )

        # Initial synchronisieren, falls Spherical gesetzt ist
        update_spherical_state()
    
    def on_component_clicked(self, item):
        """Handle clicks on components in the setup list."""
        # 1. Create deep copy of new component
        clicked_component = copy.deepcopy(item.data(QtCore.Qt.UserRole))
        if not isinstance(clicked_component, dict):
            return
        
        # 2. Save current field values if we have a last component
        if hasattr(self, "_last_component_item") and self._last_component_item is not None:
            last_component = self._last_component_item.data(QtCore.Qt.UserRole)
            if isinstance(last_component, dict):
                # Create a deep copy of the last component
                updated_last = copy.deepcopy(last_component)
                
                # Update with current field values
                if hasattr(self, '_property_fields'):
                    for key, field in self._property_fields.items():
                        if key not in updated_last["properties"]:
                            continue
                            
                        if isinstance(field, QtWidgets.QLineEdit):
                            try:
                                if key == "Refractive index":
                                    value = float(field.text())
                                else:
                                    value = self.vc.convert_to_float(field.text(), self)
                            except:
                                value = field.text()
                            updated_last["properties"][key] = value
                        elif isinstance(field, QtWidgets.QCheckBox):
                            updated_last["properties"][key] = 1.0 if field.isChecked() else 0.0
                
                # Update the last item with its modified copy
                self._last_component_item.setData(QtCore.Qt.UserRole, updated_last)
        
        # 3. Show new component
        self.labelType.setText(clicked_component.get("type", ""))
        self.labelName.setText(clicked_component.get("name", ""))
        self.labelManufacturer.setText(clicked_component.get("manufacturer", ""))
        
        # 4. Update properties display
        props = clicked_component.get("properties", {})
        self.show_properties(props, clicked_component)
        
        # 5. Store current item as last item and update its data
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

    def build_optical_system_from_setup_list(self, mode="sagittal"):
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

            if ctype == "GENERIC" and component.get("name", "").strip().lower() == "beam":
                continue
            elif ctype == "GENERIC" and component.get("name", "").strip().lower() == "propagation":
                length = props.get("Length", 0.1)
                n = props.get("Refractive index", 1)
                optical_system.append((self.matrices.free_space, (length, n)))
            elif ctype == "LENS" or ctype == "GENERIC" and component.get("name", "").strip().lower() == "lens":
                if mode == "sagittal":
                    f = props.get("Focal length sagittal", 0.1)
                else:
                    f = props.get("Focal length tangential", 0.1)
                optical_system.append((self.matrices.lens, (f,)))
            elif ctype == "MIRROR" or ctype == "GENERIC" and component.get("name", "").strip().lower() == "Mirror":
                if mode == "sagittal":
                    r = props.get("CURVATURE_SAGITTAL")
                else:
                    r = props.get("CURVATURE_TANGENTIAL")
                optical_system.append(self.matrices.curved_mirror_sagittal, (r,))
                
            # ... weitere Typen ...
        return optical_system
    
    def update_live_plot(self):
        if self._plot_busy:
            return
        self._plot_busy = True
        try:
            if hasattr(self, '_live_plot_update_timer'):
                self._live_plot_update_timer.stop()
            beam_item = self.setupList.currentItem()
            if beam_item is None:
                beam_item = self.setupList.item(0)
            if beam_item is not None and hasattr(self, '_property_fields'):
                updated_beam = self.save_properties_to_component(beam_item.data(QtCore.Qt.UserRole))
                if updated_beam is not None:
                    beam_item.setData(QtCore.Qt.UserRole, updated_beam)
            optical_system_sag = self.build_optical_system_from_setup_list(mode="sagittal")
            optical_system_tan = self.build_optical_system_from_setup_list(mode="tangential")
            # Hole Startparameter aus dem Beam (immer an Position 0)
            beam_item = self.setupList.item(0)
            beam = beam_item.data(QtCore.Qt.UserRole)
            props = beam.get("properties", {})
            wavelength = props.get("Wavelength", 514E-9)
            waist_sag = props.get("Waist radius sagittal", 1E-3)
            waist_tan = props.get("Waist radius tangential", 1E-3)
            waist_pos_sag = props.get("Waist position sagittal", 0.0)
            waist_pos_tan = props.get("Waist position tangential", 0.0)
            n = 1  # Optional: aus Beam-Properties holen
            try:
                self.plot_optical_system(
                    z_start_sag=waist_pos_sag,
                    z_start_tan=waist_pos_tan,
                    wavelength=wavelength,
                    waist_sag=waist_sag,
                    waist_tan=waist_tan,
                    n=n,
                    optical_system_sag=optical_system_sag,
                    optical_system_tan=optical_system_tan
                )
            except Exception:
                pass
        finally:
            self._plot_busy = False
    
    def save_properties_to_component(self, component):
        """Save current field values to the given component."""
        if not isinstance(component, dict) or "properties" not in component:
            return
            
        # Create a copy to modify
        updated = copy.deepcopy(component)
        
        for key, field in self._property_fields.items():
            # Skip if property doesn't belong to this component
            if key not in updated["properties"]:
                continue
                
            # Skip calculated fields
            if "Rayleigh range" in key:
                continue
                
            if isinstance(field, QtWidgets.QLineEdit):
                try:
                    if key == "Refractive index":
                        value = float(field.text())
                    else:
                        value = self.vc.convert_to_float(field.text(), self)
                except:
                    value = field.text()
                updated["properties"][key] = value
            elif isinstance(field, QtWidgets.QCheckBox):
                updated["properties"][key] = 1.0 if field.isChecked() else 0.0
        
        return updated
        
    def plot_optical_system_from_resonator(self, optical_system):
        self.plot_optical_system(optical_system=optical_system)
        
    def plot_optical_system(self, z_start_sag, z_start_tan, wavelength, waist_sag, waist_tan, n, optical_system_sag, optical_system_tan):
        # Speichere die aktuellen Parameter als Attribute, damit update_plot_for_visible_range darauf zugreifen kann
        
        self.wavelength = wavelength
        self.waist_sag = waist_sag
        self.waist_tan = waist_tan
        self.waist_pos_sag = z_start_sag
        self.waist_pos_tan = z_start_tan
        self.n = n
        self.optical_system_sag = optical_system_sag
        self.optical_system_tan = optical_system_tan
        
        self.curve_sag = None
        self.curve_tan = None
        self.plotWidget.clear()

        # Initialplot (z.B. gesamter Bereich)
        z_min, z_max = self.plotWidget.getViewBox().viewRange()[0]
        if not np.isfinite(z_min) or not np.isfinite(z_max) or z_min == z_max:
            # Fallback: Bereich aus optischem System bestimmen
            z_min = 0
            z_max = sum([p[1][0] for p in optical_system_sag if hasattr(p[0], "__func__") and p[0].__func__ is self.matrices.free_space.__func__])

        self.update_plot_for_visible_range(z_min, z_max)

    def update_plot_for_visible_range(self, *args, **kwargs):
        z_min, z_max = self.plotWidget.getViewBox().viewRange()[0]
        if not np.isfinite(z_min) or not np.isfinite(z_max) or z_min == z_max:
            z_min = 0
            z_max = sum([p[1][0] for p in self.optical_system_sag
                        if hasattr(p[0], "__func__") and p[0].__func__ is self.matrices.free_space.__func__])
        
        n_points = 500
        self.z_visible = np.linspace(z_min, z_max, n_points)

        # Hole gespeicherte Parameter
        wavelength = self.wavelength
        waist_sag = self.waist_sag
        waist_tan = self.waist_tan
        waist_pos_sag = self.waist_pos_sag
        waist_pos_tan = self.waist_pos_tan
        n = self.n
        optical_system_sag = self.optical_system_sag
        optical_system_tan = self.optical_system_tan
        self.vb = self.plotWidget.getViewBox()

        # q-Werte berechnen und propagieren
        q_sag = self.beam.q_value(waist_pos_sag, waist_sag, wavelength, n)
        q_tan = self.beam.q_value(waist_pos_tan, waist_tan, wavelength, n)
        try:
            self.z_data, self.w_sag_data, z_setup = self.beam.propagate_through_system(wavelength, q_sag, optical_system_sag, self.z_visible, n_points, n=n)
            self.z_data, self.w_tan_data, z_setup = self.beam.propagate_through_system(wavelength, q_tan, optical_system_tan, self.z_visible, n_points, n=n)
            self.z_setup = z_setup
        except Exception:
            self.vb.setXRange(0, 1, padding=0.02)
            self.show_error()

        # Plot aktualisieren oder neu erstellen
        if not hasattr(self, "curve_sag") or self.curve_sag is None:
            self.plotWidget.clear()
            self.plotWidget.setBackground('w')
            self.plotWidget.addLegend()
            self.plotWidget.showGrid(x=True, y=True)
            self.plotWidget.setLabel('left', 'Waist radius', units='m', color='#333333')
            self.plotWidget.setLabel('bottom', 'z', units='m', color='#333333')
            self.plotWidget.setTitle("Gaussian Beam Propagation", color='#333333')
            axis_pen = pg.mkPen(color='#333333')
            self.plotWidget.getAxis('left').setTextPen(axis_pen)
            self.plotWidget.getAxis('bottom').setTextPen(axis_pen)
            self.plotWidget.setDefaultPadding(0.02)  # 2% padding around the plot
            region = LinearRegionItem(values=[0, z_setup], orientation='vertical', brush=(100, 100, 255, 30), movable=False)
            self.plotWidget.addItem(region)

            self.curve_sag = self.plotWidget.plot(self.z_data, self.w_sag_data, pen=pg.mkPen('r', width=1), name="Sagittal")
            self.curve_tan = self.plotWidget.plot(self.z_data, self.w_tan_data, pen=pg.mkPen('b', width=1), name="Tangential")
        else:
            self.curve_sag.setData(self.z_data, self.w_sag_data)
            self.curve_tan.setData(self.z_data, self.w_tan_data)

        # → Immer X-Achse an sichtbaren Bereich anpassen
        current_range = self.plotWidget.getViewBox().viewRange()[0]
        if abs(current_range[0] - z_min) > 1e-9 or abs(current_range[1] - z_max) > 1e-9:
            try:
                self.vb.sigXRangeChanged.disconnect(self.update_plot_for_visible_range)
            except TypeError:
                pass
            self.vb.sigXRangeChanged.connect(self.update_plot_for_visible_range)
            self.vb.setXRange(0, z_setup, padding=0.02)

        # Vertikale Linien aktualisieren
        for vline in getattr(self, "vlines", []):
            self.plotWidget.removeItem(vline)
        self.vlines = []
        z_element = 0
        for idx, (element, param) in enumerate(optical_system_sag):
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                z_element += param[0]
            else:
                vline = pg.InfiniteLine(pos=z_element, angle=90, pen=pg.mkPen(width=2, color="#FF0000"))
                self.plotWidget.addItem(vline)
                self.vlines.append(vline)
                
    def scale_visible_setup(self):
        """
        Skaliert die sichtbaren Setup-Elemente auf die aktuelle Ansicht.
        """
        self.vb = self.plotWidget.getViewBox()
        self.vb.setXRange(0, self.z_setup, padding=0.02)
        xRange = self.vb.viewRange()[0]
        visible_mask = (self.z_data >= xRange[0]) & (self.z_data <= xRange[1])
        visible_y = self.w_sag_data[visible_mask]
        if len(visible_y) > 0:
            ymax = visible_y.max()
            self.vb.setYRange(0, ymax, padding=0.1)
                
    def show_error(self):
        msg = CustomMessageBox(self, "Error", "You do not have permission to exceed this limit!", "..\\GRay-CAD-2\\assets\\error.gif")
        msg.exec()