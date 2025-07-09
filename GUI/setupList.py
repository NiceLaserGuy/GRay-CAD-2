from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
import json
import copy

class SetupList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

        # Lade Komponenten aus Generic.json
        try:
            with open("Library/Generic.json", "r", encoding="utf-8") as f:
                generic_data = json.load(f)
            components = generic_data.get("components", [])

            # Finde die gewünschten Komponenten anhand von type oder name
            def find_component(key, value):
                for comp in components:
                    if comp.get(key, "").strip().lower() == value:
                        return comp
                return None

            beam = find_component("name", "beam")
            propagation = find_component("name", "propagation")
            lens = find_component("name", "lens")

            # Füge sie in der gewünschten Reihenfolge hinzu
            for comp in [beam, propagation, lens, propagation]:
                if comp is not None:
                    item = QtWidgets.QListWidgetItem(comp.get("name", "Unnamed"))
                    item.setData(QtCore.Qt.UserRole, copy.deepcopy(comp))
                    self.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load components: {str(e)}")
            

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
                if "Lens material" not in props:
                    props["Lens material"] = "NBK7"
            
            if ctype == "LENS":
                if "Variable parameter" not in props:
                    props["Variable parameter"] = "Edit focal length"
                if "Plan lens" not in props:
                    props["Plan lens"] = True
                
            # Für Propagation  
            elif ctype == "PROPAGATION":
                if "Refractive index" not in props:
                    props["Refractive index"] = 1.0

            # Für dicke Linsen
            elif ctype == "THICK LENS":
                if "Material" not in props:
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
            QtCore.QTimer.singleShot(10, lambda: self.setCurrentItem(item))
            event.acceptProposedAction()

            
        else:
            # Internes Verschieben innerhalb der Liste
            super().dropEvent(event)