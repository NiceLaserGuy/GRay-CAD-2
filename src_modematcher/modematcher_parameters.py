import json
import numpy as np
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
from src_physics.value_converter import ValueConverter

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
        self.vc = ValueConverter()

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
            # --- NEU: temporäre Komponentenliste leeren ---
            if hasattr(self.previous_window, 'item_selector'):
                self.previous_window.item_selector.temporary_components = []
                self.previous_window.item_selector.update_temporary_list_view()
                # Optional: auch die Anzeige zurücksetzen
                if hasattr(self.previous_window.item_selector, 'update_temporary_list_view'):
                    self.previous_window.item_selector.update_temporary_list_view()
        if self.modematcher_parameter_window:
            self.modematcher_parameter_window.hide()  # Hide current window instead of closing
    
    def handle_next_button(self):
        """
        Saves the parameters and opens the calculator window.
        """
        try:
            # Save the parameters first
            self.get_parameters()
            
            # Create calculator instance if it doesn't exist
            if not hasattr(self, 'calculator'):
                self.calculator = ModematcherCalculator(self)
            
            # Zeige Calculator mit Referenz zum Parameter-Fenster
            self.calculator.show_with_previous(self.modematcher_parameter_window)
            
            # Hide the current window NACH dem Öffnen des neuen Fensters
            self.modematcher_parameter_window.hide()
            
        except ValueError as e:
            QMessageBox.critical(self.modematcher_parameter_window, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(
                self.modematcher_parameter_window, 
                "Unexpected Error", 
                f"An error occurred: {str(e)}"
            )

    def get_parameters(self):

        #General paramters
        wavelength = self.vc.convert_to_float(self.ui_modematcher.lineEdit_wavelength.text())
        distance = self.vc.convert_to_float(self.ui_modematcher.lineEdit_distance.text())

        #Input Beam
        waist_input_sag = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_input_sag.text())
        waist_input_tan = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_input_tan.text())
        waist_position_sag = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_position_sag.text())
        waist_position_tan = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_position_tan.text())
        #Output Beam
        waist_goal_sag = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_output_sag.text())
        waist_goal_tan = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_output_tan.text())
        waist_position_goal_sag = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_position_output_sag.text())
        waist_position_goal_tan = self.vc.convert_to_float(self.ui_modematcher.lineEdit_waist_position_output_tan.text())

        config.set_temp_data_modematcher(
            wavelength,
            distance,
            waist_input_sag,
            waist_input_tan,
            waist_position_sag,
            waist_position_tan,
            waist_goal_sag,
            waist_goal_tan,
            waist_position_goal_sag,
            waist_position_goal_tan
        )