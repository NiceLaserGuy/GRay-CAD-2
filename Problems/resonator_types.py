import numpy as np
from Problems.matrices import Matrices

class BowTie:

    def __init__(self):
        self.matrices = Matrices()
    
    def set_roundtrip_tangential(self, nc, lc, n0, l1, l3, r1_tan, r2_tan, theta):
            """Calculate the roundtrip matrix for the tangential plane"""
            l2 = ((2 * l1) + lc + l3) / (2 * np.cos(2*theta))
            
            m1= self.matrices.free_space(lc / 2, nc)
            m2= self.matrices.free_space(l1, n0)
            m3= self.matrices.curved_mirror_tangential(r2_tan, theta)
            m4= self.matrices.free_space(l2, n0)
            m5= self.matrices.curved_mirror_tangential(r1_tan, theta)
            m6= self.matrices.free_space(l3, n0)
            m7= self.matrices.curved_mirror_tangential(r1_tan, theta)
            m8= self.matrices.free_space(l2, n0)
            m9= self.matrices.curved_mirror_tangential(r2_tan, theta)
            m10= self.matrices.free_space(l1, n0)
            m11= self.matrices.free_space(lc / 2, nc)

            return m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11

    def set_roundtrip_sagittal(self, nc, lc, n0, l1, l3, r1_sag, r2_sag, theta):
        """Calculate the roundtrip matrix for the sagittal plane"""
        l2 = ((2 * l1) + lc + l3) / (2 * np.cos(2*theta))
        
        m1= self.matrices.free_space(lc / 2, nc)
        m2= self.matrices.free_space(l1, n0)
        m3= self.matrices.curved_mirror_sagittal(r2_sag, theta)
        m4= self.matrices.free_space(l2, n0)
        m5= self.matrices.curved_mirror_sagittal(r1_sag, theta)
        m6= self.matrices.free_space(l3, n0)
        m7= self.matrices.curved_mirror_sagittal(r1_sag, theta)
        m8= self.matrices.free_space(l2, n0)
        m9= self.matrices.curved_mirror_sagittal(r2_sag, theta)
        m10= self.matrices.free_space(l1, n0)
        m11= self.matrices.free_space(lc / 2, nc)

        return m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11        

    def set_fitness(waist_sag, waist_tan, target_sag, target_tan):
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