import numpy as np
from deap import base, creator, tools, algorithms
from scipy.optimize import minimize
import random
import json
import config
from PyQt5.QtWidgets import QMessageBox, QProgressDialog, QApplication, QTableWidgetItem
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, Qt
from src_physics.value_converter import ValueConverter

class NumericTableWidgetItem(QTableWidgetItem):
    """QTableWidgetItem-Subklasse für korrekte numerische Sortierung"""
    def __init__(self, text, value):
        super().__init__(text)
        self.setData(Qt.UserRole, float(value))
        
    def __lt__(self, other):
        # Vergleich basierend auf dem tatsächlichen numerischen Wert
        return self.data(Qt.UserRole) < other.data(Qt.UserRole)

class OptimizationWorker(QObject):
    """Worker-Klasse für die Durchführung der Optimierung in einem separaten Thread"""
    finished = pyqtSignal(object)  # Signal mit Optimierungsergebnis
    error = pyqtSignal(str)      # Signal für Fehler
    progress = pyqtSignal(int)   # Signal für Fortschrittsanzeige (nur aktueller Wert)
    
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
        results = []
        best_result = None
        best_fitness = float('inf')
        total_generations = 25

        self.optimizer.max_lenses = max_lenses
        self.optimizer.problem()

        for run in range(num_runs):
            if self.abort_flag:
                break

            self.progress.emit(run * total_generations)
            pop_size = 70
            population = self.optimizer.toolbox.population(n=pop_size)
            stats = tools.Statistics(lambda ind: ind.fitness.values)
            stats.register("avg", np.mean)
            stats.register("min", np.min)
            stats.register("max", np.max)
            hof = tools.HallOfFame(1)

            for gen in range(total_generations):
                if self.abort_flag:
                    break
                population = algorithms.varAnd(population, self.optimizer.toolbox, 0.5, 0.2)
                fits = self.optimizer.toolbox.map(self.optimizer.toolbox.evaluate, population)
                for fit, ind in zip(fits, population):
                    ind.fitness.values = fit
                population = self.optimizer.toolbox.select(population, len(population))
                hof.update(population)
                self.progress.emit(run * total_generations + gen + 1)

            if not self.abort_flag and hof:
                best_individual = hof[0]
                try:
                    optimized_individual = self.optimizer._local_optimize(best_individual)
                    if self.optimizer.fitness_function(optimized_individual)[0] < self.optimizer.fitness_function(best_individual)[0]:
                        best_individual = optimized_individual
                except Exception as e:
                    print(f"Lokale Optimierung fehlgeschlagen: {str(e)}")

                current_fitness = best_individual.fitness.values[0]
                waist_sag, waist_tan, position_sag, position_tan = self.optimizer.calculate_beam_parameters(best_individual)

                result = {
                    'lenses': [(lens['name'], lens['focal_length'], pos) for lens, pos in best_individual],
                    'waist_sag': waist_sag,
                    'waist_tan': waist_tan,
                    'position_sag': position_sag,
                    'position_tan': position_tan,
                    'fitness': current_fitness,
                    'run': run + 1
                }
                results.append(result)

                if current_fitness < best_fitness:
                    best_result = result
                    best_fitness = current_fitness

        return results  # <--- Jetzt wird eine Liste zurückgegeben!
    
    def stop(self):
        """Bricht die Optimierung ab"""
        self.abort_flag = True

class LensSystemOptimizer:
    def __init__(self, matrices):
        self.matrices = matrices
        self.lens_library = []  # Wird dynamisch geladen
        self.vc = ValueConverter()
        
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
        rel_waist_error_sag = ((self.waist_goal_sag - waist_sag)/self.waist_goal_sag)**2
        rel_waist_error_tan = ((self.waist_goal_tan - waist_tan)/self.waist_goal_tan)**2
        fitness_waist = rel_waist_error_sag + rel_waist_error_tan
        
        # Normalisierte Positionsabweichung
        target_pos_sag = self.distance + self.waist_position_goal_sag
        target_pos_tan = self.distance + self.waist_position_goal_tan
        
        rel_pos_error_sag = ((target_pos_sag - position_sag)/target_pos_sag)**2
        rel_pos_error_tan = ((target_pos_tan - position_tan)/target_pos_tan)**2
        fitness_position = rel_pos_error_sag + rel_pos_error_tan
        
        # Gewichtung zwischen Strahlgröße und Position
        try:
            weight = self.ui.modematcher_calculation.weight_slider.value() / 100.0
        except AttributeError:
            # Fallback wenn UI nicht verfügbar
            weight = 0.5
            
        fitness = (1 - weight) * fitness_waist + weight * fitness_position
        
        return (fitness,)
    
    def optimize_lens_system(self, max_lenses, num_runs=50):
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
            
            # UI-Elemente aktualisieren
            ui_found = False
            
            # Suche progressBar in der UI
            for attr_name in ['ui', 'modematcher_calculation', 'ui_modematcher_calculation']:
                if hasattr(self, attr_name):
                    ui_obj = getattr(self, attr_name)
                    if hasattr(ui_obj, 'progressBar'):
                        # Setze progressBar in der UI
                        total_steps = num_runs * 25
                        ui_obj.progressBar.setMinimum(0)
                        ui_obj.progressBar.setMaximum(total_steps)
                        ui_obj.progressBar.setValue(0)
                        
                        # Verbinde Worker-Fortschritt mit progressBar
                        self.worker.progress.connect(ui_obj.progressBar.setValue)
                        
                        # Deaktiviere Optimize-Button falls vorhanden
                        if hasattr(ui_obj, 'button_optimize'):
                            ui_obj.button_optimize.setEnabled(False)
                        
                        ui_found = True
                        break
            
            # Fallback zu QProgressDialog wenn keine UI-ProgressBar gefunden wurde
            if not ui_found:
                progress_dialog = QProgressDialog("Running multi-optimization...", "Cancel", 0, num_runs * 50)
                progress_dialog.setWindowTitle("Optimization Progress")
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setValue(0)
                progress_dialog.setModal(True)
                
                # Verbinde Cancel-Button mit Abbruch-Funktion
                progress_dialog.canceled.connect(self.worker.stop)
                
                # Verbinde Worker-Fortschritt mit progressDialog
                self.worker.progress.connect(progress_dialog.setValue)
                self.worker.finished.connect(progress_dialog.close)
                self.worker.error.connect(progress_dialog.close)
        
            # Verschiebe Worker in Thread
            self.worker.moveToThread(self.thread)
            
            # Verbinde Signale und Slots
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._on_multi_optimization_finished)
            self.worker.error.connect(self._on_optimization_error)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self._reset_ui)
            
            # Starte Thread
            self.thread.start()
            
            # Zeige Fortschrittsdialog falls nötig
            if not ui_found:
                progress_dialog.exec_()
            
            # Wir geben kein Ergebnis zurück, da die Berechnung asynchron erfolgt
            return None
            
        except Exception as e:
            QMessageBox.critical(None, "Optimization Error", f"Error setting up optimization: {str(e)}")
            return None

    def _reset_ui(self):
        """Setzt UI-Elemente nach der Optimierung zurück"""
        # Suche UI-Objekt mit progressBar
        for attr_name in ['ui', 'modematcher_calculation', 'ui_modematcher_calculation']:
            if hasattr(self, attr_name):
                ui_obj = getattr(self, attr_name)
                if hasattr(ui_obj, 'progressBar'):
                    # Setze progressBar zurück
                    ui_obj.progressBar.setValue(0)
                    
                    # Aktiviere Optimize-Button falls vorhanden
                    if hasattr(ui_obj, 'button_optimize'):
                        ui_obj.button_optimize.setEnabled(True)
                    
                    break
    
    def _on_multi_optimization_finished(self, results):
        """
        Befüllt das QTableWidget tableResults mit allen Optimierungsergebnissen.
        Jeder Eintrag in results ist ein Dictionary mit den Keys:
        'fitness', 'waist_sag', 'position_sag', 'run'
        """
        if not results:
            QMessageBox.warning(None, "Optimization Result", "No valid solution found in any run.")
            return

        # Zielwerte aus den geladenen Parametern
        w0_sag_goal = self.waist_goal_sag
        z0_sag_goal = self.distance + self.waist_position_goal_sag

        # UI finden
        ui = None
        for attr_name in ['ui', 'modematcher_calculation', 'ui_modematcher_calculation']:
            if hasattr(self, attr_name):
                ui = getattr(self, attr_name)
                break

        if ui and hasattr(ui, 'tableResults'):
            table = ui.tableResults
            table.setRowCount(len(results))
            for row, result in enumerate(results):
                waist_sag = result['waist_sag']
                position_sag = result['position_sag']
                fitness = result['fitness']
                delta_w0_sag = waist_sag - w0_sag_goal
                delta_z0_sag = position_sag - z0_sag_goal

                # Fitness mit numerischem Wert für Sortierung
                item_fitness = NumericTableWidgetItem(f"{fitness:.3e}", fitness)
                
                # Waist mit NumericTableWidgetItem
                item_waist = NumericTableWidgetItem(f"{self.vc.convert_to_nearest_string(waist_sag)}", waist_sag)
                
                # Delta Waist mit NumericTableWidgetItem
                item_delta_waist = NumericTableWidgetItem(f"{self.vc.convert_to_nearest_string(delta_w0_sag)}", delta_w0_sag)
                
                # Position mit NumericTableWidgetItem
                item_position = NumericTableWidgetItem(f"{self.vc.convert_to_nearest_string(position_sag)}", position_sag)
                
                # Delta Position mit NumericTableWidgetItem
                item_delta_position = NumericTableWidgetItem(f"{self.vc.convert_to_nearest_string(delta_z0_sag)}", delta_z0_sag)
                
                # Setze Items in Tabelle
                table.setItem(row, 0, item_fitness)
                table.setItem(row, 1, item_waist)
                table.setItem(row, 2, item_delta_waist)
                table.setItem(row, 3, item_position)
                table.setItem(row, 4, item_delta_position)

            # Aktiviere Sortierung für die Tabelle
            table.setSortingEnabled(True)
            
            # Sortiere nach Fitness (Spalte 0)
            table.sortItems(0, Qt.AscendingOrder)

        # Speichere alle Ergebnisse für spätere Verwendung
        self.last_optimization_results = results
    
    def _on_optimization_error(self, error_message):
        """Wird aufgerufen, wenn ein Fehler während der Optimierung auftritt"""
        QMessageBox.critical(None, "Optimization Error", error_message)
    
    def _local_optimize(self, best_individual):
        """Führt eine lokale Optimierung der Linsenpositionen durch"""
        # Extrahiere nur die Positionen für die Optimierung
        initial_positions = np.array([pos for _, pos in best_individual])
        
        # Definiere Grenzen (0 bis self.distance)
        bounds = [(0, self.distance) for _ in range(len(initial_positions))]
        
        # Fitness-Funktion für lokale Optimierung
        def position_fitness(positions):
            # Erstelle neues Individuum mit optimierten Positionen
            new_individual = [(lens, pos) for (lens, _), pos in zip(best_individual, positions)]
            # Sortiere nach Position
            new_individual.sort(key=lambda x: x[1])
            # Berechne Fitness
            return self.fitness_function(new_individual)[0]
        
        # Führe lokale Optimierung durch
        result = minimize(
            position_fitness,
            initial_positions,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 100, 'disp': False}
        )
        
        # Erstelle optimiertes Individuum als neue Liste
        optimized_list = [(lens, pos) for (lens, _), pos in zip(best_individual, result.x)]
        # Sortiere nach Position
        optimized_list.sort(key=lambda x: x[1])
        
        # Konvertiere zu einem DEAP Individual-Objekt
        optimized_individual = creator.Individual(optimized_list)
        
        # Berechne und setze Fitness
        fitness_value = self.fitness_function(optimized_individual)
        optimized_individual.fitness.values = fitness_value
        
        return optimized_individual