import numpy as np

class Matrices:
    
    def __init__(self):
        pass
    
    def free_space(self, *args):
        distance, n = args
        """ABCD matrix for propagation through free space with refractive index n"""
        return np.array([[1, distance/n], [0, 1]])
    
    def interface(self, *args):
        n1, n2 = args
        """ABCD matrix for refraction at a planar interface"""
        return np.array([[1, 0], [0, n1/n2]])
    
    def curved_mirror_tangential(self, *args):
        radius_of_curvature, theta = args
        """ABCD matrix for a mirror in the tangential direction"""
        return np.array([[1, 0], [-2 / (radius_of_curvature * np.cos(theta)), 1]])

    def curved_mirror_sagittal(self, *args):
        radius_of_curvature, theta = args
        """ABCD matrix for a mirror in the sagittal direction"""
        return np.array([[1, 0], [(-2 * np.cos(theta)) / radius_of_curvature, 1]])

