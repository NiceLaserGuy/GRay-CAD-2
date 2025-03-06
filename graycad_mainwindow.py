#Python 3.10.2
# -*- coding: utf-8 -*-
"""
@author: Jens Gumm, TU Darmstadt, LQO-Group
"""

from PyQt6 import uic
from pyqtgraph import *
from os import path
from PyQt6.QtCore import *
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow

import pyqtgraph as pg
import logging

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set window icon
        self.setWindowIcon(QIcon(path.abspath(path.join(path.dirname(__file__), "/assets/TaskbarIcon.png"))))

        # Load the UI from a file in this path
        self.ui = uic.loadUi(path.abspath(path.join(path.dirname(__file__))) + "/interface.ui", self)
        
        
        
        