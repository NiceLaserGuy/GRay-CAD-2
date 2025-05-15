import config
import pyqtgraph as pg
import numpy as np
import config
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from src_resonator.resonator_types import *
from src_physics.matrices import Matrices
import sympy as sym


class Plotter:
    def __init__(self):
        super().__init__()
        self.mat = Matrices()
        
    def mult(self, mat1,*argv):

        Mat = mat1
        for arg in argv:
            Mat = np.dot(Mat, arg)
        return Mat
    
    def Zr(self, wo, lam):

        zr = np.pi * wo**2 / lam
        return zr
    
    def q1_inv_func(self, z, w0, lam, mat):
        
        A = mat[0][0]
        B = mat[0][1]
        C = mat[1][0]
        D = mat[1][1]
        zr = self.Zr(w0, lam)
        real = (A*C*(z**2 + zr**2) + z*(A*D + B*C) + B*D) / (A**2*(z**2 + zr**2) + 2*A*B*z + B**2) 
        imag = -zr * (A*D-B*C) / (A**2 *(z**2 + zr**2) + 2*A*B*z + B**2) 
        R = 1/real
        w = (-lam / imag / np.pi)**.5
        return R, w

    def plot_beamdiagram(self):

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

        self.z, self.w_sag, self.w_tan, self.generate_data()

        self.w_sag_positive = self.w_sag

        plot_widget.plot(self.z, self.w_sag_positive, pen=pg.mkPen(color='r', width=2), name="waist sagittal")
        #plot_widget.plot(rang, w_sag_negative, pen=pg.mkPen(color='r', width=2))
        #plot_widget.plot(rang, w_tan_positive, pen=pg.mkPen(color='b', width=2), name="waist tangential")
        #plot_widget.plot(rang, w_tan_negative, pen=pg.mkPen(color='b', width=2))

        # Show the plot window
        self.plot_window.show()

    def generate_data(self):
        # Check if the simulation is in progress
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
            print("expecting error")
            # Show a message box with the error message
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Simulation in progress")
            msg.setInformativeText("Please wait until the simulation is finished.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setWindowTitle("Warning")
            msg.exec_()
            return
    
        z_list, w_sag_list, w_tan_list = [], [], []
        
        self.selected_class_name = self.resonator_type
        if self.selected_class_name == "BowTie":
            self.resonator_type = src_resonator.resonator.BowTie()
            self.waist_sag, self.waist_tan, self.l1, self.l2, self.l3, self.theta, self.r1_sag, self.r1_tan, self.r2_sag, self.r2_tan = self.temp_resonator_setup
            self.mat_sag = self.resonator_type.set_roundtrip_sagittal(self.nc, self.lc, 1, self.l1, self.l3, self.r1_sag, self.r2_sag, self.theta)
            self.mat_tan = self.resonator_type.set_roundtrip_tangential(self.nc, self.lc, 1, self.l1, self.l3, self.r1_tan, self.r2_tan, self.theta)
        
        else:
            self.resonator_type = None
        if self.selected_class_name is None:
            QMessageBox.critical(
                self.resonator_window,
                "Error",
                "No valid resonator type selected. Please select a valid resonator type."
            )
            return z_list, w_sag_list, w_tan_list