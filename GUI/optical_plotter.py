import numpy as np
import pyqtgraph as pg

class OpticalSystemPlotter:
    def __init__(self, plotWidget, beam, matrices):
        self.plotWidget = plotWidget
        self.beam = beam
        self.matrices = matrices

    def plot_optical_system(self, z_start, wavelength, beam_radius, n, optical_system):
        """
        Plots the given optical system.
        """
        self.wavelength = wavelength
        self.beam_radius = beam_radius
        self.z_start = z_start
        
        self.plotWidget.clear()
        self.z_data, self.w_sag_data = self.beam.propagate_through_system(
            wavelength, self.beam.q_value(z_start, beam_radius, wavelength, n), optical_system
        )
        self.w_tan_data = self.w_sag_data

        self.z_data = np.array(self.z_data)
        self.w_sag_data = np.array(self.w_sag_data)
        self.w_tan_data = np.array(self.w_tan_data)

        self.plotWidget.setBackground('w')
        self.plotWidget.addLegend()
        self.plotWidget.showGrid(x=True, y=True)

        self.plotWidget.setLabel('left', 'Waist radius', units='m', color='#333333')
        self.plotWidget.setLabel('bottom', 'z', units='m', color='#333333')
        self.plotWidget.setTitle("Gaussian Beam Propagation", color='#333333')
        axis_pen = pg.mkPen(color='#333333')
        self.plotWidget.getAxis('left').setTextPen(axis_pen)
        self.plotWidget.getAxis('bottom').setTextPen(axis_pen)

        self.plotWidget.plot(self.z_data, self.w_sag_data, pen=pg.mkPen(color='b', width=2))
        self.plotWidget.plot(self.z_data, self.w_tan_data, pen=pg.mkPen(color='r', width=2))

        z_element = 0
        for element, param in optical_system:
            # Prüfe, ob das Element KEINE Propagation ist
            if not (hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__):
                self.plotWidget.addLine(x=z_element, pen=pg.mkPen(color='#333333'))
            # Bei Propagation z_element erhöhen
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                z_element += param[0]