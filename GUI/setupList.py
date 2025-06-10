from PyQt5 import QtWidgets, QtCore
import json

class SetupList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

        # Beam wie in Generic.json hinzufügen
        beam_component = {
            "type": "GENERIC",
            "name": "Beam",
            "manufacturer": "",
            "properties": {
                "Wavelength": 514E-9,
                "Waist radius sagittal": 1.0E-3,
                "Waist radius tangential": 1.0E-3,
                "Waist position sagittal": 0.0,
                "Waist position tangential": 0.0,
                "Rayleigh range sagittal": 0.0,
                "Rayleigh range tangential": 0.0
            }
        }
        beam_item = QtWidgets.QListWidgetItem(beam_component["name"])
        beam_item.setData(QtCore.Qt.UserRole, beam_component)
        self.addItem(beam_item)
        
        # Erste Propagation
        propagation1 = {
            "type": "GENERIC",
            "name": "Propagation",
            "manufacturer": "",
            "properties": {
                "Length": 0.2,
                "refractive index": 1.0
            }
        }
        prop1_item = QtWidgets.QListWidgetItem(propagation1["name"])
        prop1_item.setData(QtCore.Qt.UserRole, propagation1)
        self.addItem(prop1_item)

        # Linse
        lens = {
            "type": "GENERIC",
            "name": "Lens",
            "manufacturer": "",
            "properties": {
                "Focal length tangential": 0.1,
                "Focal length sagittal": 0.1,
                "Radius of curvature tangential": 0.1,
                "Radius of curvature sagittal": 0.1,
                "Thickness": 0.01
            }
        }
        lens_item = QtWidgets.QListWidgetItem(lens["name"])
        lens_item.setData(QtCore.Qt.UserRole, lens)
        self.addItem(lens_item)

        # Zweite Propagation
        propagation2 = {
            "type": "GENERIC",
            "name": "Propagation",
            "manufacturer": "",
            "properties": {
                "Length": 0.3,
                "refractive index": 1.0
            }
        }
        prop2_item = QtWidgets.QListWidgetItem(propagation2["name"])
        prop2_item.setData(QtCore.Qt.UserRole, propagation2)
        self.addItem(prop2_item)

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
            is_beam = (
                component.get("name", "").strip().lower() == "beam"
                or component.get("type", "").strip().lower() == "beam"
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
                item = QtWidgets.QListWidgetItem(component.get("name", "Unnamed"))
                item.setData(QtCore.Qt.UserRole, component)
                self.insertItem(0, item)
                self.setCurrentItem(item)
                event.acceptProposedAction()
            else:
                item = QtWidgets.QListWidgetItem(component.get("name", "Unnamed"))
                item.setData(QtCore.Qt.UserRole, component)
                self.addItem(item)
                self.setCurrentItem(item)
                event.acceptProposedAction()
        else:
            # Internes Verschieben innerhalb der Liste
            super().dropEvent(event)