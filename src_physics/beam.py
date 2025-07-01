import numpy as np
from src_physics.matrices import Matrices
from PyQt5.QtWidgets import QMessageBox
import pyqtgraph as pg
from numba import njit
import time

@njit
def beam_radius_numba(q, wavelength, n):
    return np.sqrt(-wavelength / (np.pi * np.imag(1/q)))

class Beam():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matrices = Matrices()

    def q_value(self, z, beam_radius, wavelength, n):
        """
        Calculate the q parameter of a Gaussian beam.

        Parameters:
        w (float): Beam radius.
        wavelength (float): Wavelength of the beam.
        n (float): Refractive index of the medium.

        Returns:
        complex: q parameter of the beam.
        """
        if beam_radius <= 0:
            QMessageBox.critical(None, "Error", "Beam radius must be greater than zero.")
            return None
        zr = (np.pi * beam_radius**2) / (wavelength)
        return - z + (1j * zr)

    def beam_radius(self, q, wavelength, n):
        """
        Calculate the beam radius from the q parameter.

        Parameters:
        q (complex): q parameter of the beam.
        wavelength (float): Wavelength of the beam.

        Returns:
        float: Beam radius.
        """
        return np.sqrt(-wavelength / (np.pi *  np.imag(1/q)))

    def rayleigh_length(self, wavelength, beam_radius, n=1):
        """
        Calculate the Rayleigh length of a beam.

        Parameters:
        wavelength (float): Wavelength of the beam.
        n (float): Refractive index of the medium.

        Returns:
        float: Rayleigh length of the beam.
        """
        return np.imag(self.q_value(0, beam_radius, wavelength, n))

    def radius_of_curvature(self, z, waist, wavelength, n=1):
        """
        Calculate the radius of curvature of a beam.

        Parameters:
        q (complex): q parameter of the beam.
        wavelength (float): Wavelength of the beam.
        n (float): Refractive index of the medium.

        Returns:
        float: Radius of curvature of the beam.
        """
        
        zr = self.rayleigh_length(wavelength, waist, n)
        return z*(1+(zr/z)**2) if z != 0 else np.inf
    
    def propagate_q(self, q_in, ABCD):
        A, B, C, D = ABCD.flatten()
        return (A * q_in + B) / (C * q_in + D)
    
    @staticmethod
    @njit
    def propagate_free_space(q_start, dz, n_steps, wavelength, n):
        q = q_start
        z_positions = np.empty(n_steps + 1, dtype=np.float64)
        w_values = np.empty(n_steps + 1, dtype=np.float64)
        z_total = 0.0
        z_positions[0] = z_total
        w_values[0] = beam_radius_numba(q, wavelength, n)
        for i in range(1, n_steps + 1):
            # ABCD-Matrix für Freiraum
            A, B, C, D = 1, dz/n, 0, 1
            q = (A * q + B) / (C * q + D)
            z_total += dz
            z_positions[i] = z_total
            w_values[i] = beam_radius_numba(q, wavelength, n)
        return q, z_total, z_positions, w_values

    def propagate_through_system(self, wavelength, q_initial, elements, z_array, res, n=1):
        lambda_ = wavelength
        q = q_initial
        z_total = 0.0
        z_positions = [0.0]
        w_values = [self.beam_radius(q, lambda_, n)]
        steps = res

        # Berechung der Länge des optischen Systems
        z_total = 0.0
        length_plot = 0.0
        for element, param in elements:
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                length_plot += param[0]

        # Vorwärts durch das optische System propagieren
        for element, param in elements:
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                length = param[0]
                n_medium = param[1]
                try:
                    length_val = float(length)
                    n_val = float(n_medium)
                    if length_val <= 0 or n_val <= 0:
                        continue
                except Exception:
                    continue
                dz = np.min(np.diff(np.sort(np.linspace(np.min(z_array), np.max(z_array), res))))
                length_plot = np.max(z_array) - np.min(z_array)
                steps = int(np.ceil(length_val/dz)) -1
                try:
                    q, z_inc, zs, ws = Beam.propagate_free_space(q, dz, steps, lambda_, n_val)
                except Exception:
                    continue
                z_positions = np.concatenate((z_positions, z_total + zs[1:]))
                w_values = np.concatenate((w_values, ws[1:]))
                z_total += length_val
            else:
                if isinstance(param, tuple):
                    ABCD = element(*param)
                else:
                    ABCD = element(param)
                q = self.propagate_q(q, ABCD)
                w_values = np.concatenate((w_values, [self.beam_radius(q, lambda_, n)]))
                z_positions = np.concatenate((z_positions, [z_total]))
        z_setup = z_total

        # Weiter nach dem letzten optischen Element
        z_end = np.max(z_array)
        if z_total < z_end:
            length_val = z_end - z_total
            dz = np.min(np.diff(np.sort(np.linspace(z_total, z_end, res))))
            steps = int(np.ceil(length_val / dz))
            try:
                q, z_inc, zs, ws = Beam.propagate_free_space(q, dz, steps, lambda_, n)
                z_positions = np.concatenate((z_positions, z_total + zs[1:]))
                w_values = np.concatenate((w_values, ws[1:]))
            except Exception:
                return
            
        '''# Rückwärts vor das erste optische Element
        z_start = np.min(z_array)
        if z_start < 0:
            length_val = -z_start
            dz = np.min(np.diff(np.sort(np.linspace(0, z_start, res))))
            steps = int(np.ceil(length_val / dz))
            q_back = q_initial
            try:
                q_back, z_inc, zs, ws = Beam.propagate_free_space(q_back, -dz, steps, lambda_, n)
                z_positions = np.concatenate((z_start + zs[:-1], z_positions))
                w_values = np.concatenate((ws[:-1], w_values))
            except Exception:
                return'''

        return z_positions, w_values, z_setup