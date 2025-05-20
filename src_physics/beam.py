import numpy as np
from src_physics.matrices import Matrices
import pyqtgraph as pg

class Beam():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matrices = Matrices()

    def rayleigh_length(self, wavelength, beam_radius, n):
        """
        Calculate the Rayleigh length of a beam.

        Parameters:
        wavelength (float): Wavelength of the beam.
        n (float): Refractive index of the medium.

        Returns:
        float: Rayleigh length of the beam.
        """
        return (wavelength * n) / (np.pi * beam_radius**2)
    
    def propagate_q(self, q_in, ABCD):
        A, B, C, D = ABCD.flatten()
        return (A * q_in + B) / (C * q_in + D)

    def beam_radius(self, q, lambda_):
        return np.sqrt(-lambda_ / (np.pi * np.imag(1/q)))

    def propagate_through_system(self, wavelength, q_initial, elements):
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
        z_total = 0
        z_positions = [z_total]
        w_values = [self.beam_radius(q, lambda_)]
        
        for element, param in elements:
            if element == self.matrices.free_space:
                # For free space, calculate multiple points
                steps = 200
                dz = param / steps
                for i in range(steps):
                    ABCD = self.matrices(dz)
                    q = self.propagate_q(q, ABCD)
                    z_total += dz
                    z_positions.append(z_total)
                    w_values.append(self.beam_radius(q, lambda_))
            else:
                # For other elements (like lenses), just propagate once
                ABCD = element(param)
                q = self.propagate_q(q, ABCD)
                w_values.append(self.beam_radius(q, lambda_))
                z_positions.append(z_total)
        
        return z_positions, w_values