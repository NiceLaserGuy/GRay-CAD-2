import numpy as np

class Matrices:
    
    def __init__(self):
        pass
    
    def free_space(self, distance, n):
        """ABCD matrix for propagation through free space with refractive index n"""
        return np.array([[1, distance], [0, 1/n]])
    
    def interface(self, n1, n2):
        """ABCD matrix for refraction at a planar interface"""
        return np.array([[1, 0], [0, n1/n2]])
    
    def curved_mirror_tangential(self, radius_of_curvature, theta):
        """ABCD matrix for a mirror in the tangential direction"""
        return np.array([[1, 0], [-2 / (radius_of_curvature * np.cos(np.radians(theta))), 1]])

    def curved_mirror_sagittal(self, radius_of_curvature, theta):
        """ABCD matrix for a mirror in the sagittal direction"""
        return np.array([[1, 0], [-2 * np.cos(np.radians(theta)) / radius_of_curvature, 1]])
    
    def stability(self, r1, r2, d, n1, n2):
        """Calculate the stability of a resonator"""
        m = self.resonator_matrix(r1, r2, d, n1, n2)
        return m[0, 0] + m[1, 1] - 2
    
    def q_parameter(self, r1, r2, d, n1, n2):
        """Calculate the q-parameter of a resonator"""
        m = self.resonator_matrix(r1, r2, d, n1, n2)
        return (m[0, 1] * n2 - m[1, 0]) / (m[0, 0] - m[1, 1])