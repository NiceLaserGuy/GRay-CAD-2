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
    
    def roundtrip_tangential(self, nc, lc, n0, l1, l3, r1_tan, r2_tan, theta):
        """Calculate the roundtrip matrix for the tangential plane"""
        l2 = (2 * l1 + lc + l3) / (2 * np.cos(theta))
        return np.dot(
            self.free_space(lc / 2, nc),
            np.dot(
                self.free_space(l1, n0),
                np.dot(
                    self.curved_mirror_tangential(r2_tan, theta),
                    np.dot(
                        self.free_space(l2, n0),
                        np.dot(
                            self.curved_mirror_tangential(r1_tan, theta),
                            np.dot(
                                self.free_space(l3, n0),
                                np.dot(
                                    self.curved_mirror_tangential(r1_tan, theta),
                                    np.dot(
                                        self.free_space(l2, n0),
                                        np.dot(
                                            self.curved_mirror_tangential(r2_tan, theta),
                                            np.dot(
                                                self.free_space(l1, n0),
                                                self.free_space(lc / 2, nc),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )


    def roundtrip_sagittal(self, nc, lc, n0, l1, l3, r1_sag, r2_sag, theta):
        """Calculate the roundtrip matrix for the sagittal plane"""
        l2 = (2 * l1 + lc + l3) / (2 * np.cos(theta))
        return np.dot(
            self.free_space(lc / 2, nc),
            np.dot(
                self.free_space(l1, n0),
                np.dot(
                    self.curved_mirror_sagittal(r2_sag, theta),
                    np.dot(
                        self.free_space(l2, n0),
                        np.dot(
                            self.curved_mirror_sagittal(r1_sag, theta),
                            np.dot(
                                self.free_space(l3, n0),
                                np.dot(
                                    self.curved_mirror_sagittal(r1_sag, theta),
                                    np.dot(
                                        self.free_space(l2, n0),
                                        np.dot(
                                            self.curved_mirror_sagittal(r2_sag, theta),
                                            np.dot(
                                                self.free_space(l1, n0),
                                                self.free_space(lc / 2, nc),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )