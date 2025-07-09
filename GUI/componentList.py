from PyQt5 import QtWidgets, QtCore
import json
import copy

class ComponentList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.setDragEnabled(True)

    def mimeData(self, items):
        item = items[0]
        component = item.data(QtCore.Qt.UserRole)
        
        # Erstelle eine tiefe Kopie der ursprünglichen Komponente
        clean_component = copy.deepcopy(component)
        
        mime = QtCore.QMimeData()
        mime.setData("application/x-component", QtCore.QByteArray(json.dumps(clean_component).encode()))
        return mime