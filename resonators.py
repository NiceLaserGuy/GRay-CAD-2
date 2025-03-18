import numpy as np
from deap import base, creator, tools, algorithms
from deap.benchmarks.tools import diversity, convergence
from deap.benchmarks import sphere
from matrices import Matrices

class Resonator:
    
    def __init__(self):
        self.matrices = Matrices()
        self.ui_resonator = None  # Initialize ui_resonator as None
    
    def set_ui_resonator(self, ui_resonator):
        """Set the ui_resonator reference"""
        self.ui_resonator = ui_resonator

        
    def get_input(self):
        """Inputs from UI converted to meters"""
        self.target_sag = float(self.ui_resonator.edit_target_waist_sag.text())*1e-6
        self.target_tan = float(self.ui_resonator.edit_target_waist_tan.text())*1e-6
        self.nc = float(self.ui_resonator.edit_crystal_refractive_index_ordinary.text())
        self.lc = float(self.ui_resonator.edit_crystal_length.text())*1e-3
        self.wavelength = float(self.ui_resonator.edit_wavelength.text())*1e-6
        self.n_prop = 1

        return np.array([self.target_sag, self.target_tan, self.nc, self.lc, self.n_prop, self.wavelength])

    def evaluate_resonator(self):
        inputs = self.get_input()
        target_sag, target_tan, nc, lc, n_prop, wavelength = inputs

        # Define the fitness function
        def objective(individual):
            l1, l3, theta, r1_sag, r1_tan, r2_sag, r2_tan = individual
            roundtrip_matrix_sag = self.matrices.roundtrip_sagittal(nc, lc, n_prop, l1, l3, r1_sag, r2_sag, theta)
            roundtrip_matrix_tan = self.matrices.roundtrip_tangential(nc, lc, n_prop, l1, l3, r1_tan, r2_tan, theta)
            m_sag = np.abs(roundtrip_matrix_sag[0, 0] - roundtrip_matrix_sag[1, 1])
            m_tan = np.abs(roundtrip_matrix_tan[0, 0] - roundtrip_matrix_tan[1, 1])
            b_sag = np.abs(roundtrip_matrix_sag[0, 1])
            b_tan = np.abs(roundtrip_matrix_tan[0, 1])
            waist_sag = np.sqrt((b_sag * wavelength) / (np.pi) * (np.sqrt(np.abs(1 / (1 - m_sag**2)))))
            waist_tan = np.sqrt((b_tan * wavelength) / (np.pi) * (np.sqrt(np.abs(1 / (1 - m_tan**2)))))
            '''weigthing the waist sizes (smaller waist is more important)'''
            if waist_sag < waist_tan:
                fitness_value = np.sqrt(
                    2*((waist_sag - target_sag) / target_sag)**2 +
                    ((waist_tan - target_tan) / target_tan)**2 +
                    (1 / 100) * m_sag**2 +
                    (1 / 100) * m_tan**2
                )
                return fitness_value,
            if waist_sag > waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    2*((waist_tan - target_tan) / target_tan)**2 +
                    (1 / 100) * m_sag**2 +
                    (1 / 100) * m_tan**2
                )
                return fitness_value,

            else:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    ((waist_tan - target_tan) / target_tan)**2 +
                    (1 / 100) * m_sag**2 +
                    (1 / 100) * m_tan**2
                )
                return fitness_value,

        # DEAP setup for PSO
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Particle", list, fitness=creator.FitnessMin, speed=list, smin=None, smax=None, best=None)

        def generate(size, pmin, pmax, smin, smax):
            particle = creator.Particle(np.random.uniform(pmin, pmax) for _ in range(size))
            particle.speed = [np.random.uniform(smin, smax) for _ in range(size)]
            particle.smin = smin
            particle.smax = smax
            return particle

        def update_particle(part, best, phi1, phi2):
            u1 = np.random.uniform(0, phi1, len(part))
            u2 = np.random.uniform(0, phi2, len(part))
            v_u1 = [u * (b - p) for u, b, p in zip(u1, part.best, part)]
            v_u2 = [u * (b - p) for u, b, p in zip(u2, best, part)]
            part.speed = [v + vu1 + vu2 for v, vu1, vu2 in zip(part.speed, v_u1, v_u2)]

            for i, speed in enumerate(part.speed):
                if speed < part.smin:
                    part.speed[i] = part.smin
                elif speed > part.smax:
                    part.speed[i] = part.smax

            part[:] = [p + v for p, v in zip(part, part.speed)]

        toolbox = base.Toolbox()
        toolbox.register("particle", generate, size=7, pmin=0.025, pmax=1.0, smin=-0.5, smax=0.5)
        toolbox.register("population", tools.initRepeat, list, toolbox.particle)
        toolbox.register("update", update_particle, phi1=1.5, phi2=1.5)
        toolbox.register("evaluate", objective)

        # Create the population
        population = toolbox.population(n=200)

        # PSO loop
        best = None
        for gen in range(1000):
            for part in population:
                part.fitness.values = toolbox.evaluate(part)
                # Aktualisiere das beste Partikel basierend auf Minimierung
                if not part.best or part.best.fitness.values[0] > part.fitness.values[0]:
                    part.best = creator.Particle(part)
                    part.best.fitness.values = part.fitness.values
                if not best or best.fitness.values[0] > part.fitness.values[0]:
                    best = creator.Particle(part)
                    best.fitness.values = part.fitness.values

            for part in population:
                toolbox.update(part, best)

            # Debugging-Ausgabe
            print(f"Generation {gen}: Best fitness = {best.fitness.values[0]}")

        # Output results
        l1, l3, theta, r1_sag, r1_tan, r2_sag, r2_tan = best
        '''Calculate the waist sizes'''
        roundtrip_matrix_sag = self.matrices.roundtrip_sagittal(nc, lc, n_prop, l1, l3, r1_sag, r2_sag, theta)
        roundtrip_matrix_tan = self.matrices.roundtrip_tangential(nc, lc, n_prop, l1, l3, r1_tan, r2_tan, theta)
        m_sag = np.abs(roundtrip_matrix_sag[0, 0] - roundtrip_matrix_sag[1, 1])
        m_tan = np.abs(roundtrip_matrix_tan[0, 0] - roundtrip_matrix_tan[1, 1])
        b_sag = np.abs(roundtrip_matrix_sag[0, 1])
        b_tan = np.abs(roundtrip_matrix_tan[0, 1])
        waist_sag = np.sqrt((b_sag * wavelength) / (np.pi) * (np.sqrt(np.abs(1 / (1 - m_sag**2)))))
        waist_tan = np.sqrt((b_tan * wavelength) / (np.pi) * (np.sqrt(np.abs(1 / (1 - m_tan**2)))))
        print(f"Best solution found:")
        print(f"l1: {l1*1e3} mm")
        print(f"l3: {l3*1e3} mm")
        print(f"theta: {np.rad2deg(theta)} deg")
        print(f"r1_sag: {r1_sag*1e3} mm")
        print(f"r1_tan: {r1_tan*1e3} mm")
        print(f"r2_sag: {r2_sag*1e3} mm")
        print(f"r2_tan: {r2_tan*1e3} mm")
        print(f"waist_sag: {waist_sag*1e6} um")
        print(f"waist_tan: {waist_tan*1e6} um")
        print(f"Fitness: {best.fitness.values[0]}")
        return best