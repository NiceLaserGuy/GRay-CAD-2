from pint import UnitRegistry
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
import numpy as np

class ValueConverter:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ureg = UnitRegistry()
        self.ureg.default_format = "~P"  # Kompakte SI-Darstellung
        self._error_timer = QTimer()
        self._error_timer.setSingleShot(True)
        self._error_timer.timeout.connect(self._show_delayed_error)
        self._pending_error = None
        self._pending_parent = None

    def convert_to_float(self, value, parent=None):
        """
        Konvertiert z. B. '1.2 µm' → 1.2e-6 (in Meter)
        """
        try:
            quantity = self.ureg.Quantity(value)
            quantity = quantity.to_base_units()
            return float(quantity.magnitude)
        except Exception:
            self._pending_error = value
            self._pending_parent = parent
            self._error_timer.start(1000)
            return None

    def convert_to_nearest_string(self, value, parent=None):
        """
        Konvertiert z. B. 0.0000012 (Meter) → '1.2 µm'
        """
        try:
            q = value * self.ureg.meter
            q = q.to_compact()
            return f"{q:.2f#~P}"  # Kompakte SI-Notation mit 3 signifikanten Stellen
        except Exception:
            self._pending_error = value
            self._pending_parent = parent
            self._error_timer.start(1000)
            return f"{value:.3f}"

    def _show_delayed_error(self):
        if self._pending_error is not None:
            QMessageBox.critical(
                self._pending_parent,
                "Error",
                f"Unknown or invalid value: {self._pending_error}. Please enter a valid number with unit (e.g. '3.5 mm', '1.2 µm')."
            )
            self._pending_error = None
            self._pending_parent = None

    def _cancel_error(self):
        self._error_timer.stop()
        self._pending_error = None
        self._pending_parent = None
