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

    def propagate_through_system(self, wavelength, q_initial, elements, n=1):
        lambda_ = wavelength
        q = q_initial
        z_total = 0.0
        z_positions = [0.0]
        w_values = [self.beam_radius(q, lambda_, n)]

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
                dz = 1e-5  # Schrittweite
                steps = int(np.ceil(length_val / dz))
                q, z_inc, zs, ws = Beam.propagate_free_space(q, dz, steps, lambda_, n_val)
                # Die neuen Werte an den bisherigen Array-Stand anhängen (ohne das erste Element doppelt zu nehmen)
                z_positions = np.concatenate((np.array(z_positions), z_total + zs[1:]))
                w_values = np.concatenate((np.array(w_values), ws[1:]))
                z_total += length_val
            else:
                # Optisches Element: q ändern, aber z bleibt gleich!
                if isinstance(param, tuple):
                    ABCD = element(*param)
                else:
                    ABCD = element(param)
                q = self.propagate_q(q, ABCD)
                w_values = np.concatenate((w_values, [self.beam_radius(q, lambda_, n)]))
                z_positions = np.concatenate((z_positions, [z_total]))
        return z_positions, w_values
    
    def propagate_to_z_array(self, wavelength, q_initial, elements, z_array, n=1):
        lambda_ = wavelength
        q = q_initial
        z_total = 0.0
        z_element_edges = [0.0]
        q_list = [q_initial]

        # 1. Finde die Grenzen der optischen Elemente und berechne q an jedem Element-Übergang
        for element, param in elements:
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                length = float(param[0])
                n_medium = float(param[1])
                z_total += length
                z_element_edges.append(z_total)
            else:
                if isinstance(param, tuple):
                    ABCD = element(*param)
                else:
                    ABCD = element(param)
                q = self.propagate_q(q, ABCD)
                q_list.append(q)

        z_min_sys = z_element_edges[0]
        z_max_sys = z_element_edges[-1]

        w_values = np.zeros_like(z_array)
        for i, z in enumerate(z_array):
            # Bereich vor dem System: nutze Start-q
            if z < z_min_sys:
                idx = 0
                z_local = z - z_element_edges[0]
                q_local = q_list[0]
                n_medium = 1.0
            # Bereich nach dem System: nutze End-q
            elif z > z_max_sys:
                idx = len(q_list) - 1
                z_local = z - z_element_edges[-1]
                q_local = q_list[-1]
                n_medium = 1.0
            # Bereich im System
            else:
                idx = np.searchsorted(z_element_edges, z, side='right') - 1
                z_local = z - z_element_edges[idx]
                q_local = q_list[idx]
                n_medium = 1.0
                for j in range(idx, -1, -1):
                    elem, param = elements[j]
                    if hasattr(elem, "__func__") and elem.__func__ is self.matrices.free_space.__func__:
                        n_medium = float(param[1])
                        break
            # Freiraum-Propagation
            A, B, C, D = 1, z_local / n_medium, 0, 1
            q_z = (A * q_local + B) / (C * q_local + D)
            w_values[i] = self.beam_radius(q_z, wavelength, n_medium)
        return w_values