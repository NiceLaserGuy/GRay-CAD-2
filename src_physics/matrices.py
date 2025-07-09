import numpy as np


class Matrices:
    
    def __init__(self):
        pass
    
    def free_space(self, *args):
        distance, n = args
        """ABCD matrix for propagation through free space with refractive index n"""
        return np.array([[1, distance/n], [0, 1]])
    
    def curved_mirror_tangential(self, *args):
        radius_of_curvature, theta = args
        """ABCD matrix for a mirror in the tangential direction"""
        return np.array([[1, 0], [-2 / (radius_of_curvature * np.cos(theta)), 1]])

    def curved_mirror_sagittal(self, *args):
        radius_of_curvature, theta = args
        """ABCD matrix for a mirror in the sagittal direction"""
        return np.array([[1, 0], [(-2 * np.cos(theta)) / radius_of_curvature, 1]])
    
    def lens(self, *args):
        focal_length = args[0]
        """ABCD matrix for a thin lens"""
        return np.array([[1, 0], [-1/focal_length, 1]])
    
    def refraction_curved_interface(self, *args):
        """ABCD matrix for refraction at a curved interface"""
        radius_of_curvature= args[0]
        refractive_index_inital = args[1]
        refractive_index_final = args[2]
        return np.array([[1, 0],[(refractive_index_inital - refractive_index_final)/(refractive_index_final * radius_of_curvature), refractive_index_inital/refractive_index_final]])
    
    def ABCD(self, *args):
        """ABCD matrix for a system of optical elements"""
        A, B, C, D = args
        return np.array([[A, B], [C, D]])

