import numpy as np
from matrices import Matrices

class BowTie:    

    def __init__(self):
        self.matrices = Matrices()
    
    def roundtrip_tangential(self, nc, lc, n0, l1, l3, r1_tan, r2_tan, theta):
            """Calculate the roundtrip matrix for the tangential plane"""
            l2 = ((2 * l1) + lc + l3) / (2 * np.cos(2*theta))
            
            # Chain of matrix multiplications using np.matmul
            return np.matmul(self.matrices.free_space(lc / 2, nc),
                np.matmul(self.matrices.free_space(l1, n0),
                np.matmul(self.matrices.curved_mirror_tangential(r2_tan, theta),
                np.matmul(self.matrices.free_space(l2, n0),
                np.matmul(self.matrices.curved_mirror_tangential(r1_tan, theta),
                np.matmul(self.matrices.free_space(l3, n0),
                np.matmul(self.matrices.curved_mirror_tangential(r1_tan, theta),
                np.matmul(self.matrices.free_space(l2, n0),
                np.matmul(self.matrices.curved_mirror_tangential(r2_tan, theta),
                np.matmul(self.matrices.free_space(l1, n0),
                self.matrices.free_space(lc / 2, nc)))))))))))

    def roundtrip_sagittal(self, nc, lc, n0, l1, l3, r1_sag, r2_sag, theta):
        """Calculate the roundtrip matrix for the sagittal plane"""
        l2 = ((2 * l1) + lc + l3) / (2 * np.cos(2*theta))
        
        # Chain of matrix multiplications using np.matmul
        return np.matmul(self.matrices.free_space(lc / 2, nc),
            np.matmul(self.matrices.free_space(l1, n0),
            np.matmul(self.matrices.curved_mirror_sagittal(r2_sag, theta),
            np.matmul(self.matrices.free_space(l2, n0),
            np.matmul(self.matrices.curved_mirror_sagittal(r1_sag, theta),
            np.matmul(self.matrices.free_space(l3, n0),
            np.matmul(self.matrices.curved_mirror_sagittal(r1_sag, theta),
            np.matmul(self.matrices.free_space(l2, n0),
            np.matmul(self.matrices.curved_mirror_sagittal(r2_sag, theta),
            np.matmul(self.matrices.free_space(l1, n0),
            self.matrices.free_space(lc / 2, nc)))))))))))
    
    def fitness(waist_sag, waist_tan, target_sag, target_tan):
            """Calculate the fitness value for the Bowtie resonator"""
            if waist_sag < waist_tan:
                fitness_value = np.sqrt(
                    2*((waist_sag - target_sag) / target_sag)**2 +  # Double weight for smaller waist
                    ((waist_tan - target_tan) / target_tan)**2
                )
                return fitness_value,
            if waist_sag > waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    2*((waist_tan - target_tan) / target_tan)**2    # Double weight for smaller waist
                )
                return fitness_value,

            if waist_sag == waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    ((waist_tan - target_tan) / target_tan)**2
                )
                return fitness_value,
    
class FabryPerot:
    
    def __init__(self):
        self.matrices = Matrices()
    
    def roundtrip_tangential(self, nc, lc, n0, l1, l2, r1_tan, r2_tan, theta):
        """Calculate the roundtrip matrix for a Fabry-Perot resonator"""
        return np.matmul(self.matrices.free_space(lc / 2, nc),
            np.matmul(self.matrices.free_space(l1, n0),
            np.matmul(self.matrices.curved_mirror_tangential(r1_tan, theta),
            np.matmul(self.matrices.free_space(l2, n0),
            np.matmul(self.matrices.curved_mirror_tangential(r2_tan, theta),
            np.matmul(self.matrices.free_space(l1, n0),
            self.matrices.free_space(lc / 2, nc)))))))
    
    def roundtrip_sagittal(self, nc, lc, n0, l1, l2, r1_sag, r2_sag, theta):
        """Calculate the roundtrip matrix for a Fabry-Perot resonator"""
        return np.matmul(self.matrices.free_space(lc / 2, nc),
            np.matmul(self.matrices.free_space(l1, n0),
            np.matmul(self.matrices.curved_mirror_sagittal(r1_sag, theta),
            np.matmul(self.matrices.free_space(l2, n0),
            np.matmul(self.matrices.curved_mirror_sagittal(r2_sag, theta),
            np.matmul(self.matrices.free_space(l1, n0),
            self.matrices.free_space(lc / 2, nc)))))))
    
    def fitness(waist_sag, waist_tan, target_sag, target_tan):
            """Calculate the fitness value for the Bowtie resonator"""
            if waist_sag < waist_tan:
                fitness_value = np.sqrt(
                    2*((waist_sag - target_sag) / target_sag)**2 +  # Double weight for smaller waist
                    ((waist_tan - target_tan) / target_tan)**2
                )
                return fitness_value,
            if waist_sag > waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    2*((waist_tan - target_tan) / target_tan)**2    # Double weight for smaller waist
                )
                return fitness_value,

            if waist_sag == waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    ((waist_tan - target_tan) / target_tan)**2
                )
                return fitness_value,