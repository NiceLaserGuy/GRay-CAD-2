from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from os import path
from graycad_mainwindow import MainWindow
from deap import base, creator

class Start:
    def __init__(self):

        # Initialize DEAP creator classes only once at application start
        if not hasattr(creator, "FitnessMin"):
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        if not hasattr(creator, "Particle"):
            creator.create("Particle", list, fitness=creator.FitnessMin, 
                         speed=list, smin=None, smax=None, best=None)
            

        self.app = QApplication([])
        self.app.setWindowIcon(QIcon(path.abspath(path.join(path.dirname(__file__), 
                             "TaskbarIcon.png"))))
        self.window = MainWindow()
        self.window.show()

    def run(self):
        self.app.exec()

if __name__ == "__main__":
    app = Start()
    app.run()