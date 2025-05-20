from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5 import uic
from os import path

class ModematcherCalculationWindow(QMainWindow):
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

class ModematcherCalculator:
    def __init__(self, modematcher):
        self.modematcher = modematcher

    def open_modematcher_calculator_window(self):
        """
        Creates and shows the modematcher configuration window.
        """
        self.modematcher_calculation_window = QMainWindow()
        # Load the modematcher UI
        self.ui_modematcher_calculation = uic.loadUi(
            path.abspath(path.join(path.dirname(path.dirname(__file__)), 
            "assets/modematcher_calculation_window.ui")), 
            self.modematcher_calculation_window
        )
        
        # Configure and show the window
        self.modematcher_calculation_window.setWindowTitle("Mode Matching")
        self.modematcher_calculation_window.show()

        self.ui_modematcher_calculation.button_back.clicked.connect(self.close_modematcher_calculation_window)

    def close_modematcher_calculation_window(self):
        """
        Hides the current window and shows the previous window.
        """
        if hasattr(self, 'previous_window') and self.previous_window:
            self.previous_window.show()  # Show the previous window
            self.previous_window.raise_()  # Bring previous window to front
        
        if self.modematcher_calculation_window:
            self.modematcher_calculation_window.hide()  # Hide current window instead of closing
