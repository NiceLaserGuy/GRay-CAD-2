from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
import json
import copy
import os

class SetupList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        
        # Lade Default-Setup
        self.load_default_setup()

    def _to_bool(self, value):
        """Konvertiert verschiedene Werte zu Boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return False

    @staticmethod
    def get_default_components():
        """Definiere Standard-Komponenten als Fallback (als statische Methode)."""
        return [
            {
                "type": "BEAM",
                "name": "Beam",
                "manufacturer": "",
                "properties": {
                    "Wavelength": 514e-9,
                    "Waist radius sagittal": 1e-3,
                    "Waist radius tangential": 1e-3,
                    "Waist position sagittal": 0,
                    "Waist position tangential": 0,
                    "IS_ROUND": True
                }
            },
            {
                "type": "PROPAGATION",
                "name": "Propagation",
                "manufacturer": "",
                "properties": {
                    "Length": 0.1,
                    "Refractive index": 1.0
                }
            },
            {
                "type": "LENS",
                "name": "Lens",
                "manufacturer": "",
                "properties": {
                    "Focal length tangential": 0.09606,
                    "Focal length sagittal": 0.09606,
                    "Radius of curvature tangential": 0.1,
                    "Radius of curvature sagittal": 0.1,
                    "Lens material":"NBK7",
                    "Plan lens": False,
                    "Design wavelength":514e-9,
                    "IS_ROUND": True
                }
            },
            {
                "type": "PROPAGATION",
                "name": "Propagation",
                "manufacturer": "",
                "properties": {
                    "Length": 0.2,
                    "Refractive index": 1.0
                }
            }
        ]

    def load_default_setup(self):
        """Lade Default-Setup mit Fallback-Mechanismus."""
        components = None
        
        # Versuche zuerst aus Default-Setup-Datei zu laden
        try:
            default_setup_path = "Projects/templates/default_setup.graycad"
            if os.path.exists(default_setup_path):
                with open(default_setup_path, "r", encoding="utf-8") as f:
                    setup_data = json.load(f)
                components = setup_data.get("components", [])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load default setup file: {e}")
        
        # Fallback: Versuche aus Generic.json zu laden
        if not components:
            try:
                with open("Library/Generic.json", "r", encoding="utf-8") as f:
                    generic_data = json.load(f)
                library_components = generic_data.get("components", [])
                
                # Finde die gewünschten Komponenten
                def find_component(key, value):
                    for comp in library_components:
                        if comp.get(key, "").strip().lower() == value:
                            return comp
                    return None

                beam = find_component("name", "beam")
                propagation = find_component("name", "propagation")
                lens = find_component("name", "lens")
                
                components = [beam, propagation, lens, propagation]
                components = [comp for comp in components if comp is not None]
            except Exception as e:
                pass
        # Letzter Fallback: Code-basierte Komponenten
        if not components:
            components = self.get_default_components()

        
        # Füge Komponenten zur Liste hinzu
        for comp in components:
            if comp is not None:
                # Sichere Boolean-Konvertierung für alle Properties
                if "properties" in comp:
                    for key, value in comp["properties"].items():
                        if key in ["IS_ROUND", "Plan lens"]:
                            comp["properties"][key] = self._to_bool(value)
                
                item = QtWidgets.QListWidgetItem(comp.get("name", "Unnamed"))
                item.setData(QtCore.Qt.UserRole, copy.deepcopy(comp))
                self.addItem(item)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            # Mehrere markierte Items löschen, aber nie den Beam (Index 0)
            for item in self.selectedItems():
                row = self.row(item)
                if row == 0:
                    continue  # Beam nicht löschen
                self.takeItem(row)
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-component"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-component"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        # Externes Drag & Drop (z.B. von componentList)
        if event.source() != self and event.mimeData().hasFormat("application/x-component"):
            component = json.loads(bytes(event.mimeData().data("application/x-component")).decode())
            
            # Erstelle eine frische Kopie ohne zwischengespeicherte Änderungen
            fresh_component = copy.deepcopy(component)
            
            # Initialisiere wichtige Eigenschaften basierend auf Komponentenart
            ctype = fresh_component.get("type", "").strip().upper()
            props = fresh_component.get("properties", {})
            
            # Für Linsen - NUR setzen wenn nicht vorhanden
            if ctype == "LENS":
                if "Variable parameter" not in props:
                    props["Variable parameter"] = "Edit focal length"
                if "Plan lens" not in props:
                    props["Plan lens"] = True
                if "Lens material" not in props:
                    props["Lens material"] = "NBK7"
                
            # Für Propagation  
            elif ctype == "PROPAGATION":
                if "Refractive index" not in props:
                    props["Refractive index"] = 1.0

            # Für dicke Linsen
            elif ctype == "THICK LENS":
                if "Lens material" not in props:
                    props["Lens material"] = "NBK7"
                if "Thickness" not in props:
                    props["Thickness"] = 0.01
            
            # Aktualisierte Properties zurückschreiben
            fresh_component["properties"] = props
            
            # Verwende fresh_component statt component
            is_beam = (
                fresh_component.get("name", "").strip().lower() == "beam"
                or fresh_component.get("type", "").strip().lower() == "beam"
            )
            # Prüfe, ob schon ein Beam existiert
            for i in range(self.count()):
                c = self.item(i).data(QtCore.Qt.UserRole)
                if isinstance(c, dict) and (
                    c.get("name", "").strip().lower() == "beam"
                    or c.get("type", "").strip().lower() == "beam"
                ):
                    if is_beam:
                        event.ignore()
                        return
            # Füge Beam immer an Position 0 ein, andere Komponenten ans Ende
            if is_beam:
                item = QtWidgets.QListWidgetItem(fresh_component.get("name", "Unnamed"))  # fresh_component!
                item.setData(QtCore.Qt.UserRole, fresh_component)  # fresh_component!
                self.insertItem(0, item)
                event.acceptProposedAction()
            else:
                item = QtWidgets.QListWidgetItem(fresh_component.get("name", "Unnamed"))  # fresh_component!
                item.setData(QtCore.Qt.UserRole, fresh_component)  # fresh_component!
                self.addItem(item)
                event.acceptProposedAction()
            
        else:
            # Internes Verschieben innerhalb der Liste
            super().dropEvent(event)