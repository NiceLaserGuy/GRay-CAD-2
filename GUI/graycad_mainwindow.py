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

# Custom module imports
from src_resonator.resonators import Resonator
from src_libraries.libraries import Libraries
from src_libraries.select_items import ItemSelector
from src_modematcher.modematcher import Modematcher

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
        self.modematcher = Modematcher()
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
        self.ui.button_build_resonator.clicked.connect(self.handle_build_resonator)
        self.ui.button_modematcher.clicked.connect(self.handle_modematcher)

    def handle_build_resonator(self):
        """
        Handles the 'Build Resonator' button action.
        Sets the current context to 'resonator' and opens the library window.
        """
        self.current_context = "resonator"
        self.item_selector_res.open_library_window()
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