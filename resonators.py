import json
import numpy as np
from deap import base, creator, tools
from os import path
from PyQt5.QtCore import QThread, pyqtSignal
from resonator_types import BowTie

class Resonator:
    """
    Main class for resonator optimization using Particle Swarm Optimization (PSO).
    Handles mirror configurations and resonator calculations.
    """
    
    def __init__(self):
        self.resonator_type = BowTie()  # Initialize resonator type as BowTie
        self.ui_resonator = None  # Initialize ui_resonator as None
        self.mirror_curvatures = []

    def load_mirror_data(self, filepath):
        """
        Loads mirror data from a JSON file.
        For non-round mirrors (IS_ROUND = 0.0), creates an additional entry 
        with swapped sagittal and tangential curvatures.
        
        Args:
            filepath (str): Path to the JSON file containing mirror definitions
        """
        # Überprüfen, ob die Datei existiert
        if not path.exists(filepath):
            raise FileNotFoundError(f"Die Datei '{filepath}' wurde nicht gefunden.")

        # Laden der JSON-Daten
        with open(filepath, 'r') as file:
            data = json.load(file)

        # Extrahieren der Spiegel-Daten
        self.mirror_curvatures = []
        for component in data.get("components", []):
            if component.get("type") == "MIRROR":
                properties = component.get("properties", {})
                curvature_tangential = properties.get("CURVATURE_TANGENTIAL", 0.0)
                curvature_sagittal = properties.get("CURVATURE_SAGITTAL", 0.0)
                is_round = properties.get("IS_ROUND", 0.0)
                
                # Normale Variante speichern
                self.mirror_curvatures.append((curvature_sagittal, curvature_tangential, is_round))
                
                # Für nicht-runde Spiegel zusätzlich die getauschte Variante speichern
                if is_round == 0.0:
                    self.mirror_curvatures.append((curvature_tangential, curvature_sagittal, is_round))
                    
        # Debugging-Ausgabe
        if not self.mirror_curvatures:
            raise ValueError("Die Liste 'mirror_curvatures' ist leer. Überprüfen Sie die Datei 'Mirrors.json'.")
        
    def set_ui_resonator(self, ui_resonator):
        """Set the ui_resonator reference"""
        self.ui_resonator = ui_resonator

        
    def get_input(self):
        """
        Retrieves input parameters from the UI and converts them to meters.
        
        Returns:
            numpy.array: Array containing [target_sag, target_tan, nc, lc, n_prop, wavelength]
        """
        self.target_sag = float(self.ui_resonator.edit_target_waist_sag.text())*1e-6
        self.target_tan = float(self.ui_resonator.edit_target_waist_tan.text())*1e-6
        self.nc = float(self.ui_resonator.edit_crystal_refractive_index.text())
        self.lc = float(self.ui_resonator.edit_crystal_length.text())*1e-3
        self.wavelength = float(self.ui_resonator.edit_wavelength.text())*1e-6
        self.n_prop = 1

        return np.array([self.target_sag, self.target_tan, self.nc, self.lc, self.n_prop, self.wavelength])
    
    def getbounds(self):
        """
        Gets geometric bounds from the UI for l1, l3, and theta parameters.
        Converts UI values to appropriate units (meters and radians).
        
        Returns:
            tuple: (l1_min, l1_max, l3_min, l3_max, theta_min, theta_max)
        """
        l1_min = float(self.ui_resonator.edit_lower_bound_l1.text()) * 1e-3
        l1_max = float(self.ui_resonator.edit_upper_bound_l1.text()) * 1e-3
        l3_min = float(self.ui_resonator.edit_lower_bound_l3.text()) * 1e-3
        l3_max = float(self.ui_resonator.edit_upper_bound_l3.text()) * 1e-3
        theta_min = np.deg2rad(float(self.ui_resonator.edit_lower_bound_theta.text())/2)
        theta_max = np.deg2rad(float(self.ui_resonator.edit_upper_bound_theta.text())/2)
        return l1_min, l1_max, l3_min, l3_max, theta_min, theta_max
    
    def get_optimization_parameters(self):
        """
        Retrieves optimization parameters from the UI.
        
        Returns:
            tuple: (population_number, generation_number, phi1, phi2, pmin, pmax, smin, smax)
        """
        population_number = int(float(self.ui_resonator.edit_population_number.text()))
        generation_number = int(float(self.ui_resonator.edit_generation_number.text()))
        phi1 = float(self.ui_resonator.edit_phi1_float.text())
        phi2 = float(self.ui_resonator.edit_phi2_float.text())
        pmin = float(self.ui_resonator.edit_pmin.text())
        pmax = float(self.ui_resonator.edit_pmax.text())
        smin = float(self.ui_resonator.edit_smin.text())
        smax = float(self.ui_resonator.edit_smax.text())
        return population_number, generation_number, phi1, phi2, pmin, pmax, smin, smax

    def evaluate_resonator(self):
        # Load mirror data and get input parameters
        self.load_mirror_data(path.abspath(path.join(path.dirname(__file__), "Library/Mirrors.json")))
        
        if not self.mirror_curvatures:
            raise ValueError("Die Liste 'mirror_curvatures' ist leer. Überprüfen Sie die Datei 'Mirrors.json'.")
        
        # Get optimization parameters
        population_number, generation_number, phi1, phi2, pmin, pmax, smin, smax = self.get_optimization_parameters()
        
        inputs = self.get_input()
        target_sag, target_tan, nc, lc, n_prop, wavelength = inputs

        # Define the fitness function with closure over the input values
        def objective(individual):
            """
            Fitness function for PSO optimization.
            Calculates resonator parameters and returns fitness value.
            
            Args:
                individual: Particle containing [l1, l3, theta, mirror1, mirror2]
            
            Returns:
                tuple: Single-element tuple containing the fitness value
            """
            # Extract individual parameters
            l1, l3, theta, mirror1, mirror2 = individual
            
            # Get mirror curvatures
            mirror1 = int(np.clip(mirror1, 0, len(self.mirror_curvatures) - 1))
            mirror2 = int(np.clip(mirror2, 0, len(self.mirror_curvatures) - 1))
            r1_sag, r1_tan = self.mirror_curvatures[mirror1][:2]
            r2_sag, r2_tan = self.mirror_curvatures[mirror2][:2]
            
            # Calculate roundtrip matrices
            roundtrip_matrix_sag = self.resonator_type.roundtrip_sagittal(nc, lc, n_prop, l1, l3, r1_sag, r2_sag, theta)
            roundtrip_matrix_tan = self.resonator_type.roundtrip_tangential(nc, lc, n_prop, l1, l3, r1_tan, r2_tan, theta)
            
            # Extract matrix elements for stability calculation
            m_sag = np.abs((roundtrip_matrix_sag[0, 0] + roundtrip_matrix_sag[1, 1])/2)
            m_tan = np.abs((roundtrip_matrix_tan[0, 0] + roundtrip_matrix_tan[1, 1])/2)
            
            # Calculate beam parameters
            b_sag = np.abs(roundtrip_matrix_sag[0, 1])
            b_tan = np.abs(roundtrip_matrix_tan[0, 1])
            
            # Calculate waist sizes
            waist_sag = np.sqrt(((b_sag * wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_sag**2)))))
            waist_tan = np.sqrt(((b_tan * wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_tan**2)))))
            
            # Calculate fitness value based on waist size ratios
            # Different weights are applied depending on which waist is smaller
            if waist_sag < waist_tan:
                fitness_value = np.sqrt(
                    2*((waist_sag - target_sag) / target_sag)**2 +  # Double weight for smaller waist
                    ((waist_tan - target_tan) / target_tan)**2 +
                    1/100 * (m_sag**2 + m_tan**2)  # Penalty for unstable resonators
                )
                return fitness_value,
            if waist_sag > waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    2*((waist_tan - target_tan) / target_tan)**2 +
                    1/100 * (m_sag**2 + m_tan**2)  # Penalty for unstable resonators
                )
                return fitness_value,

            if waist_sag == waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    ((waist_tan - target_tan) / target_tan)**2 +
                    1/100 * (m_sag**2 + m_tan**2)  # Penalty for unstable resonators
                )
                return fitness_value,
    
            if abs(m_sag) > 1 or abs(m_tan) > 1:
                return 1e6,

        # Definition der generate Funktion
        def generate(size, pmin, pmax, smin, smax):
            """
            Generates a new particle for PSO.
            
            Args:
                size (int): Number of parameters per particle
                pmin (float): Minimum position value
                pmax (float): Maximum position value
                smin (float): Minimum velocity value
                smax (float): Maximum velocity value
            
            Returns:
                Particle: New particle with random initial position and velocity
            """
            # Grenzen für l1, l3 und theta aus dem UI
            l1_min, l1_max, l3_min, l3_max, theta_min, theta_max = self.getbounds()

            particle = creator.Particle([
                np.random.uniform(l1_min, l1_max) if i == 0 else
                np.random.uniform(l3_min, l3_max) if i == 1 else
                np.random.uniform(theta_min, theta_max) if i == 2 else
                np.random.randint(0, len(self.mirror_curvatures))
                for i in range(size)
            ])
            particle.speed = [np.random.uniform(smin, smax) for _ in range(size)]
            particle.smin = smin
            particle.smax = smax
            return particle

        # Definition der update_particle Funktion
        def update_particle(part, best, phi1, phi2):
            """
            Updates particle position and velocity.
            
            Args:
                part: Particle to update
                best: Global best position
                phi1: Personal best weight
                phi2: Global best weight
            """
            u1 = np.random.uniform(0, phi1, len(part))
            u2 = np.random.uniform(0, phi2, len(part))
            v_u1 = [u * (b - p) for u, b, p in zip(u1, part.best, part)]
            v_u2 = [u * (b - p) for u, b, p in zip(u2, best, part)]
            part.speed = [v + vu1 + vu2 for v, vu1, vu2 in zip(part.speed, v_u1, v_u2)]

            # Geschwindigkeitsgrenzen einhalten
            for i, speed in enumerate(part.speed):
                if speed < part.smin:
                    part.speed[i] = part.smin
                elif speed > part.smax:
                    part.speed[i] = part.smax

            # Positionsgrenzen einhalten
            l1_min, l1_max, l3_min, l3_max, theta_min, theta_max = self.getbounds()

            part[:] = [
                np.clip(p + v, l1_min, l1_max) if i == 0 else
                np.clip(p + v, l3_min, l3_max) if i == 1 else
                np.clip(p + v, theta_min, theta_max) if i == 2 else
                int(np.clip(round(p + v), 0, len(self.mirror_curvatures) - 1))
                for i, (p, v) in enumerate(zip(part, part.speed))
            ]

        # DEAP setup for PSO with optimization parameters
        toolbox = base.Toolbox()
        toolbox.register("particle", generate, size=5, pmin=pmin, pmax=pmax, smin=smin, smax=smax)
        toolbox.register("population", tools.initRepeat, list, toolbox.particle)
        toolbox.register("update", update_particle, phi1=phi1, phi2=phi2)
        toolbox.register("evaluate", objective)

        # Create population with population_number
        population = toolbox.population(n=population_number)

        # Initialize optimization thread with generation_number
        self.optimization_thread = OptimizationThread(
            self, population, toolbox, generation_number
        )
        
        # Setup progress bar with generation_number
        self.ui_resonator.progressBar_build_resonator.setMaximum(generation_number)
        self.ui_resonator.progressBar_build_resonator.setValue(0)

        # Connect signals and start thread
        self.optimization_thread.progress.connect(
            self.ui_resonator.progressBar_build_resonator.setValue
        )
        self.optimization_thread.finished.connect(self.optimization_finished)
        self.optimization_thread.generation_update.connect(self.generation_update)
        self.optimization_thread.start()

    def optimization_finished(self, best):
        # Entpacken der gespeicherten Input-Werte aus dem Thread
        thread = self.optimization_thread
        nc = thread.nc
        lc = thread.lc
        n_prop = thread.n_prop
        wavelength = thread.wavelength

        # Entpacken der Werte aus dem besten Partikel
        l1, l3, theta, mirror1, mirror2 = best

        # Berechnung der Krümmungswerte basierend auf den Indizes
        mirror1 = int(np.clip(mirror1, 0, len(self.mirror_curvatures) - 1))
        mirror2 = int(np.clip(mirror2, 0, len(self.mirror_curvatures) - 1))
        r1_sag, r1_tan = self.mirror_curvatures[mirror1][:2]
        r2_sag, r2_tan = self.mirror_curvatures[mirror2][:2]

        # Berechnung der Waist-Größen mit den gespeicherten Werten
        roundtrip_matrix_sag = self.resonator_type.roundtrip_sagittal(nc, lc, n_prop, l1, l3, r1_sag, r2_sag, theta)
        roundtrip_matrix_tan = self.resonator_type.roundtrip_tangential(nc, lc, n_prop, l1, l3, r1_tan, r2_tan, theta)
        m_sag = np.abs((roundtrip_matrix_sag[0, 0] + roundtrip_matrix_sag[1, 1])/2)
        m_tan = np.abs((roundtrip_matrix_tan[0, 0] + roundtrip_matrix_tan[1, 1])/2)
        b_sag = np.abs(roundtrip_matrix_sag[0, 1])
        b_tan = np.abs(roundtrip_matrix_tan[0, 1])
        waist_sag = np.sqrt(((b_sag * wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_sag**2)))))
        waist_tan = np.sqrt(((b_tan * wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_tan**2)))))

        r1_sag = "Infinity" if r1_sag >= 1e+15 else r1_sag * 1e3
        r1_tan = "Infinity" if r1_tan >= 1e+15 else r1_tan * 1e3
        r2_sag = "Infinity" if r2_sag >= 1e+15 else r2_sag * 1e3
        r2_tan = "Infinity" if r2_tan >= 1e+15 else r2_tan * 1e3

        # Ausgabe der Ergebnisse
        print(f"Best solution found:")
        print(f"l1: {np.round(l1*1e3,3)} mm")
        print(f"l2: {np.round(((2 * l1) + lc + l3) / (2 * np.cos(2*theta))*1e3,3)} mm")
        print(f"l3: {np.round(l3*1e3,3)} mm")
        print(f"theta: {np.round(np.rad2deg(theta*2),3)} deg")
        print(f"r1_sag: {r1_sag} mm, r1_tan: {r1_tan} mm")
        print(f"r2_sag: {r2_sag} mm, r2_tan: {r2_tan} mm")
        print(f"waist_sag: {np.round(waist_sag*1e6,3)} um, waist_tan: {np.round(waist_tan*1e6,3)} um")
        print(f"m_sag: {np.round(m_sag,6)}, m_tan: {np.round(m_tan,6)}")
        print(f"Fitness: {np.round(best.fitness.values[0],6)}")
        return best

    def generation_update(self, gen, best_fitness):
        # Debugging-Ausgabe
        print(f"Generation {gen}: Best fitness = {best_fitness}")

    def stop_optimization(self):
        if hasattr(self, 'optimization_thread'):
            self.optimization_thread.stop()


class OptimizationThread(QThread):
    progress = pyqtSignal(int)  # Signal für den Fortschritt
    finished = pyqtSignal(object)  # Signal für das beste Ergebnis
    generation_update = pyqtSignal(int, float)  # Signal für Generation-Updates

    def __init__(self, resonator, population, toolbox, generation_count):
        super().__init__()
        self.resonator = resonator
        self.population = population
        self.toolbox = toolbox
        self.generation_count = generation_count
        self.abort_flag = False
        
        # Speichern der Input-Werte
        inputs = self.resonator.get_input()
        self.target_sag, self.target_tan, self.nc, self.lc, self.n_prop, self.wavelength = inputs

    def run(self):
        best = None
        for gen in range(self.generation_count):
            if self.abort_flag:
                break

            for part in self.population:
                part.fitness.values = self.toolbox.evaluate(part)
                if not part.best or part.best.fitness.values[0] > part.fitness.values[0]:
                    part.best = creator.Particle(part)
                    part.best.fitness.values = part.fitness.values
                if not best or best.fitness.values[0] > part.fitness.values[0]:
                    best = creator.Particle(part)
                    best.fitness.values = part.fitness.values

            for part in self.population:
                self.toolbox.update(part, best)

            self.progress.emit(gen + 1)
            self.generation_update.emit(gen, best.fitness.values[0])

        self.finished.emit(best)

    def stop(self):
        self.abort_flag = True