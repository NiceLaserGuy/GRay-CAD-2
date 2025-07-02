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
    
    def thick_lens(self, *args):
        """ABCD matrix for a thick lens"""
        radius_of_curvature_in = args[0]
        radius_of_curvature_out = args[1]
        thickness = args[2]
        refractive_index_lens = args[3]
        refractive_index_before = args[4]
        refractive_index_behind = args[5]
        s1 = np.array([[1, 0],[(refractive_index_lens - refractive_index_before)/(refractive_index_lens * radius_of_curvature_in), refractive_index_before/refractive_index_lens]])
        t = np.array([[1, thickness],[0, 1]])
        s2 = np.array([[1, 0],[(refractive_index_behind - refractive_index_lens)/radius_of_curvature_out, refractive_index_lens/refractive_index_behind]])
        return np.matmul(np.matmul(s2, t), s1)
    
    def ABCD(self, *args):
        """ABCD matrix for a system of optical elements"""
        A, B, C, D = args
        return np.array([[A, B], [C, D]])

