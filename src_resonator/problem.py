from Problems.resonator_types import *
from Problems.matrices import Matrices
import numpy as np

class Problem:
    def __init__(self, resonator_type=object):
        self.matrices = Matrices()
        self.type = resonator_type
        
    def problem_dimension(self, *args, **kwargs):
        """
        Calls the problem dimension calculation on the resonator type.
        """
        return self.type.set_problem_dimension(*args, **kwargs)

    def roundtrip_tangential(self, *args, **kwargs):
        """
        Calls the tangential roundtrip calculation on the resonator type.
        """
        self.type.set_roundtrip_tangential(*args, **kwargs) # Set the parameters for the calculation

        result = None
        for m in self.type.set_roundtrip_tangential(*args, **kwargs):
            result = np.matmul(m, result) if result is not None else m
        return result

    def roundtrip_sagittal(self, *args, **kwargs):
        """
        Calls the sagittal roundtrip calculation on the resonator type.
        """
        self.type.set_roundtrip_sagittal(*args, **kwargs)

        result = None
        for m in self.type.set_roundtrip_sagittal(*args, **kwargs):
            result = np.matmul(m, result) if result is not None else m
        return result

    def fitness(self, *args, **kwargs):
        """
        Calls the fitness calculation on the resonator type.
        """
        return self.type.set_fitness(*args, **kwargs)
    
    def optimization_parameters(self, *args, **kwargs):
        """
        Calls the parameters of the resonator type.
        """
        return self, type.parameters(*args, **kwargs)