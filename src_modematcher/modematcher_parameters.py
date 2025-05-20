import json
import numpy as np
import re
import config
from os import path
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from src_resonator.problem import Problem
from src_resonator.plot_setup import Plotter
from src_resonator.resonator_types import *
from src_modematcher.modematcher_calculator import ModematcherCalculator

class ModematcherParameterWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_selector = None  # Reference to ItemSelector
        self.modematcher_calculation = None  # Reference to Modematcher calculation

    def closeEvent(self, event):
        """
        Called when the window is about to be closed (X button).
        """
        event.ignore()  # Prevent default closing
        if self.item_selector:
            self.item_selector.handle_back_button()

class ModematcherParameters(QObject):
    """
    Class for matching the impedance of a resonator.
    """

    def __init__(self, parent=None):
        """
        Initialize the Modematcher class.
        """
        super().__init__(parent)
        self.resonator = None
        self.libraries = None
        self.item_selector = None
        self.modematcher_calculation_window = None

    def open_modematcher_parameter_window(self):
        """
        Creates and shows the modematcher configuration window.
        """
        self.modematcher_parameter_window = QMainWindow()
        # Load the modematcher UI
        self.ui_modematcher = uic.loadUi(
            path.abspath(path.join(path.dirname(path.dirname(__file__)), 
            "assets/modematcher_parameter_input_window.ui")), 
            self.modematcher_parameter_window
        )
        
        # Configure and show the window
        self.modematcher_parameter_window.setWindowTitle("Mode Matching")
        self.modematcher_parameter_window.show()

        self.ui_modematcher.button_back.clicked.connect(self.close_modematcher_parameter_window)

        self.ui_modematcher.button_next.clicked.connect(self.handle_next_button)

    def close_modematcher_parameter_window(self):
        """
        Hides the current window and shows the previous window.
        """
        if hasattr(self, 'previous_window') and self.previous_window:
            self.previous_window.show()  # Show the previous window
            self.previous_window.raise_()  # Bring previous window to front
        
        if self.modematcher_parameter_window:
            self.modematcher_parameter_window.hide()  # Hide current window instead of closing
    
    def handle_next_button(self):
        """
        Saves the parameters and opens the calculator window.
        """
        try:
            # Save the parameters first
            self.get_parameters()
            
            # Hide the current window
            self.modematcher_parameter_window.hide()
            
            # Create calculator instance if it doesn't exist
            if not hasattr(self, 'calculator'):
                self.calculator = ModematcherCalculator(self)
            
            # Open calculator window and set previous window reference
            self.calculator.open_modematcher_calculator_window()
            self.calculator.previous_window = self.modematcher_parameter_window
            
        except ValueError as e:
            QMessageBox.critical(self.modematcher_parameter_window, "Error", str(e))

    def get_parameters(self):

        #General paramters
        wavelength = self.convert_to_float(self.ui_modematcher.lineEdit_wavelength.text())
        distance = self.convert_to_float(self.ui_modematcher.lineEdit_distance.text())

        #Input Beam
        waist_input_sag = self.convert_to_float(self.ui_modematcher.lineEdit_waist_input_sag.text())
        waist_input_tan = self.convert_to_float(self.ui_modematcher.lineEdit_waist_input_tan.text())
        waist_position_sag = self.convert_to_float(self.ui_modematcher.lineEdit_waist_position_sag.text())
        waist_position_tan = self.convert_to_float(self.ui_modematcher.lineEdit_waist_position_tan.text())
        zr_input_sag = np.pi * (waist_position_sag**2) / wavelength
        zr_input_tan = np.pi * (waist_position_tan**2) / wavelength

        #Output Beam
        waist_output_sag = self.convert_to_float(self.ui_modematcher.lineEdit_waist_output_sag.text())
        waist_output_tan = self.convert_to_float(self.ui_modematcher.lineEdit_waist_output_tan.text())
        waist_position_output_sag = self.convert_to_float(self.ui_modematcher.lineEdit_waist_position_output_sag.text())
        waist_position_output_tan = self.convert_to_float(self.ui_modematcher.lineEdit_waist_position_output_tan.text())
        zr_output_sag = np.pi * (waist_position_output_sag**2) / wavelength
        zr_output_tan = np.pi * (waist_position_output_tan**2) / wavelength

        config.set_temp_data_modematcher(
            wavelength,
            distance,
            waist_input_sag,
            waist_input_tan,
            waist_position_sag,
            waist_position_tan,
            zr_input_sag,
            zr_input_tan,
            waist_output_sag,
            waist_output_tan,
            waist_position_output_sag,
            waist_position_output_tan,
            zr_output_sag,
            zr_output_tan
        ) 


    def convert_to_float(self, value):
        """
        Converts a string containing a number and a unit to meters.
        
        Args:
            value (str): String containing a number and a unit (e.g. "10 mm")
            
        Returns:
            float: Value converted to meters
            
        Raises:
            ValueError: If the unit is unknown or the format is invalid
        """
        # Units and conversion factors
        units = {
            'am': 1e-18,  # Attometers to meters
            'fm': 1e-15,  # Femtometers to meters
            'pm': 1e-12,  # Picometers to meters
            'nm': 1e-9,   # Nanometers to meters
            'µm': 1e-6,   # Micrometers to meters
            'um': 1e-6,   # Micrometers to meters (alternative)
            'mm': 1e-3,   # Millimeters to meters
            'cm': 1e-2,   # Centimeters to meters
            'm': 1,       # Meters to meters
            'km': 1e3     # Kilometers to meters
        }

        # Regex to extract number and unit
        match = re.match(r"(\d+\.?\d*)\s*(\w+)", value)
        
        if match:
            number = float(match.group(1))  # Extract number
            unit = match.group(2)           # Extract unit
            
            if unit in units:
                return number * units[unit]
            else:
                raise ValueError(f"Unknown unit: {unit}")
        else:
            raise ValueError("Invalid format. Please enter a number followed by a unit (e.g. '10 mm').")