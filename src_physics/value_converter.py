import re
from PyQt5.QtWidgets import QMessageBox

from PyQt5.QtCore import QTimer

class ValueConverter():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._error_timer = QTimer()
        self._error_timer.setSingleShot(True)
        self._error_timer.timeout.connect(self._show_delayed_error)
        self._pending_error = None
        self._pending_parent = None

    def convert_to_float(self, value, parent=None):
        units = {
            'am': 1e-18, 'fm': 1e-15, 'pm': 1e-12, 'nm': 1e-9,
            'µm': 1e-6, 'um': 1e-6, 'mm': 1e-3, 'cm': 1e-2,
            'm': 1, 'km': 1e3, 'Inf': 1e30, 'inf': 1e30
        }
        match = re.match(r"(\d+\.?\d*)\s*(\w+)?", value)
        if match:
            number = float(match.group(1))
            unit = match.group(2)
            if unit is None:
                self._cancel_error()
                return number * units['mm']
            if unit in units:
                self._cancel_error()
                return number * units[unit]
        # Fehler verzögert anzeigen
        self._pending_error = value
        self._pending_parent = parent
        self._error_timer.start(500)
        return None

    def _show_delayed_error(self):
        if self._pending_error is not None:
            QMessageBox.critical(
                self._pending_parent,
                "Error",
                "Unknown unit for value: {}. Please use one of the following units: {}".format(
                    self._pending_error, ['am','fm','pm','nm','µm','um','mm','cm','m','km','Inf','inf']
                )
            )
            self._pending_error = None
            self._pending_parent = None

    def _cancel_error(self):
        self._error_timer.stop()
        self._pending_error = None
        self._pending_parent = None

    def convert_to_nearest_string(self, value, parent=None):
        """
        Converts a float value to a string with the nearest unit.
        
        Args:
            value (float): Value in meters
            
        Returns:
            str: Value converted to the nearest unit
        """
        units = {
            'am': 1e-18,
            'fm': 1e-15,
            'pm': 1e-12,
            'nm': 1e-9,
            'µm': 1e-6,
            'um': 1e-6,
            'mm': 1e-3,
            'cm': 1e-2,
            'm': 1,
            'km': 1e3,
            'Inf': 1e30
        }

        for unit, factor in units.items():
            if unit == 'Inf' and abs(value) >= 1e29:
                return unit
            if abs(value / 100) <= factor:
                num = value / factor
                num_str = f"{num:.3f}".rstrip('0').rstrip('.')
                return f"{num_str} {unit}"

        # Fehlermeldung nur, wenn keine passende Einheit gefunden wurde
        self._pending_error = value
        self._pending_parent = parent
        self._error_timer.start(500)
        return f"{value:.3f}"