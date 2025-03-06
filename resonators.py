from matrices import Matrices
import numpy as np

class Resonator:
    
    def __init__(self):
        self.matrices = Matrices()
    
    def bow_tie_resonator_matrix(self, r1, r2, d, n1, n2, theta):
        """ABCD matrix for a resonator with four mirrors"""
        m1 = self.matrices.curved_mirror_tangential(r1, theta)
        m2 = self.matrices.free_space(d, n1)
        m3 = self.matrices.curved_mirror_tangential(r2, theta)
        m4 = self.matrices.free_space(d, n2)
        return np.dot(m4, np.dot(m3, np.dot(m2, m1)))
    
    def stability(self, r1, r2, d, n1, n2):
        """Calculate the stability of a resonator"""
        m = self.resonator_matrix(r1, r2, d, n1, n2)
        return m[0, 0] + m[1, 1] - 2
    
    def roundtrip_tangential(self, nc, lc, n0, l1, l2, l3, l4, r1_tan, r2_tan, r3_tan, r4_tan, theta1):
        """Calculate the roundtrip matrix for the tangential plane"""
        return np.dot(
            self.matrices.free_space(nc, lc/2),
            np.dot(
                self.matrices.free_space(n0, l4),
                np.dot(
                    self.matrices.curved_mirror_tangential(r4_tan, theta1/2),
                    np.dot(
                        self.matrices.free_space(n0, l2),
                        np.dot(
                            self.matrices.curved_mirror_tangential(r3_tan, theta1/2),
                            np.dot(
                                self.matrices.free_space(n0, l3),
                                np.dot(
                                    self.matrices.curved_mirror_tangential(r2_tan, theta1/2),
                                    np.dot(
                                        self.matrices.free_space(n0, l2),
                                        np.dot(
                                            self.matrices.curved_mirror_tangential(r1_tan, theta1/2),
                                            np.dot(
                                                self.matrices.free_space(n0, l1),
                                                self.matrices.free_space(nc, lc/2)))))))))))
        
    def roundtrip_saittal(self, nc, lc, n0, l1, l2, l3, l4, r1_tan, r2_tan, r3_tan, r4_tan, theta1):
        """Calculate the roundtrip matrix for the tangential plane"""
        return np.dot(
            self.matrices.free_space(nc, lc/2),
            np.dot(
                self.matrices.free_space(n0, l4),
                np.dot(
                    self.matrices.curved_mirror_sagittal(r4_sag, theta1/2),
                    np.dot(
                        self.matrices.free_space(n0, l2),
                        np.dot(
                            self.matrices.curved_mirror_sagittal(r3_sag, theta1/2),
                            np.dot(
                                self.matrices.free_space(n0, l3),
                                np.dot(
                                    self.matrices.curved_mirror_sagittal(r2_sag, theta1/2),
                                    np.dot(
                                        self.matrices.free_space(n0, l2),
                                        np.dot(
                                            self.matrices.curved_mirror_sagittal(r1_sag, theta1/2),
                                            np.dot(
                                                self.matrices.free_space(n0, l1),
                                                self.matrices.free_space(nc, lc/2)))))))))))
    
    def stability_plot(self, r1, r2, d, n1, n2):
        """Plot the stability of a resonator as a function of the distance between the mirrors"""
        import matplotlib.pyplot as plt
        distances = np.linspace(0, d, 100)
        stabilities = [self.stability(r1, r2, distance, n1, n2) for distance in distances]
        plt.plot(distances, stabilities)
        plt.xlabel('Distance between mirrors')
        plt.ylabel('Stability')
        plt.show()