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
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog, QTreeWidgetItem, QLabel, QLineEdit, QHBoxLayout
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
        self.modematcher = ModematcherParameters()
        self.lib = Libraries()
        self.item_selector_res = ItemSelector(self)
        self.item_selector_modematcher = ItemSelector(self)
        self.matrices = Matrices()
        self.beam = Beam()
        self.vc = ValueConverter()
        self.action = Action()

        # Variable, um den Kontext zu speichern
        self.current_context = None
        self.wavelength = None  # Default wavelength

        # Set application window icon
        self.setWindowIcon(QIcon(path.abspath(path.join(path.dirname(__file__), 
                         "../../assets/TaskbarIcon.png"))))

        # Load the main UI from .ui file
        self.ui = uic.loadUi(path.abspath(path.join(path.dirname(__file__), "../assets/mainwindow.ui")), self)
        old_component_tree = self.findChild(QtWidgets.QTreeWidget, "componentTree")
        old_setup_tree = self.findChild(QtWidgets.QTreeWidget, "setupTree")

        # Neue ersetzen (mit gleichem parent und objectName)
        self.componentTree = ComponentTree(self)
        self.componentTree.setObjectName("componentTree")

        self.setupTree = SetupTree(self)
        self.setupTree.setObjectName("setupTree")

        # Im Layout ersetzen
        parent1 = old_component_tree.parent()
        parent2 = old_setup_tree.parent()

        layout1 = parent1.layout()
        layout2 = parent2.layout()

        layout1.replaceWidget(old_component_tree, self.componentTree)
        layout2.replaceWidget(old_setup_tree, self.setupTree)

        # Alte verstecken oder löschen
        old_component_tree.deleteLater()
        old_setup_tree.deleteLater()

        # Connect menu items to their respective handlers
        self.ui.action_Open.triggered.connect(lambda: self.action.action_open(self))
        self.ui.action_Save.triggered.connect(lambda: self.action.action_save(self))
        self.ui.action_Save_as.triggered.connect(lambda: self.action.action_save_as(self))
        self.ui.action_Exit.triggered.connect(lambda: self.action.action_exit(self))
        self.ui.action_Tips_and_tricks.triggered.connect(lambda: self.action.action_tips_and_tricks(self))
        self.ui.action_About.triggered.connect(lambda: self.action.action_about(self))
        
        # Connect library menu item to the library window
        self.ui.action_Library.triggered.connect(self.lib.open_library_window)
        
        # Connect buttons to their respective handlers
        self.ui.action_Cavity_Designer.triggered.connect(lambda: self.action.handle_build_resonator(self))
        self.ui.action_Modematcher.triggered.connect(lambda: self.action.handle_modematcher(self))

        #self.ui.pushButton_create_setup.clicked.connect(self.new_setup)
        #self.ui.pushButton_delete_setup.clicked.connect(self.delete_setup)

        # Default optical system
        self.current_optical_system = [
            (self.matrices.free_space, (0.1, 1)),
            (self.matrices.lens, 0.05),
            (self.matrices.free_space, (0.3, 1))
        ]

        self.plot_optical_system()

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
        self.res.setup_generated.connect(self.plot_optical_system_from_resonator)
        
        # Set up the component tree
        self.load_component_tree_from_folder("Library")
        self.componentTree.itemClicked.connect(self.on_component_clicked)
        self.setupTree.itemClicked.connect(self.on_setup_item_clicked)

    def show_properties(self, properties: dict):
        # Bestehende Einträge entfernen
        layout: QtWidgets.QGridLayout = self.propertyLayout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Neue Einträge einfügen
        for row, (key, value) in enumerate(properties.items()):
            label = QtWidgets.QLabel(key + ":")
            if key.upper() == "IS_ROUND":
                checkbox = QtWidgets.QCheckBox()
                checkbox.setChecked(float(value) == 1.0)
                checkbox.setEnabled(True)
                layout.addWidget(label, row, 0)
                layout.addWidget(checkbox, row, 1)
            else:
                field = QtWidgets.QLineEdit(str(value))
                field.setReadOnly(False)
                field.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                layout.addWidget(label, row, 0)
                layout.addWidget(field, row, 1)
        # Vertical Spacer am Ende hinzufügen
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer, layout.rowCount(), 0, 1, 2)

    def on_component_clicked(self, item, column):
        component = item.data(0, QtCore.Qt.UserRole)
        if not isinstance(component, dict):
            return

        self.labelType.setText(component.get("type", ""))
        self.labelName.setText(component.get("name", ""))
        self.labelManufacturer.setText(component.get("manufacturer", ""))
        props = component.get("properties", {})
        self.show_properties(props)

    def on_setup_item_clicked(self, item, column):
        component = item.data(0, QtCore.Qt.UserRole)
        if not isinstance(component, dict):
            return
        
        self.labelType.setText(component.get("type", ""))
        self.labelName.setText(component.get("name", ""))
        self.labelManufacturer.setText(component.get("manufacturer", ""))
        props = component.get("properties", {})
        self.show_properties(props)

    def load_component_tree_from_folder(self, folder_path):
        self.componentTree.clear()

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                filepath = os.path.join(folder_path, filename)
                with open(filepath, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        continue

                # Verwende 'name' in JSON oder den Dateinamen als Titel
                group_name = data.get("name") or filename.replace(".json", "")
                top_item = QTreeWidgetItem([group_name])
                self.componentTree.addTopLevelItem(top_item)

                for component in data.get("components", []):
                    name = component.get("name", "Unnamed Component")
                    item = QTreeWidgetItem([name])
                    item.setData(0, QtCore.Qt.UserRole, component)
                    top_item.addChild(item)

                top_item.setExpanded(True)

    def plot_optical_system_from_resonator(self, optical_system):
        self.plot_optical_system(optical_system=optical_system)
        
    def plot_optical_system(self, z_start=0, wavelength=0.514E-6, beam_radius=1E-3, n=1, optical_system=None):
        """
        Plots the given optical system.
        """
        if optical_system is None:
            optical_system = self.current_optical_system
            self.wavelength = wavelength
        
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

class ComponentTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.setHeaderHidden(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

    def mimeData(self, items):
        mime = QtCore.QMimeData()
        component = items[0].data(0, QtCore.Qt.UserRole)
        if component:
            mime.setData("application/x-component", QtCore.QByteArray(json.dumps(component).encode()))
        return mime

class SetupTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setHeaderHidden(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-component") or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-component") or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Externer Drop (aus ComponentTree)
        if event.mimeData().hasFormat("application/x-component") and event.source() != self:
            data = event.mimeData().data("application/x-component")
            component = json.loads(bytes(data).decode())
            item = QtWidgets.QTreeWidgetItem([component.get("name", "Unnamed")])
            item.setData(0, QtCore.Qt.UserRole, component)
            self.addTopLevelItem(item)
            event.acceptProposedAction()
        else:
            # Internes Verschieben: Standardverhalten nutzen
            super().dropEvent(event)