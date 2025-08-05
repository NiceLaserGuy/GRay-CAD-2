import numpy as np
from deap import base, creator, tools, algorithms
from scipy.optimize import minimize
import random
import json
import config
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

class OptimizationWorker(QObject):
    """Worker-Klasse für die Durchführung der Optimierung in einem separaten Thread"""
    finished = pyqtSignal(dict)  # Signal mit Optimierungsergebnis
    error = pyqtSignal(str)      # Signal für Fehler
    progress = pyqtSignal(int, int)   # Signal für Fortschrittsanzeige (aktueller Wert, Maximum)
    
    def __init__(self, optimizer, max_lenses, num_runs=3):
        super().__init__()
        self.optimizer = optimizer
        self.max_lenses = max_lenses
        self.num_runs = num_runs
        self.abort_flag = False
        
    @pyqtSlot()
    def run(self):
        """Führt die Optimierung in einem separaten Thread aus"""
        try:
            # Validiere Parameter
            if not self.optimizer.lens_library:
                self.error.emit("No lenses in library. Please select lenses first.")
                return
                
            # Stellt sicher, dass max_lenses mindestens 1 ist
            max_lenses = max(1, self.max_lenses)
            
            # Stellt sicher, dass genügend Linsen in der Bibliothek vorhanden sind
            if len(self.optimizer.lens_library) < 1:
                self.error.emit("Not enough lenses in library. Need at least 1 lens.")
                return
            
            # Führe Multi-Run Optimierung durch
            result = self._run_multi_optimization(max_lenses, self.num_runs)
            
            # Sende Ergebnis zurück
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"Error during optimization: {str(e)}")
    
    def _run_multi_optimization(self, max_lenses, num_runs):
        """Führt mehrere Durchläufe der Optimierung durch und gibt das beste Ergebnis zurück"""
        best_result = None
        best_fitness = float('inf')
        
        total_generations = 50  # Anzahl der Generationen pro Lauf
        total_steps = num_runs * total_generations
        
        # Setze max_lenses für den Optimizer
        self.optimizer.max_lenses = max_lenses
        
        # Problem definieren (nur einmal)
        self.optimizer.problem()
        
        for run in range(num_runs):
            if self.abort_flag:
                break
                
            # Emittiere Fortschritt
            self.progress.emit(run * total_generations, total_steps)
            
            # Startpopulation erzeugen
            pop_size = 70
            population = self.optimizer.toolbox.population(n=pop_size)
            
            # Statistik-Objekt für Tracking
            stats = tools.Statistics(lambda ind: ind.fitness.values)
            stats.register("avg", np.mean)
            stats.register("min", np.min)
            stats.register("max", np.max)
            
            # Hall of Fame für die besten Individuen
            hof = tools.HallOfFame(1)
            
            # Genetischer Algorithmus ausführen
            for gen in range(total_generations):
                if self.abort_flag:
                    break
                    
                # Ein Schritt des Algorithmus
                population = algorithms.varAnd(population, self.optimizer.toolbox, 0.5, 0.2)
                
                # Bewerte Population
                fits = self.optimizer.toolbox.map(self.optimizer.toolbox.evaluate, population)
                for fit, ind in zip(fits, population):
                    ind.fitness.values = fit
                
                # Selektiere für nächste Generation
                population = self.optimizer.toolbox.select(population, len(population))
                
                # Aktualisiere Hall of Fame
                hof.update(population)
                
                # Emittiere Fortschritt
                self.progress.emit(run * total_generations + gen + 1, total_steps)
            
            if not self.abort_flag and hof:
                # Berechne Parameter für das beste Individuum dieses Laufs
                best_individual = hof[0]
                current_fitness = best_individual.fitness.values[0]
                
                # Wenn besser als bisher bestes Ergebnis, aktualisiere
                if current_fitness < best_fitness:
                    waist_sag, waist_tan, position_sag, position_tan = self.optimizer.calculate_beam_parameters(best_individual)
                    
                    best_result = {
                        'lenses': [(lens['name'], lens['focal_length'], pos) for lens, pos in best_individual],
                        'waist_sag': waist_sag,
                        'waist_tan': waist_tan,
                        'position_sag': position_sag,
                        'position_tan': position_tan,
                        'fitness': current_fitness,
                        'run': run + 1
                    }
                    best_fitness = current_fitness
        
        return best_result
    
    def stop(self):
        """Bricht die Optimierung ab"""
        self.abort_flag = True

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
                    
                    # Bestimme Linsentyp basierend auf IS_ROUND
                    is_round = properties.get("IS_ROUND", True)
                    lens_type = "spherical" if is_round else "cylindrical"
                    
                    # Extrahiere Brennweiten für beide Achsen
                    f_sag = None
                    f_tan = None
                    
                    # Extrahiere sagittale und tangentiale Brennweite direkt
                    for key in ["Focal length sagittal", "focal length sagittal"]:
                        if key in properties:
                            f_sag = float(properties[key])
                            break
                    
                    for key in ["Focal length tangential", "focal length tangential"]:
                        if key in properties:
                            f_tan = float(properties[key])
                            break
                    
                    # Wenn keine spezifischen Brennweiten gefunden wurden, suche nach allgemeiner Brennweite
                    if f_sag is None and f_tan is None:
                        for key in ["Focal length", "focal length"]:
                            if key in properties:
                                f_sag = f_tan = float(properties[key])
                                break
                    
                    # Wenn wir eine Brennweite haben, füge die Linse zur Bibliothek hinzu
                    if f_sag is not None or f_tan is not None:
                        # Prüfe auf unendliche oder sehr große Brennweiten (zylindrische Linsen)
                        if f_sag is not None and (f_sag > 1e20 or f_sag == float('inf')):
                            f_sag = float('inf')  # Standardisiere auf unendlich
                        
                        if f_tan is not None and (f_tan > 1e20 or f_tan == float('inf')):
                            f_tan = float('inf')  # Standardisiere auf unendlich
                        
                        lens_entry = {
                            'name': name,
                            'focal_length': f_sag if f_sag is not None and f_sag != float('inf') else f_tan,  # Für Abwärtskompatibilität
                            'focal_length_sag': f_sag,
                            'focal_length_tan': f_tan,
                            'lens_type': lens_type,
                            'is_round': is_round,
                            'component_data': component  # Vollständige Komponentendaten
                        }
                        self.lens_library.append(lens_entry)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error loading lens library: {str(e)}")

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
            
            # Extrahiere Brennweiten für beide Ebenen
            f_sag, f_tan = self._get_lens_focal_lengths(lens)
            
            # Linseneffekt hinzufügen - berücksichtige unterschiedliche Brennweiten
            if f_sag is not None and f_sag != float('inf'):
                elements_sag.append((beam.matrices.lens, (f_sag,)))
            
            if f_tan is not None and f_tan != float('inf'):
                elements_tan.append((beam.matrices.lens, (f_tan,)))
            
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
        position_sag = self.distance - q_sag_final.real
        position_tan = self.distance - q_tan_final.real
        
        return waist_sag, waist_tan, position_sag, position_tan
    
    def _get_lens_focal_lengths(self, lens):
        """Extrahiere sagittale und tangentiale Brennweite einer Linse"""
        # Wenn bereits spezifische Brennweiten in der Linse gespeichert sind, verwende diese
        f_sag = lens.get('focal_length_sag')
        f_tan = lens.get('focal_length_tan')
        
        if f_sag is None or f_tan is None:
            # Alternativ schaue in den Komponentendaten nach
            component_data = lens.get('component_data', {})
            properties = component_data.get('properties', {})
            
            # Extrahiere Brennweiten aus den Eigenschaften
            if f_sag is None:
                f_sag = properties.get('Focal length sagittal', lens.get('focal_length'))
            
            if f_tan is None:
                f_tan = properties.get('Focal length tangential', lens.get('focal_length'))
            
            # Wenn immer noch nicht gefunden, verwende die generische Brennweite
            if f_sag is None and f_tan is None:
                f_default = lens.get('focal_length')
                f_sag = f_tan = f_default
        
        # Konvertiere in float wenn möglich
        try:
            f_sag = float(f_sag) if f_sag is not None else None
            f_tan = float(f_tan) if f_tan is not None else None
        except (ValueError, TypeError):
            f_sag = f_tan = lens.get('focal_length')
        
        # Prüfe auf unendliche oder sehr große Werte
        if f_sag is not None and (f_sag > 1e20 or f_sag == float('inf')):
            f_sag = float('inf')
        
        if f_tan is not None and (f_tan > 1e20 or f_tan == float('inf')):
            f_tan = float('inf')
        
        return f_sag, f_tan
    
    def fitness_function(self, individual):
        """Berechne Fitness für ein gegebenes Individuum"""
        # Berechne resultierende Strahlparameter
        waist_sag, waist_tan, position_sag, position_tan = self.calculate_beam_parameters(individual)
        
        # Berechne Abweichung von Zielparametern
        fitness_waist = abs(self.waist_goal_sag - waist_sag)/self.waist_goal_sag + abs(self.waist_goal_tan - waist_tan)/self.waist_goal_tan
        fitness_position = abs(self.distance + self.waist_position_goal_sag - position_sag)/(self.distance + self.waist_position_goal_sag)
        + abs(self.distance + self.waist_position_goal_tan - position_tan)/(self.distance + self.waist_position_goal_tan)
        
        # Gewichtung zwischen Strahlgröße und Position
        try:
            weight = self.ui.modematcher_calculation.weight_slider.value() / 100.0
        except AttributeError:
            # Fallback wenn UI nicht verfügbar
            weight = 0.5
            
        fitness = (1 - weight) * fitness_waist + weight * fitness_position
        
        return (fitness,)
    
    '''def optimize_lens_system(self, max_lenses):
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
            pop_size = 70
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
                ngen=50,        # Anzahl der Generationen
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
                                    f"Number of lenses: {len(best_individual)}\n"
                                    f"Lenses: {', '.join([lens[0] for lens in result['lenses']])}\n"
                                    f"Waist Sagittal: {waist_sag*1e6:.2f} um\n"
                                    f"Waist Tangential: {waist_tan*1e6:.2f} um\n"
                                    f"Position Sagittal: {position_sag*1e2:.2f} cm\n"
                                    f"Position Tangential: {position_tan*1e2:.2f} cm\n"
                                    f"Fitness: {best_individual.fitness.values[0]:.4f}")
            return result
            
        except Exception as e:
            QMessageBox.critical(None, "Optimization Error", f"Error during optimization: {str(e)}")
            return None'''
    
    def optimize_lens_system(self, max_lenses, num_runs=100):
        """Startet die Multi-Run-Optimierung in einem separaten Thread"""
        try:
            # Validierungen
            if not self.lens_library:
                QMessageBox.warning(None, "Warning", "No lenses in library. Please select lenses first.")
                return None
                
            if len(self.lens_library) < 1:
                QMessageBox.warning(None, "Warning", "Not enough lenses in library. Need at least 1 lens.")
                return None
            
            # Erstelle Thread und Worker-Objekt
            self.thread = QThread()
            self.worker = OptimizationWorker(self, max_lenses, num_runs)
            
            # Erstelle Fortschrittsdialog
            progress_dialog = QProgressDialog("Running multi-optimization...", "Cancel", 0, num_runs * 50)
            progress_dialog.setWindowTitle("Optimization Progress")
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            progress_dialog.setModal(True)
            
            # Verbinde Cancel-Button mit Abbruch-Funktion
            progress_dialog.canceled.connect(self.worker.stop)
            
            # Verschiebe Worker in Thread
            self.worker.moveToThread(self.thread)
            
            # Verbinde Signale und Slots
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._on_multi_optimization_finished)
            self.worker.error.connect(self._on_optimization_error)
            self.worker.progress.connect(progress_dialog.setValue)
            self.worker.finished.connect(progress_dialog.close)
            self.worker.error.connect(progress_dialog.close)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            
            # Starte Thread
            self.thread.start()
            
            # Zeige Fortschrittsdialog
            progress_dialog.exec_()
            
            # Wir geben kein Ergebnis zurück, da die Berechnung asynchron erfolgt
            # Das Ergebnis wird später über Signale übermittelt
            return None
            
        except Exception as e:
            QMessageBox.critical(None, "Optimization Error", f"Error setting up optimization: {str(e)}")
            return None
    
    def _on_multi_optimization_finished(self, result):
        """Wird aufgerufen, wenn die Multi-Run-Optimierung erfolgreich abgeschlossen wurde"""
        if not result:
            QMessageBox.warning(None, "Optimization Result", "No valid solution found in any run.")
            return
            
        # Extrahiere Ergebnisse für bessere Lesbarkeit
        waist_sag = result['waist_sag']
        waist_tan = result['waist_tan']
        position_sag = result['position_sag']
        position_tan = result['position_tan']
        fitness = result['fitness']
        lenses = result['lenses']
        run = result.get('run', 0)
        
        # Zeige Erfolgs-Nachricht
        print(None, "Multi-Run Optimization Complete", 
                             f"Optimization completed successfully.\n"
                             f"Best result found in run {run} of {self.worker.num_runs}.\n"
                             f"Number of lenses: {len(lenses)}\n"
                             f"Lenses: {', '.join([lens[0] for lens in lenses])}\n"
                             f"Waist Sagittal: {waist_sag*1e6:.2f} μm\n"
                             f"Waist Tangential: {waist_tan*1e6:.2f} μm\n"
                             f"Position Sagittal: {position_sag*1e2:.2f} cm\n"
                             f"Position Tangential: {position_tan*1e2:.2f} cm\n"
                             f"Fitness: {fitness:.4f}")
        
        # Speichere Ergebnis für spätere Verwendung
        self.last_optimization_result = result
    
    def _on_optimization_error(self, error_message):
        """Wird aufgerufen, wenn ein Fehler während der Optimierung auftritt"""
        QMessageBox.critical(None, "Optimization Error", error_message)