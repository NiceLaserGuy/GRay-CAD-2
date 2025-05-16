import json
import numpy as np
import re
from os import path
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from src_resonator.problem import Problem
from src_resonator.plot_setup import Plotter
from src_resonator.resonator_types import *

class Modematcher(QObject):
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
        self.modematcher = None

    def open_modematcher_window(self):

        self.modematcher_window = QMainWindow()
        # Load the resonator UI
        self.ui_modematcher = uic.loadUi(
            path.abspath(path.join(path.dirname(path.dirname(__file__)), 
            "assets/modematcher_window.ui")), 
            self.modematcher_window
        )
        
        # Configure and show the window
        self.modematcher_window.setWindowTitle("Modematching")
        self.modematcher_window.show()
    
    def umrechnen_zu_float(self, value):
        # Einheiten und Umrechnungsfaktoren
        units = {
            'am': 1e-18,  # Attometer in Meter
            'fm': 1e-15,  # Femtometer in Meter
            'pm': 1e-12,  # Picometer in Meter
            'nm': 1e-9,  # Nanometer in Meter
            'µm': 1e-6,  # Mikrometer in Meter
            'um': 1e-6,  # Mikrometer in Meter
            'mm': 1e-3,  # Millimeter in Meter
            'cm': 1e-2,  # Zentimeter in Meter
            'm': 1,      # Meter bleibt Meter
            'km': 1e3     # Kilometer in Meter
        }

        # Regex, um Zahl und Einheit zu extrahieren
        match = re.match(r"(\d+\.?\d*)\s*(\w+)", value)
        
        if match:
            number = float(match.group(1))  # Zahl extrahieren
            unit = match.group(2)  # Einheit extrahieren
            
            if unit in units:
                return number * units[unit]
            else:
                raise ValueError(f"Unknown Unit: {unit}")
        else:
            raise ValueError("Invalid format. Please enter a number followed by a unit.")