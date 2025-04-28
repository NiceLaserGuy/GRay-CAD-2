import config
import pyqtgraph as pg
import numpy as np
import config
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from Problems.resonator_types import *
from src_resonator.problem import Problem

class Plotter:
    def __init__(self):
        super().__init__()

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
            self.lc = config.get_temp_light_field_parameters()[1]  # Length of the cavity
            self.nc = config.get_temp_light_field_parameters()[2]  # Number of cycles
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
        
        waist_sagittal = []
        waist_tangential = []

        if self.resonator_type == "BowTie":
            self.l1, self.l2, self.l3, self.theta, self.r1_sag, self.r1_tan, self.r2_sag, self.r2_tan = self.temp_resonator_setup

            bowtie = BowTie()
            problem = Problem()
            # Hole die Abschnitte in der richtigen Reihenfolge
            sections = bowtie.set_roundtrip_direction(self.lc, self.l1, self.l3, self.theta)
            # Hole die Matrizen für den sagittalen Strahlverlauf
            matrices = bowtie.set_roundtrip_sagittal(self.nc, self.lc, 1, self.l1, self.l3, self.r1_sag, self.r2_sag, self.theta)
            for m in matrices:
                roundtrip_sag = np.matmul(m, roundtrip_sag) if roundtrip_sag is not None else m

            # Diskretisierung pro Abschnitt
            step = 0.1 # mm
            waist_sagittal = []
            waist_tangential = []
            pos = 0
            
            m_sag = np.abs((mat_total[0, 0] + mat_total[1, 1]) / 2)
            b_sag = np.abs(mat_total[0, 1])
            waist = np.sqrt(((b_sag * self.wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_sag ** 2)))))

            # Startmatrix (Einheitsmatrix)
            mat_total = np.identity(2)

            for mat in zip(matrices):
                steps = max(1, int(sec_len / step))
                for _ in range(steps):
                    mat_total = mat @ mat_total
                    
                    waist_sagittal.append(waist)
                    length.append(pos)
                    pos += step

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

        # Placeholder for the plot (to be replaced with actual data later)
        plot_widget.plot(length, waist_sagittal, pen=pg.mkPen(color='r', width=2), name="waist sagittal")
        plot_widget.plot(length, waist_tangential, pen=pg.mkPen(color='b', width=2), name="waist tangential")

        # Show the plot window
        self.plot_window.show()
        
        
import numpy as np
import matplotlib.pyplot as plt

def abcd_multiply(matrices):
    """Multipliziert eine Liste von 2x2 ABCD-Matrizen."""
    M = np.eye(2)
    for m in matrices:
        M = np.dot(m, M)
    return M

def q_transform(M, q_in):
    """Transformiert q_in mit einer ABCD-Matrix M."""
    A, B, C, D = M.flatten()
    return (A * q_in + B) / (C * q_in + D)

def w_from_q(q, wavelength):
    """Berechnet Strahlradius w(z) aus q(z)."""
    q_inv = 1 / q
    Im_qinv = q_inv.imag
    if Im_qinv == 0:
        return np.nan
    return np.sqrt(-wavelength / (np.pi * Im_qinv))

# ----------------------------
# Beispielsystem definieren
# ----------------------------

wavelength = 1064e-6  # mm (1064 nm)
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

# ----------------------------
# Plot
# ----------------------------

plt.figure(figsize=(8, 4))
plt.plot(z_list, w_list, label="Strahlradius $w(z)$", color="blue")
plt.xlabel("z [mm]")
plt.ylabel("w(z) [mm]")
plt.title("Strahlradius entlang des Systems")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
