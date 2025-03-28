import config
import pyqtgraph as pg
import numpy as np
import config
from PyQt5.QtWidgets import QDialog, QVBoxLayout


class Plotter:
    def __init__(self):
        self.temp_resonator_setup = config.get_temp_resonator_setup()
        
    def plot_beamdiagram(self):
        """
        Opens a new window and plots the beam diagram using pyqtgraph.
        The data for the plot can be provided later.
        """
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

        # set the data for the plot
        length = np.linspace(1e-15,2*self.l1+self.lc+self.l3+2*l2 , 1e9) #Length of the resonator

        # Placeholder for the plot (to be replaced with actual data later)
        plot_widget.plot(length, waist_sagittal, pen=pg.mkPen(color='r', width=2), name="waist sagittal")
        plot_widget.plot(length, waist_tangential, pen=pg.mkPen(color='b', width=2), name="waist tangential")

        # Show the plot window
        plot_window.show()