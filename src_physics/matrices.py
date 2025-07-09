import numpy as np


class Matrices:
    
    def __init__(self):
        pass
    
    def free_space(self, *args):
        """ABCD matrix for propagation through free space with refractive index n"""
        distance, n = args
        return np.array([[1, distance/n], [0, 1]])
    
    def curved_mirror_tangential(self, *args):
        """ABCD matrix for a mirror in the tangential direction"""
        radius_of_curvature, theta = args
        return np.array([[1, 0], [-2 / (radius_of_curvature * np.cos(theta)), 1]])

    def curved_mirror_sagittal(self, *args):
        """ABCD matrix for a mirror in the sagittal direction"""
        radius_of_curvature, theta = args
        return np.array([[1, 0], [(-2 * np.cos(theta)) / radius_of_curvature, 1]])
    
    def lens(self, *args):
        """ABCD matrix for a thin lens"""
        focal_length = args[0]
        return np.array([[1, 0], [-1/focal_length, 1]])
    
    def refraction_curved_interface(self, *args):
        """ABCD matrix for refraction at a curved interface"""
        radius_of_curvature, refractive_index_inital, refractive_index_final = args
        return np.array([[1, 0],[(refractive_index_inital - refractive_index_final)/(refractive_index_final * radius_of_curvature), refractive_index_inital/refractive_index_final]])
    
    def ABCD(self, *args):
        """ABCD matrix for a system of optical elements"""
        A, B, C, D = args
        return np.array([[A, B], [C, D]])

