import json
import numpy as np
from deap import base, creator, tools
from matrices import Matrices
from os import path

class Resonator:
    
    def __init__(self):
        self.matrices = Matrices()
        self.ui_resonator = None  # Initialize ui_resonator as None
        self.mirror_curvatures = []

    def load_mirror_data(self, filepath):
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
                # Speichern der Daten als Tupel (sagittal, tangential, is_round)
                self.mirror_curvatures.append((curvature_sagittal, curvature_tangential, is_round))

        # Debugging-Ausgabe
        if not self.mirror_curvatures:
            raise ValueError("Die Liste 'mirror_curvatures' ist leer. Überprüfen Sie die Datei 'Mirrors.json'.")
    
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
        # Laden der Spiegel-Daten
        self.load_mirror_data(path.abspath(path.join(path.dirname(__file__), "Library/Mirrors.json")))
        
        # Debugging-Ausgabe, um sicherzustellen, dass die Daten geladen wurden
        if not self.mirror_curvatures:
            raise ValueError("Die Liste 'mirror_curvatures' ist leer. Überprüfen Sie die Datei 'Mirrors.json'.")
        
        inputs = self.get_input()
        target_sag, target_tan, nc, lc, n_prop, wavelength = inputs

        # Define the fitness function
        def objective(individual):
            l1, l3, theta, mirror1, mirror2 = individual
            mirror1 = int(np.clip(mirror1, 0, len(self.mirror_curvatures) - 1))
            mirror2 = int(np.clip(mirror2, 0, len(self.mirror_curvatures) - 1))
            r1_sag, r1_tan = self.mirror_curvatures[mirror1][:2]
            r2_sag, r2_tan = self.mirror_curvatures[mirror2][:2]
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

            if waist_sag == waist_tan:
                fitness_value = np.sqrt(
                    ((waist_sag - target_sag) / target_sag)**2 +
                    ((waist_tan - target_tan) / target_tan)**2 +
                    (1 / 100) * m_sag**2 +
                    (1 / 100) * m_tan**2
                )
                return fitness_value,
    
            if abs(m_sag) > 1 or abs(m_tan) > 1:
                return 1e6,

        # DEAP setup for PSO
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Particle", list, fitness=creator.FitnessMin, speed=list, smin=None, smax=None, best=None)

        def generate(size, pmin, pmax, smin, smax):
            if len(self.mirror_curvatures) == 0:
                raise ValueError("Die Liste 'mirror_curvatures' ist leer. Stellen Sie sicher, dass 'load_mirror_data' korrekt aufgerufen wurde und die Datei 'Mirrors.json' gültige Daten enthält.")
            
            l1_min, l1_max = float(self.ui_resonator.edit_lower_bound_l1.text())*1e-3, float(self.ui_resonator.edit_upper_bound_l1.text())*1e-3  # Grenzen für l1 (in Metern)
            l3_min, l3_max = float(self.ui_resonator.edit_lower_bound_l3.text())*1e-3, float(self.ui_resonator.edit_upper_bound_l3.text())*1e-3  # Grenzen für l3 (in Metern)
            theta_min, theta_max = np.deg2rad(float(self.ui_resonator.edit_lower_bound_theta.text())), np.deg2rad(float(self.ui_resonator.edit_upper_bound_theta.text()))  # Grenzen für theta (in Radiant)

            particle = creator.Particle([
                np.random.uniform(l1_min, l1_max) if i == 0 else
                np.random.uniform(l3_min, l3_max) if i == 1 else
                np.random.uniform(theta_min, theta_max) if i == 2 else
                np.random.randint(0, len(self.mirror_curvatures))  # Für mirror1 und mirror2
                for i in range(size)
            ])
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

            # Grenzen für l1, l3 und theta sicherstellen
            l1_min, l1_max = float(self.ui_resonator.edit_lower_bound_l1.text()) * 1e-3, float(self.ui_resonator.edit_upper_bound_l1.text()) * 1e-3
            l3_min, l3_max = float(self.ui_resonator.edit_lower_bound_l3.text()) * 1e-3, float(self.ui_resonator.edit_upper_bound_l3.text()) * 1e-3
            theta_min, theta_max = np.deg2rad(float(self.ui_resonator.edit_lower_bound_theta.text())), np.deg2rad(float(self.ui_resonator.edit_upper_bound_theta.text()))

            part[:] = [
                np.clip(p + v, l1_min, l1_max) if i == 0 else
                np.clip(p + v, l3_min, l3_max) if i == 1 else
                np.clip(p + v, theta_min, theta_max) if i == 2 else
                int(np.clip(round(p + v), 0, len(self.mirror_curvatures) - 1))
                for i, (p, v) in enumerate(zip(part, part.speed))
            ]

        toolbox = base.Toolbox()
        toolbox.register("particle", generate, size=5, pmin=0.025, pmax=1.0, smin=-2, smax=2)
        toolbox.register("population", tools.initRepeat, list, toolbox.particle)
        toolbox.register("update", update_particle, phi1=float(self.ui_resonator.edit_phi1_float.text()), phi2=float(self.ui_resonator.edit_phi2_float.text()))
        toolbox.register("evaluate", objective)

        # Create the population
        population = toolbox.population(n=int(float(self.ui_resonator.edit_population_number.text())))

        # PSO loop
        best = None
        for gen in range(int(float(self.ui_resonator.edit_generation_number.text()))):
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

        # Entpacken der Werte aus dem besten Partikel
        l1, l3, theta, mirror1, mirror2 = best

        # Berechnung der Krümmungswerte basierend auf den Indizes
        mirror1 = int(np.clip(mirror1, 0, len(self.mirror_curvatures) - 1))
        mirror2 = int(np.clip(mirror2, 0, len(self.mirror_curvatures) - 1))
        r1_sag, r1_tan = self.mirror_curvatures[mirror1][:2]
        r2_sag, r2_tan = self.mirror_curvatures[mirror2][:2]

        # Berechnung der Waist-Größen
        roundtrip_matrix_sag = self.matrices.roundtrip_sagittal(nc, lc, n_prop, l1, l3, r1_sag, r2_sag, theta)
        roundtrip_matrix_tan = self.matrices.roundtrip_tangential(nc, lc, n_prop, l1, l3, r1_tan, r2_tan, theta)
        m_sag = np.abs(roundtrip_matrix_sag[0, 0] - roundtrip_matrix_sag[1, 1])
        m_tan = np.abs(roundtrip_matrix_tan[0, 0] - roundtrip_matrix_tan[1, 1])
        b_sag = np.abs(roundtrip_matrix_sag[0, 1])
        b_tan = np.abs(roundtrip_matrix_tan[0, 1])
        waist_sag = np.sqrt((b_sag * wavelength) / (np.pi) * (np.sqrt(np.abs(1 / (1 - m_sag**2)))))
        waist_tan = np.sqrt((b_tan * wavelength) / (np.pi) * (np.sqrt(np.abs(1 / (1 - m_tan**2)))))

        r1_sag = "Infinity" if r1_sag >= 1e+15 else r1_sag * 1e3
        r1_tan = "Infinity" if r1_tan >= 1e+15 else r1_tan * 1e3
        r2_sag = "Infinity" if r2_sag >= 1e+15 else r2_sag * 1e3
        r2_tan = "Infinity" if r2_tan >= 1e+15 else r2_tan * 1e3

        # Ausgabe der Ergebnisse
        print(f"Best solution found:")
        print(f"l1: {l1*1e3} mm")
        print(f"l3: {l3*1e3} mm")
        print(f"theta: {np.rad2deg(theta)} deg")
        print(f"r1_sag: {r1_sag} mm, r1_tan: {r1_tan} mm")
        print(f"r2_sag: {r2_sag} mm, r2_tan: {r2_tan} mm")
        print(f"waist_sag: {waist_sag*1e6} um, waist_tan: {waist_tan*1e6} um")
        print(f"Fitness: {best.fitness.values[0]}")
        return best