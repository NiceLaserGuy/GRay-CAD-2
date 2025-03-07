import numpy as np
import deap
from deap import base, creator, tools, algorithms
from matrices import Matrices
from lens_library import LensLibrary
from os import path

class Resonator:
    
    def __init__(self):
        self.matrices = Matrices()
        self.ui_resonator = None  # Initialize ui_resonator as None
        self.lens_library = LensLibrary(library_path=(path.abspath(path.join(path.dirname(__file__))) + "/Library_Mirrors"))

    def set_ui_resonator(self, ui_resonator):
        """Set the ui_resonator reference"""
        self.ui_resonator = ui_resonator
    
    def roundtrip_tangential(self, nc, lc, n0, l1, l3, r1_tan, r2_tan, theta):
        """Calculate the roundtrip matrix for the tangential plane"""
        l2 = (2*l1+lc+l3)/np.cos(theta)
        r3_tan = r2_tan
        r4_tan = r1_tan
        return np.dot(
            self.matrices.free_space(nc, lc/2),
            np.dot(
                self.matrices.free_space(n0, l1),
                np.dot(
                    self.matrices.curved_mirror_tangential(r4_tan, theta/2),
                    np.dot(
                        self.matrices.free_space(n0, l2),
                        np.dot(
                            self.matrices.curved_mirror_tangential(r3_tan, theta/2),
                            np.dot(
                                self.matrices.free_space(n0, l3),
                                np.dot(
                                    self.matrices.curved_mirror_tangential(r2_tan, theta/2),
                                    np.dot(
                                        self.matrices.free_space(n0, l2),
                                        np.dot(
                                            self.matrices.curved_mirror_tangential(r1_tan, theta/2),
                                            np.dot(
                                                self.matrices.free_space(n0, l1),
                                                self.matrices.free_space(nc, lc/2)))))))))))
        
    def roundtrip_sagittal(self, nc, lc, n0, l1, l3, r1_sag, r2_sag, theta):
        """Calculate the roundtrip matrix for the sagittal plane"""
        l2 = (2*l1+lc+l3)/np.cos(theta)
        r3_sag = r2_sag
        r4_sag = r1_sag
        return np.dot(
            self.matrices.free_space(nc, lc/2),
            np.dot(
                self.matrices.free_space(n0, l1),
                np.dot(
                    self.matrices.curved_mirror_sagittal(r4_sag, theta/2),
                    np.dot(
                        self.matrices.free_space(n0, l2),
                        np.dot(
                            self.matrices.curved_mirror_sagittal(r3_sag, theta/2),
                            np.dot(
                                self.matrices.free_space(n0, l3),
                                np.dot(
                                    self.matrices.curved_mirror_sagittal(r2_sag, theta/2),
                                    np.dot(
                                        self.matrices.free_space(n0, l2),
                                        np.dot(
                                            self.matrices.curved_mirror_sagittal(r1_sag, theta/2),
                                            np.dot(
                                                self.matrices.free_space(n0, l1),
                                                self.matrices.free_space(nc, lc/2)))))))))))

        
    def waist_sagittal(self, z):
        """Calculate the sagittal waist of a resonator in the center of the crystal"""
        # TODO: Implement the waist calculation
        return 0
        
    
    def get_input(self):
        """Inputs from UI in mm"""
        self.target_sag = float(self.ui_resonator.edit_target_waist_sag.text())*1e-3
        self.target_tan = float(self.ui_resonator.edit_target_waist_tan.text())*1e-3
        self.nco = float(self.ui_resonator.edit_crystal_refractive_index_ordinary.text())
        self.nce = float(self.ui_resonator.edit_crystal_refractive_index_extraordinary.text())
        self.lc = float(self.ui_resonator.edit_crystal_length.text())
        self.wavelength = float(self.ui_resonator.edit_wavelength.text())*1e-3
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
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=3)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        def evaluate(individual):
            mirror = self.lens_library.get_mirror_curvatures()
            l1, l3, theta = individual            
            r1_sag = 100
            r2_sag = 1/np.Infinity
            r1_tan = 1/np.Infinity
            r2_tan = 100
            roundtrip_matrix_sag = self.roundtrip_sagittal(nco, lc, n_prop, l1, l3, r1_sag, r2_sag, theta)
            roundtrip_matrix_tan = self.roundtrip_tangential(nco, lc, n_prop, l1, l3, r1_tan, r2_tan, theta)
            waist_sag = np.abs(roundtrip_matrix_sag[0, 0] - roundtrip_matrix_sag[1, 1])
            waist_tan = np.abs(roundtrip_matrix_tan[0, 0] - roundtrip_matrix_tan[1, 1])
            
            fitness = np.abs(waist_sag - target_sag) + np.abs(waist_tan - target_tan)
            penalty = 10000
            if any(l1 < 0 or l3 < 0 or theta < 0 for l1, l3, theta in individual):
                return (fitness + penalty,)
            return (fitness,)

        toolbox.register("mate", tools.cxBlend, alpha=0.5)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("evaluate", evaluate)

        population = toolbox.population(n=100)
        ngen = 100
        cxpb = 0.5
        mutpb = 0.2

        algorithms.eaSimple(population, toolbox, cxpb, mutpb, ngen, verbose=True)

        best_individual = tools.selBest(population, 1)[0]
        print("l1: %s mm\n l2: "+ (2*best_individual[0]+lc+best_individual[1])/np.cos(best_individual[2]) + "\nl3: %s mm\ntheta: %s degree\nwith fitness: %s" % (best_individual[0], best_individual[1], best_individual[2]*180/np.pi, best_individual.fitness.values))

        return best_individual
