import re

class ValueConverter():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def convert_to_float(self, value):
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
            'km': 1e3     # Kilometers to meters
        }

        # Regex to extract number and unit
        match = re.match(r"(\d+\.?\d*)\s*(\w+)", value)
        
        if match:
            number = float(match.group(1))  # Extract number
            unit = match.group(2)           # Extract unit
            
            if unit in units:
                return number * units[unit]
            else:
                raise ValueError(f"Unknown unit: {unit}")
        else:
            raise ValueError("Invalid format. Please enter a number followed by a unit (e.g. '10 mm').")
        
    def convert_to_nearest_string(self, value):
        """
        Converts a float value to a string with the nearest unit.
        
        Args:
            value (float): Value in meters
            
        Returns:
            str: Value converted to the nearest unit
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
            'km': 1e3     # Kilometers to meters
        }
        
        for unit, factor in units.items():
            if abs(value / 1000) <= factor:
                return f"{value / factor:.3f} {unit}"
        
        return f"{value:.3f}"