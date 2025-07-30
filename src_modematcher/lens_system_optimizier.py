import numpy as np
from deap import base, creator, tools, algorithms
from scipy.optimize import minimize
import random
import json
import config
from PyQt5.QtWidgets import QMessageBox

class LensSystemOptimizer:
    def __init__(self, matrices):
        self.matrices = matrices
        self.lens_library = []  # Wird dynamisch geladen
        
        # DEAP Setup (falls noch nicht existiert)
        if not hasattr(creator, "FitnessMin"):
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMin)
        
        self.toolbox = base.Toolbox()
        
        # Lade Linsenbibliothek aus temporärer Datei
        self._load_lens_library_from_temp_file()

        #Lade Strahlparameter aus temporärer Datei
        self.wavelength = None
        self.distance = None
        self.waist_input_sag = None
        self.waist_input_tan = None
        self.waist_position_sag = None
        self.waist_position_tan = None
        self.waist_goal_sag = None
        self.waist_goal_tan = None
        self.waist_position_goal_sag = None
        self.waist_position_goal_tan = None
        self.get_beam_parameters()  # Lade die Strahlparameter

    def _load_lens_library_from_temp_file(self):
        """Lade Linsenbibliothek aus der temporären Datei"""
        try:
            temp_file_path = config.get_temp_file_path()
            if not temp_file_path:
                QMessageBox.warning(self, "Error", "Warning: No temp file path found, using default lens library")
                return
            
            with open(temp_file_path, 'r') as file:
                data = json.load(file)
            
            components = data.get("components", [])
            self.lens_library = []
            
            for component in components:
                if component.get("type", "").upper() == "LENS":
                    # Extrahiere Linsendaten
                    properties = component.get("properties", {})
                    name = component.get("name", "Unknown Lens")
                    
                    # Bestimme Brennweite (verschiedene mögliche Felder)
                    focal_length = None
                    for key in ["Focal length tangential", "Focal length sagittal"]:
                        if key in properties:
                            focal_length = float(properties[key])
                            break
                    
                    if focal_length is not None:
                        lens_entry = {
                            'name': name,
                            'focal_length': focal_length,
                            'component_data': component  # Vollständige Komponentendaten für später
                        }
                        self.lens_library.append(lens_entry)
            
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading lens library from temp file: {e}, using fallback library")
    
    def get_beam_parameters(self):
        try:
            temp_data_modematcher = config.get_temp_data_modematcher()
            self.wavelength, self.distance, self.waist_input_sag, self.waist_input_tan, self.waist_position_sag, self.waist_position_tan, self.waist_goal_sag, self.waist_goal_tan, self.waist_position_goal_sag, self.waist_position_goal_tan = temp_data_modematcher
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading lens library from temp file: {e}.")

    def optimize_lens_system(self, max_lenses=3, max_length=1.0, n_medium=1.0):
        """
        Hauptoptimierungsfunktion - verwendet Parameter aus get_beam_parameters
        
        Parameters:
        - max_lenses: Maximale Anzahl Linsen
        - max_length: Maximale Systemlänge
        - n_medium: Brechungsindex des Mediums
        """
        
        if not self.lens_library:
            raise Exception("No lenses available in library")
        
        if not self.wavelength:
            raise Exception("No beam parameters loaded. Call get_beam_parameters() first.")
        
        # Verwende die geladenen Parameter
        w0_sag = self.waist_input_sag
        w0_tan = self.waist_input_tan
        z0_sag = self.waist_position_sag
        z0_tan = self.waist_position_tan
        w_target_sag = self.waist_goal_sag
        w_target_tan = self.waist_goal_tan
        z_target_sag = self.waist_position_goal_sag
        z_target_tan = self.waist_position_goal_tan
        wavelength = self.wavelength
        
        print(f"Optimizing for:")
        print(f"  Sagittal: w0={w0_sag:.6f}, z0={z0_sag:.3f} -> w_target={w_target_sag:.6f}, z_target={z_target_sag:.3f}")
        print(f"  Tangential: w0={w0_tan:.6f}, z0={z0_tan:.3f} -> w_target={w_target_tan:.6f}, z_target={z_target_tan:.3f}")
        print(f"  Wavelength: {wavelength:.9f}")
        
        # 1. PHASE: Genetischer Algorithmus für globale Optimierung (beide Ebenen)
        best_individual = self._genetic_optimization_dual(
            w0_sag, z0_sag, w_target_sag, z_target_sag,
            w0_tan, z0_tan, w_target_tan, z_target_tan,
            wavelength, max_lenses, max_length, n_medium)
        
        # 2. PHASE: Lokale Verfeinerung mit scipy.optimize (beide Ebenen)
        refined_solution = self._local_refinement_dual(
            best_individual, 
            w0_sag, z0_sag, w_target_sag, z_target_sag,
            w0_tan, z0_tan, w_target_tan, z_target_tan,
            wavelength, n_medium)
        
        # 3. PHASE: Ergebnis-Konvertierung
        optimized_system = self._convert_to_optical_system_dual(
            refined_solution, w0_sag, w0_tan, z0_sag, z0_tan, wavelength)
        
        return optimized_system
    
    def _genetic_optimization(self, w0, z0, w_target, z_target, wavelength, 
                            max_lenses, max_length, n_medium):
        """Genetischer Algorithmus für globale Optimierung"""
        
        # Individual-Struktur: [n_lenses, lens1_type, lens1_pos, lens2_type, lens2_pos, ...]
        def create_individual():
            n_lenses = random.randint(1, max_lenses)
            individual = [n_lenses]
            
            for i in range(max_lenses):
                if i < n_lenses:
                    # Lens type (Index in der Bibliothek)
                    lens_type = random.randint(0, len(self.lens_library) - 1)
                    # Position (0 bis max_length)
                    position = random.uniform(0, max_length)
                    individual.extend([lens_type, position])
                else:
                    # Inaktive Linse
                    individual.extend([-1, 0.0])
            
            return creator.Individual(individual)
        
        # Fitness-Funktion
        def evaluate_fitness(individual):
            return (self._calculate_error(individual, w0, z0, w_target, z_target, 
                                        wavelength, n_medium),)
        
        # Crossover-Funktion
        def crossover_lenses(ind1, ind2):
            # Intelligenter Crossover für Linsensysteme
            tools.cxTwoPoint(ind1, ind2)
            
            # Repariere n_lenses falls nötig
            ind1[0] = max(1, min(max_lenses, int(ind1[0])))
            ind2[0] = max(1, min(max_lenses, int(ind2[0])))
            
            return ind1, ind2
        
        # Mutations-Funktion
        def mutate_lenses(individual, mu=0, sigma=0.1):
            # Mutiere Anzahl Linsen (selten)
            if random.random() < 0.1:
                individual[0] = max(1, min(max_lenses, 
                                  individual[0] + random.randint(-1, 1)))
            
            # Mutiere Linsentypen und Positionen
            for i in range(max_lenses):
                lens_type_idx = 1 + i * 2
                position_idx = 2 + i * 2
                
                if i < individual[0]:  # Aktive Linse
                    # Linsentyp mutieren
                    if random.random() < 0.2:
                        individual[lens_type_idx] = random.randint(0, len(self.lens_library) - 1)
                    
                    # Position mutieren
                    if random.random() < 0.5:
                        individual[position_idx] += random.gauss(mu, sigma * max_length)
                        individual[position_idx] = max(0, min(max_length, individual[position_idx]))
            
            return individual,
        
        # DEAP Toolbox konfigurieren
        self.toolbox.register("individual", create_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", evaluate_fitness)
        self.toolbox.register("mate", crossover_lenses)
        self.toolbox.register("mutate", mutate_lenses)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        
        # GA-Parameter
        population_size = 100
        generations = 50
        crossover_prob = 0.7
        mutation_prob = 0.3
        
        # Evolutionärer Algorithmus
        population = self.toolbox.population(n=population_size)
        
        # Hall of Fame für beste Individuen
        hof = tools.HallOfFame(1)
        
        # Statistiken
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Evolution ausführen
        population, logbook = algorithms.eaSimple(
            population, self.toolbox, crossover_prob, mutation_prob, 
            generations, stats=stats, halloffame=hof, verbose=True)
        
        return hof[0]  # Bestes Individuum
    
    def _local_refinement(self, ga_solution, w0, z0, w_target, z_target, wavelength, n_medium):
        """Lokale Verfeinerung mit scipy.optimize"""
        
        # Extrahiere nur die Positionen für lokale Optimierung
        n_lenses = int(ga_solution[0])
        positions = []
        lens_types = []
        
        for i in range(n_lenses):
            lens_type = int(ga_solution[1 + i * 2])
            position = ga_solution[2 + i * 2]
            lens_types.append(lens_type)
            positions.append(position)
        
        # Optimiere nur Positionen (Linsentypen bleiben fix)
        def objective(positions_array):
            # Baue Individual für Fehlerberechnung
            temp_individual = [n_lenses]
            for i, pos in enumerate(positions_array):
                temp_individual.extend([lens_types[i], pos])
            
            # Fülle mit inaktiven Linsen auf
            max_lenses = (len(ga_solution) - 1) // 2
            for i in range(n_lenses, max_lenses):
                temp_individual.extend([-1, 0.0])
            
            return self._calculate_error(temp_individual, w0, z0, w_target, z_target, 
                                       wavelength, n_medium)
        
        # Grenzen für Positionen
        bounds = [(0, 1.0) for _ in range(n_lenses)]
        
        # Lokale Optimierung
        result = minimize(objective, positions, method='L-BFGS-B', bounds=bounds)
        
        # Baue finales Individual
        refined_individual = [n_lenses]
        for i, pos in enumerate(result.x):
            refined_individual.extend([lens_types[i], pos])
        
        # Fülle mit inaktiven Linsen auf
        max_lenses = (len(ga_solution) - 1) // 2
        for i in range(n_lenses, max_lenses):
            refined_individual.extend([-1, 0.0])
        
        return refined_individual
    
    def _local_refinement_dual(self, ga_solution, 
                          w0_sag, z0_sag, w_target_sag, z_target_sag,
                          w0_tan, z0_tan, w_target_tan, z_target_tan,
                          wavelength, n_medium):
        """Lokale Verfeinerung mit scipy.optimize für beide Ebenen"""
        
        # Extrahiere nur die Positionen für lokale Optimierung
        n_lenses = int(ga_solution[0])
        positions = []
        lens_types = []
        
        for i in range(n_lenses):
            lens_type = int(ga_solution[1 + i * 2])
            position = ga_solution[2 + i * 2]
            lens_types.append(lens_type)
            positions.append(position)
        
        # Optimiere nur Positionen (Linsentypen bleiben fix)
        def objective_dual(positions_array):
            # Baue Individual für Fehlerberechnung
            temp_individual = [n_lenses]
            for i, pos in enumerate(positions_array):
                temp_individual.extend([lens_types[i], pos])
            
            # Fülle mit inaktiven Linsen auf
            max_lenses = (len(ga_solution) - 1) // 2
            for i in range(n_lenses, max_lenses):
                temp_individual.extend([-1, 0.0])
            
            return self._calculate_error_dual(temp_individual,
                                        w0_sag, z0_sag, w_target_sag, z_target_sag,
                                        w0_tan, z0_tan, w_target_tan, z_target_tan,
                                        wavelength, n_medium)
    
        # Grenzen für Positionen
        bounds = [(0, 1.0) for _ in range(n_lenses)]
        
        try:
            # Lokale Optimierung
            result = minimize(objective_dual, positions, method='L-BFGS-B', bounds=bounds)
            positions = result.x
        except Exception as e:
            print(f"Local refinement failed: {e}, using GA solution")
            # Bei Fehlern verwende GA-Lösung
        
        # Baue finales Individual
        refined_individual = [n_lenses]
        for i, pos in enumerate(positions):
            refined_individual.extend([lens_types[i], pos])
        
        # Fülle mit inaktiven Linsen auf
        max_lenses = (len(ga_solution) - 1) // 2
        for i in range(n_lenses, max_lenses):
            refined_individual.extend([-1, 0.0])
        
        return refined_individual
    
    def _calculate_error(self, individual, w0, z0, w_target, z_target, wavelength, n_medium):
        """Berechne Fitnessfunktion (Fehler zwischen Ist und Soll)"""
        try:
            # Baue optisches System aus Individual
            optical_system = self._build_system_from_individual(individual)
            
            # Start-q-Parameter
            from src_physics.beam import Beam
            beam = Beam()
            q_start = beam.q_value(z0, w0, wavelength, n_medium)
            
            # Propagiere durch System
            q_final = q_start
            for element, param in optical_system:
                if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                    # Freiraum
                    A, B, C, D = 1, param[0]/param[1], 0, 1
                else:
                    # Optisches Element
                    if isinstance(param, tuple):
                        ABCD = element(*param)
                    else:
                        ABCD = element(param)
                    A, B, C, D = ABCD.flatten()
                
                q_final = (A * q_final + B) / (C * q_final + D)
            
            # Ziel-Strahlparameter berechnen
            w_final = beam.beam_radius(q_final, wavelength, n_medium)
            z_final = 0  # Bei gegebener Position
            
            # Fehler berechnen (gewichtete Summe)
            w_error = abs(w_final - w_target) / w_target
            # z_error für Position könnte hier hinzugefügt werden
            
            total_error = w_error
            
            # Penalty für zu viele Linsen
            n_lenses = individual[0]
            complexity_penalty = 0.1 * n_lenses
            
            return total_error + complexity_penalty
            
        except Exception as e:
            # Bei Fehlern hohe Strafe
            return 1000.0
    
    def _build_system_from_individual(self, individual):
        """Baue optisches System aus GA-Individual"""
        optical_system = []
        n_lenses = int(individual[0])
        
        # Sammle alle Linsen mit Positionen
        lenses = []
        for i in range(n_lenses):
            lens_type_idx = 1 + i * 2
            position_idx = 2 + i * 2
            
            lens_type = int(individual[lens_type_idx])
            position = individual[position_idx]
            
            if lens_type >= 0 and lens_type < len(self.lens_library):
                lenses.append((position, lens_type))
        
        # Sortiere nach Position
        lenses.sort(key=lambda x: x[0])
        
        # Baue System: Freiraum -> Linse -> Freiraum -> Linse -> ...
        current_pos = 0
        for pos, lens_type in lenses:
            # Freiraum bis zur Linse
            if pos > current_pos:
                distance = pos - current_pos
                optical_system.append((self.matrices.free_space, (distance, 1.0)))
            
            # Linse
            lens_data = self.lens_library[lens_type]
            focal_length = lens_data['focal_length']
            optical_system.append((self.matrices.thin_lens, focal_length))
            
            current_pos = pos
        
        return optical_system
    
    def _convert_to_optical_system(self, solution, w0, z0, wavelength):
        """Konvertiere Lösung in Setup-Format für GUI mit korrekten Beam-Parametern"""
        optical_system = self._build_system_from_individual(solution)
        
        setup_components = []
        
        # Start mit Beam (mit korrekten Parametern)
        setup_components.append({
            "type": "BEAM",
            "name": "Optimized Beam",
            "properties": {
                "Wavelength": wavelength,
                "Waist radius sagittal": w0,
                "Waist radius tangential": w0,
                "Waist position sagittal": z0,
                "Waist position tangential": z0
            }
        })
        
        # Füge optische Elemente hinzu
        for element, param in optical_system:
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                setup_components.append({
                    "type": "FREESPACE",
                    "name": f"Free Space {param[0]:.3f}m",
                    "properties": {
                        "Distance": param[0],
                        "Refractive index": param[1]
                    }
                })
            else:
                # Linse - verwende Original-Komponentendaten wenn verfügbar
                lens_focal_length = param
                lens_name = f"Lens f={lens_focal_length:.3f}m"
                
                # Finde die entsprechende Linse in der Bibliothek
                matching_lens = None
                for lens in self.lens_library:
                    if abs(lens['focal_length'] - lens_focal_length) < 1e-6:
                        matching_lens = lens
                        break
                
                if matching_lens and matching_lens['component_data']:
                    # Verwende Original-Komponentendaten
                    lens_component = matching_lens['component_data'].copy()
                    setup_components.append(lens_component)
                else:
                    # Fallback: Erstelle Standard-Linsenkomponente
                    setup_components.append({
                        "type": "LENS",
                        "name": lens_name,
                        "properties": {
                            "Focal length sagittal": lens_focal_length,
                            "Focal length tangential": lens_focal_length
                        }
                    })
        
        return setup_components
    
    def _convert_to_optical_system_dual(self, solution, w0_sag, w0_tan, z0_sag, z0_tan, wavelength):
        """Konvertiere Lösung in Setup-Format für GUI mit beiden Ebenen"""
        optical_system = self._build_system_from_individual(solution)
        
        setup_components = []
        
        # Start mit Beam (mit korrekten Parametern für beide Ebenen)
        setup_components.append({
            "type": "BEAM",
            "name": "Optimized Beam",
            "properties": {
                "Wavelength": wavelength,
                "Waist radius sagittal": w0_sag,
                "Waist radius tangential": w0_tan,
                "Waist position sagittal": z0_sag,
                "Waist position tangential": z0_tan
            }
        })
        
        # Füge optische Elemente hinzu
        for element, param in optical_system:
            if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                setup_components.append({
                    "type": "FREESPACE",
                    "name": f"Free Space {param[0]:.3f}m",
                    "properties": {
                        "Distance": param[0],
                        "Refractive index": param[1]
                    }
                })
            else:
                # Linse - verwende Original-Komponentendaten mit beiden Brennweiten
                lens_focal_length = param
                
                # Finde die entsprechende Linse in der Bibliothek
                matching_lens = None
                for lens in self.lens_library:
                    if abs(lens['focal_length'] - lens_focal_length) < 1e-6:
                        matching_lens = lens
                        break
                
                if matching_lens and matching_lens['component_data']:
                    # Verwende Original-Komponentendaten
                    lens_component = matching_lens['component_data'].copy()
                    setup_components.append(lens_component)
                else:
                    # Fallback: Erstelle Standard-Linsenkomponente mit beiden Brennweiten
                    lens_name = f"Lens f={lens_focal_length:.3f}m"
                    setup_components.append({
                        "type": "LENS",
                        "name": lens_name,
                        "properties": {
                            "Focal length sagittal": lens_focal_length,
                            "Focal length tangential": lens_focal_length
                        }
                    })
    
        return setup_components
    
    def _genetic_optimization_dual(self, w0_sag, z0_sag, w_target_sag, z_target_sag,
                                  w0_tan, z0_tan, w_target_tan, z_target_tan,
                                  wavelength, max_lenses, max_length, n_medium):
        """Genetischer Algorithmus für beide Ebenen gleichzeitig"""
        
        # Individual-Struktur: [n_lenses, lens1_type, lens1_pos, lens2_type, lens2_pos, ...]
        def create_individual():
            n_lenses = random.randint(1, max_lenses)
            individual = [n_lenses]
            
            for i in range(max_lenses):
                if i < n_lenses:
                    # Lens type (Index in der Bibliothek)
                    lens_type = random.randint(0, len(self.lens_library) - 1)
                    # Position (0 bis max_length)
                    position = random.uniform(0, max_length)
                    individual.extend([lens_type, position])
                else:
                    # Inaktive Linse
                    individual.extend([-1, 0.0])
            
            return creator.Individual(individual)
        
        # Fitness-Funktion für beide Ebenen
        def evaluate_fitness_dual(individual):
            return (self._calculate_error_dual(individual, 
                                             w0_sag, z0_sag, w_target_sag, z_target_sag,
                                             w0_tan, z0_tan, w_target_tan, z_target_tan,
                                             wavelength, n_medium),)
        
        # Crossover-Funktion (gleich wie vorher)
        def crossover_lenses(ind1, ind2):
            tools.cxTwoPoint(ind1, ind2)
            ind1[0] = max(1, min(max_lenses, int(ind1[0])))
            ind2[0] = max(1, min(max_lenses, int(ind2[0])))
            return ind1, ind2
        
        # Mutations-Funktion (gleich wie vorher)
        def mutate_lenses(individual, mu=0, sigma=0.1):
            if random.random() < 0.1:
                individual[0] = max(1, min(max_lenses, 
                              individual[0] + random.randint(-1, 1)))
            
            for i in range(max_lenses):
                lens_type_idx = 1 + i * 2
                position_idx = 2 + i * 2
                
                if i < individual[0]:
                    if random.random() < 0.2:
                        individual[lens_type_idx] = random.randint(0, len(self.lens_library) - 1)
                    
                    if random.random() < 0.5:
                        individual[position_idx] += random.gauss(mu, sigma * max_length)
                        individual[position_idx] = max(0, min(max_length, individual[position_idx]))
        
            return individual,
        
        # DEAP Toolbox neu konfigurieren
        self.toolbox.unregister("individual")
        self.toolbox.unregister("population") 
        self.toolbox.unregister("evaluate")
        self.toolbox.unregister("mate")
        self.toolbox.unregister("mutate")
        self.toolbox.unregister("select")
        
        self.toolbox.register("individual", create_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", evaluate_fitness_dual)
        self.toolbox.register("mate", crossover_lenses)
        self.toolbox.register("mutate", mutate_lenses)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        
        # GA-Parameter
        population_size = 100
        generations = 50
        crossover_prob = 0.7
        mutation_prob = 0.3
        
        # Evolutionärer Algorithmus
        population = self.toolbox.population(n=population_size)
        
        # Hall of Fame für beste Individuen
        hof = tools.HallOfFame(1)
        
        # Statistiken
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Evolution ausführen
        population, logbook = algorithms.eaSimple(
            population, self.toolbox, crossover_prob, mutation_prob, 
            generations, stats=stats, halloffame=hof, verbose=True)
        
        return hof[0]  # Bestes Individuum
    
    def _calculate_error_dual(self, individual, 
                         w0_sag, z0_sag, w_target_sag, z_target_sag,
                         w0_tan, z0_tan, w_target_tan, z_target_tan,
                         wavelength, n_medium):
        """Berechne Fitnessfunktion für beide Ebenen"""
        try:
            # Baue optisches System aus Individual
            optical_system = self._build_system_from_individual(individual)
            
            from src_physics.beam import Beam
            beam = Beam()
            
            # === SAGITTALE EBENE ===
            q_start_sag = beam.q_value(z0_sag, w0_sag, wavelength, n_medium)
            q_final_sag = q_start_sag
            
            for element, param in optical_system:
                if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                    # Freiraum
                    A, B, C, D = 1, param[0]/param[1], 0, 1
                else:
                    # Optisches Element - verwende sagittale Brennweite
                    lens_data = self._get_lens_data_from_param(param)
                    if lens_data:
                        focal_length_sag = self._get_sagittal_focal_length(lens_data)
                        ABCD = self.matrices.thin_lens(focal_length_sag)
                    else:
                        ABCD = self.matrices.thin_lens(param)  # Fallback
                    A, B, C, D = ABCD.flatten()
            
                q_final_sag = (A * q_final_sag + B) / (C * q_final_sag + D)
            
            # === TANGENTIALE EBENE ===
            q_start_tan = beam.q_value(z0_tan, w0_tan, wavelength, n_medium)
            q_final_tan = q_start_tan
            
            for element, param in optical_system:
                if hasattr(element, "__func__") and element.__func__ is self.matrices.free_space.__func__:
                    # Freiraum (gleich für beide Ebenen)
                    A, B, C, D = 1, param[0]/param[1], 0, 1
                else:
                    # Optisches Element - verwende tangentiale Brennweite
                    lens_data = self._get_lens_data_from_param(param)
                    if lens_data:
                        focal_length_tan = self._get_tangential_focal_length(lens_data)
                        ABCD = self.matrices.thin_lens(focal_length_tan)
                    else:
                        ABCD = self.matrices.thin_lens(param)  # Fallback
                    A, B, C, D = ABCD.flatten()
            
                q_final_tan = (A * q_final_tan + B) / (C * q_final_tan + D)
            
            # Berechne finale Strahlparameter
            w_final_sag = beam.beam_radius(q_final_sag, wavelength, n_medium)
            w_final_tan = beam.beam_radius(q_final_tan, wavelength, n_medium)
            
            # Fehler berechnen (gewichtete Summe beider Ebenen)
            w_error_sag = abs(w_final_sag - w_target_sag) / w_target_sag
            w_error_tan = abs(w_final_tan - w_target_tan) / w_target_tan
            
            # Kombinierter Fehler (gleiche Gewichtung beider Ebenen)
            total_error = 0.5 * (w_error_sag + w_error_tan)
            
            # Penalty für zu viele Linsen
            n_lenses = individual[0]
            complexity_penalty = 0.1 * n_lenses
            
            # Zusätzliche Penalty wenn eine Ebene sehr schlecht ist
            max_error = max(w_error_sag, w_error_tan)
            if max_error > 0.5:  # Wenn eine Ebene >50% Fehler hat
                balance_penalty = max_error * 0.5
            else:
                balance_penalty = 0
            
            return total_error + complexity_penalty + balance_penalty
            
        except Exception as e:
            # Bei Fehlern hohe Strafe
            print(f"Error in fitness calculation: {e}")
            return 1000.0

    def _get_lens_data_from_param(self, param):
        """Extrahiere Linsendaten basierend auf Brennweite"""
        for lens in self.lens_library:
            if abs(lens['focal_length'] - param) < 1e-6:
                return lens['component_data']
        return None

    def _get_sagittal_focal_length(self, lens_data):
        """Extrahiere sagittale Brennweite aus Linsendaten"""
        if not lens_data:
            return None
        properties = lens_data.get("properties", {})
        return properties.get("Focal length sagittal", properties.get("Focal length", None))

    def _get_tangential_focal_length(self, lens_data):
        """Extrahiere tangentiale Brennweite aus Linsendaten"""
        if not lens_data:
            return None
        properties = lens_data.get("properties", {})
        return properties.get("Focal length tangential", properties.get("Focal length", None))