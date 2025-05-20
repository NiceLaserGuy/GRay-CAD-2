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
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog
import pyqtgraph as pg
import numpy as np

# Custom module imports
from src_resonator.resonators import Resonator
from src_libraries.libraries import Libraries
from src_libraries.select_items import ItemSelector
from src_modematcher.modematcher_parameters import ModematcherParameters
from src_physics.beam import Beam

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

        # Variable, um den Kontext zu speichern
        self.current_context = None

        # Set application window icon
        self.setWindowIcon(QIcon(path.abspath(path.join(path.dirname(__file__), 
                         "../../assets/TaskbarIcon.png"))))

        # Load the main UI from .ui file
        self.ui = uic.loadUi(path.abspath(path.join(path.dirname(__file__), "../assets/mainwindow.ui")), self)

        # Connect menu items to their respective handlers
        self.ui.action_Open.triggered.connect(self.action_open)
        self.ui.action_Save.triggered.connect(self.action_save)
        self.ui.action_Save_as.triggered.connect(self.action_save_as)
        self.ui.action_Exit.triggered.connect(self.action_exit)
        # Connect library menu item to the library window
        self.ui.action_Library.triggered.connect(self.lib.open_library_window)
        
        # Connect buttons to their respective handlers
        self.ui.action_Cavity_Designer.triggered.connect(self.handle_build_resonator)
        self.ui.action_Modematcher.triggered.connect(self.handle_modematcher)

        self.plotWidget.setLabel('left', 'Waist radius', units='µm', color='#333333')
        self.plotWidget.setLabel('bottom', 'z', units='cm', color='#333333')
        self.plotWidget.setTitle("Gaussian Beam Propagation", color='#333333')
        axis_pen = pg.mkPen(color='#333333')
        self.plotWidget.getAxis('left').setTextPen(axis_pen)
        self.plotWidget.getAxis('bottom').setTextPen(axis_pen)

        # Set up the plot widget
        self.z_data = [0,1,2,3,4,5]
        self.w_sag_data = [1,1,1,1,1,1]
        self.w_tan_data = [0,2,3,4,5,6]
        self.plotWidget.setBackground('w')
        self.plotWidget.addLegend()
        self.plotWidget.showGrid(x=True, y=True)

        # Add text item for coordinates
        text = pg.TextItem(text='', anchor=(0.5, 2.0), color='#333333')
        self.plotWidget.addItem(text)

        self.plotWidget.plot(self.z_data, self.w_sag_data, 
                        pen=pg.mkPen(color='b', width=2))
        self.plotWidget.plot(self.z_data, self.w_tan_data, 
                        pen=pg.mkPen(color='r', width=2))
        
        def mouseMoved(evt):
            pos = evt
            if self.plotWidget.sceneBoundingRect().contains(pos):
                mousePoint = self.plotWidget.getViewBox().mapSceneToView(pos)
                z = mousePoint.x()
                z_data = np.array(self.z_data)  # Umwandlung hier!
                idz = (np.abs(z_data - z)).argmin()
                z_val = z_data[idz]
                w_sag_val = np.array(self.w_sag_data)[idz]
                w_tan_val = np.array(self.w_tan_data)[idz]
                self.ui.label_z_position.setText(f"{z_val:.3f} mm")
                self.ui.label_w_sag.setText(f"{w_sag_val:.3f} mm")
                self.ui.label_w_tan.setText(f"{w_tan_val:.3f} mm")

        # Connect signal to function
        self.plotWidget.scene().sigMouseMoved.connect(mouseMoved)

    def generate_data(self, optical_system_sag, optical_system_tan, q0):
        # Create PyQtGraph window
        
        # Define optical system: propagation(0.1m) -> lens(f=0.05m) -> propagation(0.2m)
        self.optical_system_sag = optical_system_sag
        self.optical_system_tan = optical_system_tan
        
        # Calculate beam propagation
        z_vals, w_sag_vals = self.propagate_through_system(q0, optical_system_sag)
        z_vals, w_tan_vals = self.propagate_through_system(q0, optical_system_tan)
        
        # Convert to mm for plotting
        z_vals = np.array(z_vals) * 1e3  # meters to mm
        w_sag_vals = np.array(w_sag_vals) * 1e3  # meters to mm
        w_tan_vals = np.array(w_tan_vals) * 1e3

        
        # Add vertical lines at optical element positions
        z_element = 0
        for element, param in optical_system_sag:
            if element != self.matrices.free_space:
                self.plotWidget.addLine(x=z_element*1e3, pen=pg.mkPen('r'))
            z_element += param if element == self.matrices.free_space else 0
        
    def handle_build_resonator(self):
        """
        Handles the 'Build Resonator' button action.
        Sets the current context to 'resonator' and opens the library window.
        """
        self.current_context = "resonator"
        self.item_selector_res.open_library_window(self)
        self.hide()

    def handle_modematcher(self):
        """
        Handles the 'Modematcher' button action.
        Sets the current context to 'modematcher' and opens the library window.
        """
        self.current_context = "modematcher"
        self.item_selector_modematcher.open_library_window()
        self.hide()

    def action_open(self):
        """
        Handles the 'Open' menu action.
        Opens a file dialog for selecting and loading files.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "Open File", 
            "", 
            "All Files (*);;Python Files (*.py)"
        )
        if file_name:
            with open(file_name, 'r') as file:
                content = file.read()
                print(content)  # Placeholder for file handling logic

    def action_save(self):
        """
        Handles the 'Save' menu action.
        Placeholder for save functionality.
        """
        print("Save action triggered")  # Placeholder for save logic

    def action_save_as(self):
        """
        Handles the 'Save As' menu action.
        Opens a file dialog for saving files to a new location.
        """
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "Save File As", 
            "", 
            "All Files (*);;Python Files (*.py)"
        )
        if file_name:
            with open(file_name, 'w') as file:
                file.write("test")  # Placeholder for save logic

    

    def action_exit(self):
        """
        Handles the 'Exit' menu action.
        Shows a confirmation dialog before closing the application.
        """
        reply = QMessageBox.question(
            self, 
            "Exit", 
            "Do you really want to close the program? All unsaved data will be lost!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()