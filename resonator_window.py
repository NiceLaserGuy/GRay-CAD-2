from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow
from os import path
from resonators import Resonator

class ResonatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.res = Resonator()
        
    def open_resonator_window(main_window):
        """Open a new window when the button is clicked"""
        main_window.resonator_window = QMainWindow(main_window)
        main_window.ui_resonator = uic.loadUi(path.abspath(path.join(path.dirname(__file__), "assets/resonator_window.ui")), main_window.resonator_window)
        main_window.resonator_window.setWindowTitle("Build Resonator")
        main_window.resonator_window.show()

        # Pass the ui_resonator reference to the Resonator instance
        main_window.res.set_ui_resonator(main_window.ui_resonator)

        # Connect the button to the method after ui_resonator is initialized
        main_window.ui_resonator.button_evaluate_resonator.clicked.connect(main_window.res.evaluate_resonator)