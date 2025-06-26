from PyQt5 import QtWidgets, QtGui, QtCore
import sys

class CustomMessageBox(QtWidgets.QDialog):
    def __init__(self, parent=None, title="Fehler", message="", gif_path="your_animation.gif"):
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QtWidgets.QVBoxLayout()

        # GIF einfügen
        gif_label = QtWidgets.QLabel()
        movie = QtGui.QMovie(gif_path)
        gif_label.setMovie(movie)
        movie.start()

        # Text einfügen
        text_label = QtWidgets.QLabel(message)
        text_label.setWordWrap(True)

        layout.addWidget(gif_label)
        layout.addWidget(text_label)

        # OK Button
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)
