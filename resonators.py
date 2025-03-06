import numpy as np
import deap

from deap import base, creator, tools, algorithms
from matrices import Matrices

class Resonator:
    
    def __init__(self):
        self.matrices = Matrices()
        self.ui_resonator = None  # Initialize ui_resonator as None
    
    def set_ui_resonator(self, ui_resonator):
        """Set the ui_resonator reference"""
        self.ui_resonator = ui_resonator
    
    def roundtrip_tangential(self, nc, lc, n0, l1, l2, l3, r1_tan, r2_tan, r3_tan, r4_tan, theta1):
        """Calculate the roundtrip matrix for the tangential plane"""
        return np.dot(
            self.matrices.free_space(nc, lc/2),
            np.dot(
                self.matrices.free_space(n0, l1),
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
        
    def roundtrip_sagittal(self, nc, lc, n0, l1, l2, l3, r1_sag, r2_sag, r3_sag, r4_sag, theta1):
        """Calculate the roundtrip matrix for the sagittal plane"""
        return np.dot(
            self.matrices.free_space(nc, lc/2),
            np.dot(
                self.matrices.free_space(n0, l1),
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

    
    def get_input(self):
        self.target_sag = float(self.ui_resonator.edit_target_waist_sag.text())*1e-6
        self.target_tan = float(self.ui_resonator.edit_target_waist_tan.text())*1e-6
        self.nco = float(self.ui_resonator.edit_crystal_refractive_index_ordinary.text())
        self.nce = float(self.ui_resonator.edit_crystal_refractive_index_extraordinary.text())
        self.lc = float(self.ui_resonator.edit_crystal_length.text())*1e-3
        self.wavelength = float(self.ui_resonator.edit_wavelength.text())*1e-6
        self.n_prop = 1
        
        return np.array([self.target_sag, self.target_tan, self.nco, self.nce, self.lc, self.n_prop, self.wavelength])
        
    def evaluate_resonator(self):
        inputs = self.get_input()
        target_sag, target_tan, nco, nce, lc, n_prop, wavelength = inputs

        # Define the DEAP algorithm
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        toolbox = base.Toolbox()
        toolbox.register("attr_float", np.random.uniform, 0.1, 10.0)
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=4)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        def evaluate(individual):
            l1, l2, l3, theta1 = individual
            # TODO: Implenent the radius of curvature calculation from .json file
            roundtrip_matrix_sag = self.roundtrip_sagittal(nco, lc, n_prop, l1, l2, l3, 1, 1, 1, 1, theta1)
            roundtrip_matrix_tan = self.roundtrip_tangential(nco, lc, n_prop, l1, l2, l3, 1, 1, 1, 1, theta1)
            waist_sag = np.abs(roundtrip_matrix_sag[0, 0] - roundtrip_matrix_sag[1, 1])
            waist_tan = np.abs(roundtrip_matrix_tan[0, 0] - roundtrip_matrix_tan[1, 1])
            return (np.abs(waist_sag - target_sag) + np.abs(waist_tan - target_tan),)

        toolbox.register("mate", tools.cxBlend, alpha=0.5)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("evaluate", evaluate)

        population = toolbox.population(n=50)
        ngen = 40
        cxpb = 0.5
        mutpb = 0.2

        algorithms.eaSimple(population, toolbox, cxpb, mutpb, ngen, verbose=True)

        best_individual = tools.selBest(population, 1)[0]
        print("Best individual is: %s\nwith fitness: %s" % (best_individual, best_individual.fitness.values))

        return best_individual
