class Start:
    def __init__(self):
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QIcon
        from os import path
        from graycad_mainwindow import MainWindow

        self.app = QApplication([])
        self.app.setWindowIcon(QIcon(path.abspath(path.join(path.dirname(__file__), "TaskbarIcon.png"))))
        self.window = MainWindow()
        self.window.show()

    def run(self):
        self.app.exec()

if __name__ == "__main__":
    app = Start()
    app.run()