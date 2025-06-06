from PyQt5 import QtWidgets, QtCore
import json

class ComponentList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.setDragEnabled(True)

    def mimeData(self, items):
        item = items[0]
        component = item.data(QtCore.Qt.UserRole)
        mime = QtCore.QMimeData()
        mime.setData("application/x-component", QtCore.QByteArray(json.dumps(component).encode()))
        return mime