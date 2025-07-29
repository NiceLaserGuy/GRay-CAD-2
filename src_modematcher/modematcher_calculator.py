from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5 import uic
from os import path
from src_modematcher.lens_system_optimizier import LensSystemOptimizer

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
        
        # Optimizer initialisieren (ohne feste Linsenbibliothek)
        from src_physics.matrices import Matrices
        self.matrices = Matrices()
        self.optimizer = LensSystemOptimizer(self.matrices)  # Keine lens_library mehr
    
    def calculate_optimal_system(self, w0, z0, w_target, z_target, wavelength):
        """Berechne optimales Linsensystem"""
        try:
            # Prüfe ob Linsenbibliothek verfügbar ist
            if not self.optimizer.lens_library:
                raise Exception("No lens library available. Please select lenses first.")
            
            optimized_system = self.optimizer.optimize_lens_system(
                w0=w0,
                z0=z0, 
                w_target=w_target,
                z_target=z_target,
                wavelength=wavelength,
                max_lenses=3,
                max_length=1.0,
                n_medium=1.0
            )
            
            return optimized_system
            
        except Exception as e:
            print(f"Error in optimization: {e}")
            return None
    
    def open_modematcher_calculator_window(self):
        """UI-Integration"""
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
        
        # Neue Button-Verbindungen
        self.ui_modematcher_calculation.button_optimize.clicked.connect(self.run_optimization)

    def close_modematcher_calculation_window(self):
        """
        Hides the current window and shows the previous window.
        """
        if hasattr(self, 'previous_window') and self.previous_window:
            self.previous_window.show()  # Show the previous window
            self.previous_window.raise_()  # Bring previous window to front
        
        if self.modematcher_calculation_window:
            self.modematcher_calculation_window.hide()  # Hide current window instead of closing
    
    def run_optimization(self):
        """GUI-Callback für Optimierung"""
        try:
            # Prüfe ob Linsen ausgewählt wurden
            temp_file_path = config.get_temp_file_path()
            if not temp_file_path:
                QMessageBox.warning(
                    self.modematcher_calculation_window,
                    "No Lenses Selected",
                    "Please select lenses first using the 'Select Lenses' button."
                )
                return
            
            # Lese Parameter aus GUI
            w0 = float(self.ui_modematcher_calculation.input_w0.text())
            z0 = float(self.ui_modematcher_calculation.input_z0.text())
            w_target = float(self.ui_modematcher_calculation.input_w_target.text())
            z_target = float(self.ui_modematcher_calculation.input_z_target.text())
            wavelength = float(self.ui_modematcher_calculation.input_wavelength.text())
            
            # Status-Update
            self.ui_modematcher_calculation.label_status.setText("Optimizing...")
            self.ui_modematcher_calculation.button_optimize.setEnabled(False)
            
            # Optimierung durchführen
            optimized_system = self.calculate_optimal_system(
                w0, z0, w_target, z_target, wavelength)
            
            if optimized_system:
                # Übertrage an Hauptfenster
                self._transfer_optimized_system(optimized_system)
                QMessageBox.information(
                    self.modematcher_calculation_window,
                    "Optimization Complete",
                    f"Generated optimized lens system with {len(optimized_system)} components."
                )
                self.ui_modematcher_calculation.label_status.setText("Optimization successful")
            else:
                QMessageBox.warning(
                    self.modematcher_calculation_window,
                    "Optimization Failed",
                    "Could not find a suitable lens system."
                )
                self.ui_modematcher_calculation.label_status.setText("Optimization failed")
                
        except Exception as e:
            QMessageBox.critical(
                self.modematcher_calculation_window,
                "Error",
                f"Error in optimization: {str(e)}"
            )
            self.ui_modematcher_calculation.label_status.setText("Error in optimization")
        finally:
            self.ui_modematcher_calculation.button_optimize.setEnabled(True)
    
    def _transfer_optimized_system(self, optimized_system):
        """Übertrage optimiertes System an Hauptfenster"""
        try:
            # Methode 1: Direkte Übertragung via Parent
            parent = self.parent()
            if parent and hasattr(parent, 'receive_optimized_system'):
                parent.receive_optimized_system(optimized_system)
                return
            
            # Methode 2: Widget-Suche
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if hasattr(widget, 'receive_optimized_system') and hasattr(widget, 'setupList'):
                        widget.receive_optimized_system(optimized_system)
                        return
            
            raise Exception("Could not find MainWindow to transfer optimized system")
            
        except Exception as e:
            raise Exception(f"Failed to transfer optimized system: {e}")
