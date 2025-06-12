import numpy as np
from src_physics.matrices import Matrices
from PyQt5.QtWidgets import QMessageBox
import pyqtgraph as pg
from numba import njit

@njit
def beam_radius_numba(q, wavelength, n):
    return np.sqrt(-wavelength / (np.pi * n * np.imag(1/q)))


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
        zr = (np.pi * beam_radius**2 * n) / (wavelength)
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
        return np.sqrt(-wavelength / (np.pi * n * np.imag(1/q)))

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
        z_total = 0.0
        z_positions = [z_total]
        w_values = [beam_radius_numba(q, wavelength, n)]
        for i in range(n_steps):
            # ABCD-Matrix für Freiraum
            A, B, C, D = 1, dz, 0, 1
            q = (A * q + B) / (C * q + D)
            z_total += dz
            z_positions.append(z_total)
            w_values.append(beam_radius_numba(q, wavelength, n))
        return q, z_total, z_positions, w_values

    def propagate_through_system(self, wavelength, q_initial, elements, n=1):
        """
        Propagate beam through a sequence of optical elements

        Args:
            q_initial: Initial q parameter
            elements: List of tuples (element_function, parameter)
        Returns:
            z_positions, w_values: Lists of positions and beam radii
        """
        lambda_ = wavelength
        q = q_initial
        z_total = 0.0
        z_positions = [z_total]
        w_values = [self.beam_radius(q, lambda_, n)]

        for element, param in elements:
            # Prüfe auf gültige Parameter für Freiraum
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                length = param[0]
                n_medium = param[1]
                try:
                    length_val = float(length)
                    n_val = float(n_medium)
                    if length_val <= 0 or n_val <= 0:
                        # Ungültige Werte: überspringen oder abbrechen
                        continue
                except Exception:
                    continue
                dz = 1e-4  # Schrittweite
                steps = int(np.ceil(length_val / dz))
                q, z_inc, zs, ws = Beam.propagate_free_space(q, dz, steps, lambda_, n_val)
                z_positions.extend([z_total + z for z in np.array(zs)[1:]])
                w_values.extend(ws[1:])
                z_total += length_val
            else:
                # Optisches Element: q ändern, aber z bleibt gleich!
                if isinstance(param, tuple):
                    ABCD = element(*param)
                else:
                    ABCD = element(param)
                q = self.propagate_q(q, ABCD)
                w_values.append(self.beam_radius(q, lambda_, n))
                z_positions.append(z_total)
        return z_positions, w_values