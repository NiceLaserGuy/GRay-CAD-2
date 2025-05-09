import config
import pyqtgraph as pg
import numpy as np
import config
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from Problems.resonator_types import *
from Problems.matrices import Matrices


class Plotter:
    def __init__(self):
        super().__init__()
        self.mat = Matrices()
        self.bowtie = BowTie()

    def q_transform(self, M, q_in):
        """Transformiert q_in mit einer ABCD-Matrix M."""
        A, B, C, D = M.flatten()
        return (A * q_in + B) / (C * q_in + D)

    def plot_beamdiagram(self):
        """
        Opens a new window and plots the beam diagram using pyqtgraph.
        The data for the plot can be provided later.
        """
        try:
            if config.get_temp_resonator_setup() is None or config.get_temp_light_field_parameters() is None or config.get_temp_resonator_type() is None:
                # Show a message box with the error message
                raise ValueError("Simulation in progress")
            self.temp_resonator_setup = config.get_temp_resonator_setup()
            self.resonator_type = config.get_temp_resonator_type()
            self.wavelength = config.get_temp_light_field_parameters()[0]  # Wavelength of the light
            self.lc = config.get_temp_light_field_parameters()[1]  # Length of the crystal
            self.nc = config.get_temp_light_field_parameters()[2]  # Refractive index of the crystal
        except ValueError:
            # Show a message box with the error message
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Simulation in progress")
            msg.setInformativeText("Please wait until the simulation is finished.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowTitle("Warning")
            msg.exec_()
            return
        
        self.step = 0.1 # mm
        self.z = 0
        self.waist_sagittal = []
        self.waist_tangential = []
        self.z_list = []

        
        

        if self.resonator_type == "BowTie":
            self.waist_sag, self.waist_tan, self.l1, self.l2, self.l3, self.theta, self.r1_sag, self.r1_tan, self.r2_sag, self.r2_tan = self.temp_resonator_setup
            
            self.z_R_sag = np.pi * self.waist_sag**2 / self.wavelength
            self.q_sag = self.z - 1j * self.z_R_sag

            self.z_R_tan = np.pi * self.waist_tan**2 / self.wavelength
            self.q_tan = self.z - 1j * self.z_R_tan

            while self.z < self.lc/2:
                self.qz = self.q_transform(self.mat.free_space(self.z, self.nc), self.q_sag)
                self.z_list.append(self.z)
                self.waist_sagittal.append(self.qz)
                self.z += self.step

            while self.z < self.l1:
                self.qz = self.q_transform(self.mat.free_space(self.z, 1)@self.mat.free_space(self.lc/2, self.nc), self.q_sag)
                self.z_list.append(self.z)
                self.waist_sagittal.append(self.qz)
                self.z += self.step

        # Create a new dialog window for the plot
        self.plot_window = QDialog()
        self.plot_window.setWindowTitle("Beam Diagram")
        self.plot_window.resize(800, 600)

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
        self.plot_window.setLayout(layout)

        waist_sagittal_real = [np.abs(q) for q in self.waist_sagittal]
        # Placeholder for the plot (to be replaced with actual data later)
        plot_widget.plot(self.z_list, waist_sagittal_real, pen=pg.mkPen(color='r', width=2), name="waist sagittal")
        #plot_widget.plot(pos, waist_tangential, pen=pg.mkPen(color='b', width=2), name="waist tangential")

        # Show the plot window
        self.plot_window.show()
        

'''wavelength = 1064e-6  # mm (1064 nm)
z_R = 2.0             # Rayleigh-Länge
q_in = 1j * z_R       # Start-q

# System: Freiraum (50 mm) → Linse (f=100 mm) → Freiraum (100 mm)
elements = [
    ("free", 50),
    ("lens", 10),
    ("free", 100)
]

# Auflösung innerhalb von Freiraumstrecken
dz = 1.0  # mm

# ----------------------------
# Simulation durchführen
# ----------------------------

z_list = []
w_list = []
q_current = q_in
z_current = 0.0
M_accumulated = np.eye(2)

for elem in elements:
    typ, param = elem
    if typ == "free":
        num_steps = int(param / dz)
        for i in range(num_steps):
            step_matrix = np.array([[1, dz], [0, 1]])
            M_accumulated = step_matrix @ M_accumulated
            qz = q_transform(M_accumulated, q_in)
            wz = w_from_q(qz, wavelength)
            z_current += dz
            z_list.append(z_current)
            w_list.append(wz)
    elif typ == "lens":
        lens_matrix = np.array([[1, 0], [-1/param, 1]])
        M_accumulated = lens_matrix @ M_accumulated
        # Optional: auch hier Punkt speichern
        qz = q_transform(M_accumulated, q_in)
        wz = w_from_q(qz, wavelength)
        z_list.append(z_current)
        w_list.append(wz)
'''