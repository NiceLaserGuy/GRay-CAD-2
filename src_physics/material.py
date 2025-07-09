import numpy as np
from PyQt5.QtWidgets import QMessageBox

class Material:

    def __init__(self):
        pass

    def get_n(*args):
        material = args[0]  # args[0] ist die Instanz (self)
        lambda_ = args[1]*1e6
        
        # Initialisiere n mit Standardwert
        n = 1.0  # Fallback: Luft
        
        if isinstance(material, str):
            if material == "NBK7":
                n = np.sqrt(((1.03961212*lambda_**2)/(lambda_**2-0.00600069867))
                    +((0.231792344*lambda_**2)/(lambda_**2-0.0200179144))
                    +((1.01046945*lambda_**2)/(lambda_**2-103.560653))+1)
            elif material == "Fused Silica":  # Verwende elif statt if
                n = np.sqrt(((0.6961663*lambda_**2)/(lambda_**2- 0.0684043**2))
                    +((0.4079426*lambda_**2)/(lambda_**2- 0.1162414**2))
                    +((0.8974794*lambda_**2)/(lambda_**2-9.896161**2))+1)
            else:
                QMessageBox.critical(None, "Error", f"Material '{material}' not recognized.")
        elif isinstance(material, (int, float)):
            # Falls material eine Zahl ist, verwende diese direkt als Brechungsindex
            n = float(material)
        
        return n