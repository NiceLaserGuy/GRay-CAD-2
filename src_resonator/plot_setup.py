import config
import pyqtgraph as pg
import numpy as np
import config
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from Problems.resonator_types import BowTie


class Plotter:
    def __init__(self):
        self.temp_resonator_setup = config.get_temp_resonator_setup()
        self.res = BowTie()
        
    def plot_beamdiagram(self):
        """
        Opens a new window and plots the beam diagram using pyqtgraph.
        The data for the plot can be provided later.
        """

        # Überprüfen, ob die temporären Daten vorhanden sind
        if not self.temp_resonator_setup:
            raise ValueError("No temporary resonator setup data found.")

        # Extrahiere die gespeicherten Variablen
        l1, l3, theta, mirror1, mirror2 = self.temp_resonator_setup
        nc = self.res.nc
        lc = self.res.lc
        wavelength = self.res.wavelength

        # set the data for the plot           
        self.res.set_roundtrip_direction()
        self.res.set_roundtrip_sagittal()
        self.res.set_roundtrip_tangential()
        length = np.linspace(1e-30,length, 1e9) #Length of the resonator

        waist_sagittal = []
        waist_tangential = []

        # Create a new dialog window for the plot
        plot_window = QDialog(self.resonator_window)
        plot_window.setWindowTitle("Beam Diagram")
        plot_window.resize(800, 600)

        # Create a pyqtgraph PlotWidget
        styles = {'color':'black', 'font-size':'15px'}  # Styles for the labels
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('white')
        plot_widget.setTitle("Beam Diagram", **styles)
        plot_widget.setLabel('left', 'waist / μm', **styles)
        plot_widget.setLabel('bottom', 'length / mm', **styles)
        plot_widget.showGrid(x=True, y=True)
        plot_widget.addLegend()

        # Create a layout and add the PlotWidget
        layout = QVBoxLayout()
        layout.addWidget(plot_widget)
        plot_window.setLayout(layout)

        # Placeholder for the plot (to be replaced with actual data later)
        plot_widget.plot(length, waist_sagittal, pen=pg.mkPen(color='r', width=2), name="waist sagittal")
        plot_widget.plot(length, waist_tangential, pen=pg.mkPen(color='b', width=2), name="waist tangential")

        # Show the plot window
        plot_window.show()