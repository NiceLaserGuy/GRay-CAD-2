import numpy as np
from Problems.matrices import Matrices

class BowTie:

    def __init__(self):
        self.matrices = Matrices()
        
    def set_problem_dimension(self):
        self.dimension = 5
        return self.dimension

    def set_roundtrip_direction(self, lc, l1, l3, theta):
         self.l1 = l1
         self.l3 = l3
         self.lc = lc
         self.l2 = ((2 * l1) + lc + l3) / (2 * np.cos(2*theta))
         """Sets the direction of the roundtrip, only needed for plotting"""
         vars = self.lc/2, self.l1, self.l2, self.l3, self.l2, self.l1, self.lc/2
         return vars
    
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

    def set_fitness(self, waist_sag, waist_tan, target_sag, target_tan):
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

    def set_problem_dimension(self):
        self.dimension = 2
        return self.dimension

    def set_roundtrip_direction(self, lc, l1):
         self.l1 = l1
         self.lc = lc
         """Sets the direction of the roundtrip, only needed for plotting"""
         return self.lc/2, self.l1, self.l1, self.lc, self.l1, self.l1, self.lc/2
    
    def set_roundtrip_tangential(self, nc, lc, n0, l1, r1_tan):
        """Calculate the roundtrip matrix for the tangential plane"""

        m1 = self.matrices.free_space(lc / 2, nc)
        m2 = self.matrices.free_space(l1, n0)
        m3 = self.matrices.curved_mirror_tangential(r1_tan, 0)
        m4 = self.matrices.free_space(l1, n0)
        m5 = self.matrices.free_space(lc / 2, nc)
        #m6 = self.matrices.free_space(l1, n0)
        #m7 = self.matrices.curved_mirror_tangential(r1_tan, 0)
        #m8 = self.matrices.free_space(l1, n0)
        #m9 = self.matrices.free_space(lc / 2, nc)

        return m1, m2, m3, m4, m5#, m6, m7, m8, m9

    def set_roundtrip_sagittal(self, nc, lc, n0, l1, r1_sag):
        """Calculate the roundtrip matrix for the sagittal plane"""
        
        m1 = self.matrices.free_space(lc / 2, nc)
        m2 = self.matrices.free_space(l1, n0)
        m3 = self.matrices.curved_mirror_sagittal(r1_sag, 0)
        m4 = self.matrices.free_space(l1, n0)
        m5 = self.matrices.free_space(lc / 2, nc)
        #m6 = self.matrices.free_space(l1, n0)
        #m7 = self.matrices.curved_mirror_sagittal(r1_sag, 0)
        #m8 = self.matrices.free_space(l1, n0)
        #m9 = self.matrices.free_space(lc / 2, nc)

        return m1, m2, m3, m4, m5#, m6, m7, m8, m9

    def set_fitness(self, waist_sag, waist_tan, target_sag, target_tan):
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
            
class Triangle:
    
    def __init__(self):
        self.matrices = Matrices()

    def set_problem_dimension(self):
        self.dimension = 5
        return self.dimension

    def set_roundtrip_direction(self, lc, l1, l3):
         self.l1 = l1
         self.lc = lc
         self.l3 = l3
         """Sets the direction of the roundtrip, only needed for plotting"""
         return self.lc/2, self.l1, self.l2, self.l2, self.l1, self.lc/2
    
    def set_roundtrip_tangential(self, nc, lc, n0, l1, l2, r1_tan, r2_tan, theta):
        """Calculate the roundtrip matrix for the tangential plane"""
        phi = np.pi - (2 * theta)
        print("phi", phi)
        print("theta", theta)

        m1 = self.matrices.free_space(lc / 2, nc)
        m2 = self.matrices.free_space(l1, n0)
        m3 = self.matrices.curved_mirror_tangential(r1_tan, theta)
        m4 = self.matrices.free_space(l2, n0)
        m5 = self.matrices.curved_mirror_tangential(r2_tan, phi)
        m6 = self.matrices.free_space(l2, n0)
        m7 = self.matrices.curved_mirror_tangential(r1_tan, theta)
        m8 = self.matrices.free_space(l1, n0)
        m9 = self.matrices.free_space(lc / 2, nc)

        return m1, m2, m3, m4, m5, m6, m7, m8, m9

    def set_roundtrip_sagittal(self, nc, lc, n0, l1, l2, r1_sag, r2_sag, theta):
        """Calculate the roundtrip matrix for the sagittal plane"""
        phi = np.pi - (2 * theta)

        m1 = self.matrices.free_space(lc / 2, nc)
        m2 = self.matrices.free_space(l1, n0)
        m3 = self.matrices.curved_mirror_sagittal(r1_sag, theta)
        m4 = self.matrices.free_space(l2, n0)
        m5 = self.matrices.curved_mirror_sagittal(r2_sag, phi)
        m6 = self.matrices.free_space(l2, n0)
        m7 = self.matrices.curved_mirror_sagittal(r1_sag, theta)
        m8 = self.matrices.free_space(l1, n0)
        m9 = self.matrices.free_space(lc / 2, nc)
        
        return m1, m2, m3, m4, m5, m6, m7, m8, m9

    def set_fitness(self, waist_sag, waist_tan, target_sag, target_tan):
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
            
class Rectangle:
    
    def __init__(self):
        self.matrices = Matrices()

    def set_problem_dimension(self):
        self.dimension = 4
        return self.dimension

    def set_roundtrip_direction(self, lc, l1, l2):
         self.l1 = l1
         self.lc = lc
         self.l2 = l2
         self.l3 = (2 * self.l1) + self.lc
         """Sets the direction of the roundtrip, only needed for plotting"""
         return self.lc/2, self.l1, self.l2, self.l3, self.l2, self.l1, self.lc/2
    
    def set_roundtrip_tangential(self, nc, lc, n0, l1, l2, r1_tan, r2_tan):
            """Calculate the roundtrip matrix for the tangential plane"""
            l3 = (2 * l1) + lc
            
            m1= self.matrices.free_space(lc / 2, nc)
            m2= self.matrices.free_space(l1, n0)
            m3= self.matrices.curved_mirror_tangential(r2_tan, np.pi/2)
            m4= self.matrices.free_space(l2, n0)
            m5= self.matrices.curved_mirror_tangential(r1_tan, np.pi/2)
            m6= self.matrices.free_space(l3, n0)
            m7= self.matrices.curved_mirror_tangential(r1_tan, np.pi/2)
            m8= self.matrices.free_space(l2, n0)
            m9= self.matrices.curved_mirror_tangential(r2_tan, np.pi/2)
            m10= self.matrices.free_space(l1, n0)
            m11= self.matrices.free_space(lc / 2, nc)

            return m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11

    def set_roundtrip_sagittal(self, nc, lc, n0, l1, l2, r1_sag, r2_sag):
        """Calculate the roundtrip matrix for the sagittal plane"""
        l3 = (2 * l1) + lc
                   
        m1= self.matrices.free_space(lc / 2, nc)
        m2= self.matrices.free_space(l1, n0)
        m3= self.matrices.curved_mirror_sagittal(r2_sag, np.pi/2)
        m4= self.matrices.free_space(l2, n0)
        m5= self.matrices.curved_mirror_sagittal(r1_sag, np.pi/2)
        m6= self.matrices.free_space(l3, n0)
        m7= self.matrices.curved_mirror_sagittal(r1_sag, np.pi/2)
        m8= self.matrices.free_space(l2, n0)
        m9= self.matrices.curved_mirror_sagittal(r2_sag, np.pi/2)
        m10= self.matrices.free_space(l1, n0)
        m11= self.matrices.free_space(lc / 2, nc)

        return m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11     

    def set_fitness(self, waist_sag, waist_tan, target_sag, target_tan):
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