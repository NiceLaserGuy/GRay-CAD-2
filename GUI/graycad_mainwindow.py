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
from src_physics.matrices import Matrices
from src_physics.value_converter import ValueConverter

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
        self.ui.action_About.triggered.connect(self.action_about)
        self.ui.action_Tips_and_tricks.triggered.connect(self.action_tips_and_tricks)
        
        # Connect library menu item to the library window
        self.ui.action_Library.triggered.connect(self.lib.open_library_window)
        
        # Connect buttons to their respective handlers
        self.ui.action_Cavity_Designer.triggered.connect(self.handle_build_resonator)
        self.ui.action_Modematcher.triggered.connect(self.handle_modematcher)

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
                #self.ui.label_roc_sag.setText(f"{self.vc.convert_to_nearest_string(self.beam.radius_of_curvature(z_val, 0.514E-6, 1))}")
                #self.ui.label_roc_tan.setText(f"{self.vc.convert_to_nearest_string(self.beam.radius_of_curvature(z_val, 0.514E-6, 1))}")
                
        # Connect signal to function
        self.plotWidget.scene().sigMouseMoved.connect(mouseMoved)
        
    def plot_optical_system(self, z_start=0, wavelength=0.514E-6, beam_radius=1E-3, n=1, optical_system=None):
        """
        Plots the given optical system.
        """
        if optical_system is None:
            optical_system = self.current_optical_system
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

    def handle_build_resonator(self):
        """
        Handles the 'Build Resonator' button action.
        Sets the current context to 'resonator' and opens the library window.
        """
        self.current_context = "resonator"
        self.item_selector_res.open_library_window(self)

    def handle_modematcher(self):
        """
        Handles the 'Modematcher' button action.
        Sets the current context to 'modematcher' and opens the library window.
        """
        self.current_context = "modematcher"
        self.item_selector_modematcher.open_library_window()

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
                
    def action_about(self):
        """
        Handles the 'About' menu action.
        Displays information about the application.
        """
        QMessageBox.information(
            self, 
            "About", 
            "GRay-CAD 2\nVersion 1.0\nDeveloped by Jens Gumm, TU Darmstadt, LQO-Group"
        )

    def action_tips_and_tricks(self):
        """
        Handles the 'Tips and Tricks' menu action.
        Displays helpful tips for using the application.
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Tips and Tricks")
        msg.setTextFormat(Qt.RichText)
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            "1. Use the library to manage your components.<br>"
            "2. Take advantage of the simulation features like the Modematcher and the Cavity Designer.<br>"
            "3. Don't forget to save your work!<br>"
            '4. Report bugs on GitHub: <a href="https://github.com/NiceLaserGuy/GRay-CAD-2">https://github.com/NiceLaserGuy/GRay-CAD-2</a>'
        )
        msg.exec()

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