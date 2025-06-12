from PyQt5 import QtWidgets, QtCore
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

            beam = find_component("type", "beam") or find_component("name", "beam")
            propagation = find_component("type", "propagation") or find_component("name", "propagation")
            lens = find_component("type", "lens") or find_component("name", "lens")

            # Füge sie in der gewünschten Reihenfolge hinzu
            for comp in [beam, propagation, lens, propagation]:
                if comp is not None:
                    item = QtWidgets.QListWidgetItem(comp.get("name", "Unnamed"))
                    item.setData(QtCore.Qt.UserRole, copy.deepcopy(comp))
                    self.addItem(item)
        except Exception as e:
            print(f"Fehler beim Laden von Generic.json: {e}")

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