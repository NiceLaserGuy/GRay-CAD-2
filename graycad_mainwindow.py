#Python 3.10.2
# -*- coding: utf-8 -*-
"""
@author: Jens Gumm, TU Darmstadt, LQO-Group
"""

from PyQt6 import uic
from pyqtgraph import *
from os import path
from PyQt6.QtCore import *
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QPushButton, QDialog, QMessageBox, QFileDialog
from resonators import Resonator
from matrices import Matrices

import pyqtgraph as pg
import logging

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.res = Resonator()
        self.mat = Matrices()

        # Set window icon
        self.setWindowIcon(QIcon(path.abspath(path.join(path.dirname(__file__), "/assets/TaskbarIcon.png"))))

        # Load the UI from a file in this path
        self.ui = uic.loadUi(path.abspath(path.join(path.dirname(__file__))) + "/interface.ui", self)
        
        # Connect the button to the method
        self.ui.button_build_resonator.clicked.connect(self.open_resonator_window)

        # Connect menu actions to methods
        self.ui.action_Open.triggered.connect(self.action_open)
        self.ui.action_Save.triggered.connect(self.action_save)
        self.ui.action_Save_as.triggered.connect(self.action_save_as)
        self.ui.action_Exit.triggered.connect(self.action_exit)

    def open_resonator_window(self):
        """Open a new window when the button is clicked"""
        self.resonator_window = QMainWindow(self)
        self.ui_resonator = uic.loadUi(path.abspath(path.join(path.dirname(__file__), "resonator_window.ui")), self.resonator_window)
        self.resonator_window.setWindowTitle("Build Resonator")
        self.resonator_window.show()

        # Pass the ui_resonator reference to the Resonator instance
        self.res.set_ui_resonator(self.ui_resonator)

        # Connect the button to the method after ui_resonator is initialized
        self.ui_resonator.button_evaluate_resonator.clicked.connect(self.res.evaluate_resonator)

    def action_open(self):
        """Open a file dialog to select a file to open"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Python Files (*.py)")
        if file_name:
            with open(file_name, 'r') as file:
                # Implement the logic to open and read the file
                content = file.read()
                # For example, you can set the content to a text editor widget
                # self.ui.textEdit.setPlainText(content)
                print(content)  # Replace this with your logic

    def action_save(self):
        """Save the current file"""
        # Implement the logic to save the current file
        # For example, you can get the content from a text editor widget
        # content = self.ui.textEdit.toPlainText()
        # with open(self.current_file, 'w') as file:
        #     file.write(content)
        print("Save action triggered")  # Replace this with your logic

    def action_save_as(self):
        """Open a file dialog to select a location to save the file"""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "All Files (*);;Python Files (*.py)")
        if file_name:
            # Implement the logic to save the file
            # For example, you can get the content from a text editor widget
            # content = self.ui.textEdit.toPlainText()
            with open(file_name, 'w') as file:
                file.write("test")
            print(f"Save as action triggered: {file_name}")  # Replace this with your logic

    def action_exit(self):
        """Zeigt eine Bestätigungsnachricht an, bevor das Programm geschlossen wird."""
        reply = QMessageBox.question(self, "Exit", "Do you really want to close the program? All unsaved data will be lost!",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.close()