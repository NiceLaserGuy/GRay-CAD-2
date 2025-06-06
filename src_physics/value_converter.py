import re
from PyQt5.QtWidgets import QMessageBox

class ValueConverter():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert_to_float(self, value, parent=None):
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
            'km': 1e3,    # Kilometers to meters
            'Inf': 1e30,  # Infinity to meters
            'inf': 1e30   # Infinity to meters (case insensitive)
        }

        # Regex to extract number and unit
        match = re.match(r"(\d+\.?\d*)\s*(\w+)", value)
        
        if match:
            number = float(match.group(1))  # Extract number
            unit = match.group(2)           # Extract unit
            
            if unit in units:
                return number * units[unit]

                    # Fehlermeldung nur, wenn keine passende Einheit gefunden wurde
        QMessageBox.critical(
            parent,
            "Error",
            "Unknown unit for value: {}. Please use one of the following units: {}".format(value, list(units.keys()))
        )
        return

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
            if abs(value / 1000) <= factor:
                num = value / factor
                num_str = f"{num:.3f}".rstrip('0').rstrip('.')
                return f"{num_str} {unit}"

        # Fehlermeldung nur, wenn keine passende Einheit gefunden wurde
        QMessageBox.critical(
            parent,
            "Error",
            "Unknown unit for value: {}. Please use one of the following units: {}".format(value, list(units.keys()))
        )
        return f"{value:.3f}"