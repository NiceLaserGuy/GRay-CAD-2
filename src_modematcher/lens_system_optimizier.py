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
        
        # DEAP Setup entfernt - wird jetzt global in graycad_start.py gemacht
        self.toolbox = base.Toolbox()
        
        # Lade Linsenbibliothek aus temporärer Datei
        self._load_lens_library_from_temp_file()
        
        # Lade Beam-Parameter
        self.get_beam_parameters()

    def _load_lens_library_from_temp_file(self):
        """Lade Linsenbibliothek aus der temporären Datei"""
        try:
            temp_file_path = config.get_temp_file_path()
            if not temp_file_path:
                QMessageBox.critical(None, "Error", "Warning: No temp file path found, using default lens library")
                self._use_default_lens_library()
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
                    for key in ["Focal length tangential", "Focal length sagittal", "Focal length"]:
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
            QMessageBox.critical(None, "Error", "No lenses found in the lens library. Please check the temp file.")

    def get_beam_parameters(self):
        """Lade Strahlparameter aus der temporären Datei"""
        temp_data_modematcher = config.get_temp_data_modematcher()
        (self.wavelength, self.distance, self.waist_input_sag, self.waist_input_tan, 
        self.waist_position_sag, self.waist_position_tan, self.waist_goal_sag, 
        self.waist_goal_tan, self.waist_position_goal_sag, self.waist_position_goal_tan) = temp_data_modematcher

    def safe_crossover(self, ind1, ind2):
        """Sicherer Crossover für Individuen beliebiger Länge"""
        # For very short individuals, just swap them entirely
        if len(ind1) <= 1 or len(ind2) <= 1:
            ind1[:], ind2[:] = ind2[:], ind1[:]
            return ind1, ind2
            
        # For longer individuals, use two-point crossover
        try:
            return tools.cxTwoPoint(ind1, ind2)
        except Exception:
            # Fallback: swap random lens between individuals
            if len(ind1) > 0 and len(ind2) > 0:
                idx1 = random.randint(0, len(ind1) - 1)
                idx2 = random.randint(0, len(ind2) - 1)
                ind1[idx1], ind2[idx2] = ind2[idx2], ind1[idx1]
            return ind1, ind2

    def problem(self):
        """Erstelle das Problem-Objekt abhängig von der Anzahl der Linsen"""
        # Check if FitnessMin and Individual already exist in creator
        if not hasattr(creator, "FitnessMin"):
            creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMin)
        
        # Register the individual creation strategy
        self.toolbox.register("individual", self.build_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Register genetic operators
        self.toolbox.register("evaluate", self.fitness_function)
        # Use our safe crossover instead of standard cxTwoPoint
        self.toolbox.register("mate", self.safe_crossover)
        self.toolbox.register("mutate", self.mutate_lens_system, indpb=0.2)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def build_individual(self):
        """Erstelle ein neues Individuum (Linsensystem)"""
        individual = []
        
        # Zufällige Anzahl von Linsen (1 bis max_lenses)
        if self.max_lenses > 1:
            num_lenses = random.randint(1, self.max_lenses)
        else:
            # If max_lenses is 1, don't use randint
            num_lenses = 1
        
        # Für jede Linse: wähle eine zufällige Linse aus der Bibliothek und eine zufällige Position
        total_distance = self.distance  # Gesamtdistanz zwischen Eingangs- und Zielstrahl
        
        # FIX: Check if lens library is not empty
        if not self.lens_library:
            raise ValueError("Lens library is empty. Cannot create individuals.")
            
        for _ in range(num_lenses):
            # Wähle zufällige Linse
            lens = random.choice(self.lens_library)
            # Wähle zufällige Position (0 bis total_distance)
            position = random.uniform(0, total_distance)
            # Füge Linse und Position zum Individual hinzu
            individual.append((lens, position))
        
        # Sortiere Linsen nach Position
        individual.sort(key=lambda x: x[1])
        
        return creator.Individual(individual)
    
    def mutate_lens_system(self, individual, indpb):
        """Mutiere ein Linsensystem durch Ändern der Linsen oder Positionen"""
        # FIX: Check if lens library is not empty
        if not self.lens_library:
            return individual,
            
        for i in range(len(individual)):
            # Mit Wahrscheinlichkeit indpb, ändere die Linse
            if random.random() < indpb:
                individual[i] = (random.choice(self.lens_library), individual[i][1])
            
            # Mit Wahrscheinlichkeit indpb, ändere die Position
            if random.random() < indpb:
                individual[i] = (individual[i][0], random.uniform(0, self.distance))
        
        # Sortiere Linsen nach Position
        individual.sort(key=lambda x: x[1])
        return individual,
    
    def calculate_beam_parameters(self, individual):
        """Berechne die resultierenden Strahlparameter für ein gegebenes Linsensystem"""
        # Beam-Objekt erstellen
        from src_physics.beam import Beam
        beam = Beam()
        
        # Initialisiere mit den Eingangsparametern
        n = 1.0  # Brechungsindex von Luft
        
        # Berechne q-Parameter für sagittal und tangential
        q_sag = beam.q_value(0, self.waist_input_sag, self.wavelength, n)
        q_tan = beam.q_value(0, self.waist_input_tan, self.wavelength, n)
        
        # Sortiere Linsensystem nach Position
        sorted_system = sorted(individual, key=lambda x: x[1])
        
        # Optisches System aufbauen
        last_position = 0
        elements_sag = []
        elements_tan = []
        
        for lens, position in sorted_system:
            # Freie Propagation zur Linsenposition
            distance = position - last_position
            if distance > 0:
                elements_sag.append((beam.matrices.free_space, (distance, n)))
                elements_tan.append((beam.matrices.free_space, (distance, n)))
            
            # Linseneffekt hinzufügen
            elements_sag.append((beam.matrices.lens, (lens['focal_length'],)))
            elements_tan.append((beam.matrices.lens, (lens['focal_length'],)))
            
            # Position aktualisieren
            last_position = position
        
        # Propagation zum Ziel
        final_distance = self.distance - last_position
        if final_distance > 0:
            elements_sag.append((beam.matrices.free_space, (final_distance, n)))
            elements_tan.append((beam.matrices.free_space, (final_distance, n)))
        
        # Propagiere q-Parameter durch das System
        q_sag_final = q_sag
        q_tan_final = q_tan
        
        # Propagation durch jedes Element
        for element, params in elements_sag:
            if callable(element):
                abcd_matrix = element(*params)
                q_sag_final = beam.propagate_q(q_sag_final, abcd_matrix)
        
        for element, params in elements_tan:
            if callable(element):
                abcd_matrix = element(*params)
                q_tan_final = beam.propagate_q(q_tan_final, abcd_matrix)
        
        # Berechne Strahlparameter aus q-Parametern
        waist_sag = beam.beam_radius(q_sag_final, self.wavelength, n)
        waist_tan = beam.beam_radius(q_tan_final, self.wavelength, n)
        
        # Berechne Waist-Positionen
        # Für genaue Waist-Position müssten wir den Imaginary-Teil zu Null setzen und rückwärts propagieren
        # Vereinfachte Berechnung: 
        position_sag = self.distance - q_sag_final.real
        position_tan = self.distance - q_tan_final.real
        
        return waist_sag, waist_tan, position_sag, position_tan
    
    def fitness_function(self, individual):
        """Berechne Fitness für ein gegebenes Individuum"""
        # Berechne resultierende Strahlparameter
        waist_sag, waist_tan, position_sag, position_tan = self.calculate_beam_parameters(individual)
        
        # Berechne Abweichung von Zielparametern
        fitness_waist = abs(self.waist_goal_sag - waist_sag) + abs(self.waist_goal_tan - waist_tan)
        fitness_position = abs(self.waist_position_goal_sag - position_sag) + abs(self.waist_position_goal_tan - position_tan)
        
        # Gewichtung zwischen Strahlgröße und Position
        try:
            weight = self.ui.modematcher_calculation.weight_slider.value() / 100.0
        except AttributeError:
            # Fallback wenn UI nicht verfügbar
            weight = 0.5
            
        fitness = (1 - weight) * fitness_waist + weight * fitness_position
        
        return (fitness,)
    
    def optimize_lens_system(self, max_lenses):
        """Optimiere das Linsensystem mit einem genetischen Algorithmus"""
        try:
            # Validate input parameters
            if not self.lens_library:
                QMessageBox.warning(None, "Warning", "No lenses in library. Please select lenses first.")
                return None
                
            # FIX: Ensure max_lenses is at least 1
            self.max_lenses = max(1, max_lenses)
            
            # FIX: Make sure we have at least 2 individuals for crossover to work
            if len(self.lens_library) < 1:
                QMessageBox.warning(None, "Warning", "Not enough lenses in library. Need at least 1 lens.")
                return None
            
            # Problem definieren
            self.problem()
            
            # Startpopulation erzeugen
            pop_size = 50
            population = self.toolbox.population(n=pop_size)
            
            # Statistik-Objekt für Tracking
            stats = tools.Statistics(lambda ind: ind.fitness.values)
            stats.register("avg", np.mean)
            stats.register("min", np.min)
            stats.register("max", np.max)
            
            # Hall of Fame für die besten Individuen
            hof = tools.HallOfFame(1)
            
            # Genetischer Algorithmus ausführen
            algorithms.eaSimple(
                population, 
                self.toolbox,
                cxpb=0.5,      # Wahrscheinlichkeit für Crossover
                mutpb=0.2,      # Wahrscheinlichkeit für Mutation
                ngen=40,        # Anzahl der Generationen
                stats=stats,
                halloffame=hof,
                verbose=False   # Terminal-Ausgabe deaktivieren
            )
            
            # Bestes Individuum zurückgeben
            best_individual = hof[0]
            
            # Berechne finale Parameter
            waist_sag, waist_tan, position_sag, position_tan = self.calculate_beam_parameters(best_individual)
            
            # Ergebnisse vorbereiten
            result = {
                'lenses': [(lens['name'], lens['focal_length'], pos) for lens, pos in best_individual],
                'waist_sag': waist_sag,
                'waist_tan': waist_tan,
                'position_sag': position_sag,
                'position_tan': position_tan,
                'fitness': best_individual.fitness.values[0]
            }
            
            QMessageBox.information(None, "Optimization Complete", 
                                  f"Optimization completed successfully.\n"
                                  f"Final fitness: {result['fitness']:.6f}\n"
                                  f"Number of lenses: {len(best_individual)}")
            print (f"Final result: {result}")
            return result
            
        except Exception as e:
            QMessageBox.critical(None, "Optimization Error", f"Error during optimization: {str(e)}")
            return None