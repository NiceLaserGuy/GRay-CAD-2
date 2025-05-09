import json
import numpy as np
import config
from deap import base, creator, tools
from os import path
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from src_resonator.problem import Problem
from src_resonator.plot_setup import Plotter
from Problems.resonator_types import *

class Resonator(QObject):
    """
    Main class for resonator optimization using Particle Swarm Optimization (PSO).
    Handles mirror configurations and resonator calculations.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resonator_window = None
        self.resonator_type = None 
        self.ui_resonator = None
        self.mirror_curvatures = []
        self.plotter = Plotter()

        # Attributes to store optimization results
        self.l1 = None
        self.l2 = None
        self.l3 = None
        self.lc = None
        self.theta = None
        self.r1_sag = None
        self.r1_tan = None
        self.r2_sag = None
        self.r2_tan = None
        self.selected_class_name = None

    def open_resonator_window(self):
        """
        Creates and shows the resonator configuration window.
        Sets up the UI and connects the necessary signals.
        """
        # Create new window instance without parent
        self.resonator_window = QMainWindow()
        
        # Load the resonator UI
        self.ui_resonator = uic.loadUi(
            path.abspath(path.join(path.dirname(path.dirname(__file__)), 
            "assets/resonator_window.ui")), 
            self.resonator_window
        )
        
        # Configure and show the window
        self.resonator_window.setWindowTitle("Resonator Configuration")
        self.resonator_window.show()

        # Connect resonator instance to UI
        self.set_ui_resonator(self.ui_resonator)
        self.temp_file_path = config.get_temp_file_path()


        # Connect resonator window buttons
        self.ui_resonator.button_evaluate_resonator.clicked.connect(
            self.evaluate_resonator)
        self.ui_resonator.button_abort_resonator.clicked.connect(
            self.stop_optimization)

        self.ui_resonator.comboBox_problem_class.currentTextChanged.connect(
            self.config_ui)
        
        self.config_ui()
        
        
        self.ui_resonator.pushButton_plot_beamdiagram.clicked.connect(self.plotter.plot_beamdiagram)
        
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
            raise ValueError("Die Liste 'mirror_curvatures' ist leer.")
        
    def config_ui(self):
        self.selected_class_name = self.ui_resonator.comboBox_problem_class.currentText()

        if self.selected_class_name == "BowTie":
            self.ui_resonator.edit_lower_bound_l1.setDisabled(False)
            self.ui_resonator.edit_upper_bound_l1.setDisabled(False)
            self.ui_resonator.edit_lower_bound_l2.setDisabled(True)
            self.ui_resonator.edit_upper_bound_l2.setDisabled(True)
            self.ui_resonator.edit_lower_bound_l3.setDisabled(False)
            self.ui_resonator.edit_upper_bound_l3.setDisabled(False)
            self.ui_resonator.edit_lower_bound_theta.setDisabled(False)
            self.ui_resonator.edit_upper_bound_theta.setDisabled(False)
        elif self.selected_class_name == "FabryPerot":
            self.ui_resonator.edit_lower_bound_l1.setDisabled(False)
            self.ui_resonator.edit_upper_bound_l1.setDisabled(False)
            self.ui_resonator.edit_lower_bound_l2.setDisabled(True)
            self.ui_resonator.edit_upper_bound_l2.setDisabled(True)
            self.ui_resonator.edit_lower_bound_l3.setDisabled(True)
            self.ui_resonator.edit_upper_bound_l3.setDisabled(True)
            self.ui_resonator.edit_lower_bound_theta.setDisabled(True)
            self.ui_resonator.edit_upper_bound_theta.setDisabled(True)
        elif self.selected_class_name == "Rectangle":
            self.ui_resonator.edit_lower_bound_l1.setDisabled(False)
            self.ui_resonator.edit_upper_bound_l1.setDisabled(False)
            self.ui_resonator.edit_lower_bound_l2.setDisabled(False)
            self.ui_resonator.edit_upper_bound_l2.setDisabled(False)
            self.ui_resonator.edit_lower_bound_l3.setDisabled(True)
            self.ui_resonator.edit_upper_bound_l3.setDisabled(True)
            self.ui_resonator.edit_lower_bound_theta.setDisabled(True)
            self.ui_resonator.edit_upper_bound_theta.setDisabled(True)
        elif self.selected_class_name == "Triangle":
            self.ui_resonator.edit_lower_bound_l1.setDisabled(False)
            self.ui_resonator.edit_upper_bound_l1.setDisabled(False)
            self.ui_resonator.edit_lower_bound_l2.setDisabled(False)
            self.ui_resonator.edit_upper_bound_l2.setDisabled(False)
            self.ui_resonator.edit_lower_bound_l3.setDisabled(True)
            self.ui_resonator.edit_upper_bound_l3.setDisabled(True)
            self.ui_resonator.edit_lower_bound_theta.setDisabled(True)
            self.ui_resonator.edit_upper_bound_theta.setDisabled(True)
        config.set_temp_resonator_type(self.selected_class_name)

    def set_ui_resonator(self, ui_resonator):
        """Set the ui_resonator reference"""
        self.ui_resonator = ui_resonator

    def get_input(self):
        """
        Retrieves input parameters from the UI and converts them to meters.
        
        Returns:
            numpy.array: Array containing [target_sag, target_tan, nc, lc, n_prop, wavelength]
        """
        self.target_sag = float(self.ui_resonator.edit_target_waist_sag.text())*1e-3
        self.target_tan = float(self.ui_resonator.edit_target_waist_tan.text())*1e-3
        self.nc = float(self.ui_resonator.edit_crystal_refractive_index.text())
        self.lc = float(self.ui_resonator.edit_crystal_length.text())
        self.wavelength = float(self.ui_resonator.edit_wavelength.text())*1e-3
        self.n_prop = 1
        config.set_temp_light_field_parameters(self.wavelength, self.lc, self.nc)

        return np.array([self.target_sag, self.target_tan, self.nc, self.lc, self.n_prop, self.wavelength])
    
    def getbounds(self):
        """
        Gets geometric bounds from the UI for l1, l3, and theta parameters.
        Converts UI values to appropriate units (meters and radians).
        
        Returns:
            tuple: (l1_min, l1_max, l3_min, l3_max, theta_min, theta_max)
        """
        l1_min = float(self.ui_resonator.edit_lower_bound_l1.text())
        l1_max = float(self.ui_resonator.edit_upper_bound_l1.text())
        l2_min = float(self.ui_resonator.edit_lower_bound_l2.text())
        l2_max = float(self.ui_resonator.edit_upper_bound_l2.text())
        l3_min = float(self.ui_resonator.edit_lower_bound_l3.text())
        l3_max = float(self.ui_resonator.edit_upper_bound_l3.text())
        theta_min = np.deg2rad(float(self.ui_resonator.edit_lower_bound_theta.text())/2)
        theta_max = np.deg2rad(float(self.ui_resonator.edit_upper_bound_theta.text())/2)
    
        return l1_min, l1_max, l2_min, l2_max, l3_min, l3_max, theta_min, theta_max
    
    def get_optimization_parameters(self):
        """
        Retrieves optimization parameters from the UI.
        
        Returns:
            tuple: (population_number, generation_number, phi1, phi2, pmin, pmax, smin, smax)
        """
        num_runs = int(float(self.ui_resonator.edit_num_runs.text()))
        population_number = int(float(self.ui_resonator.edit_population_number.text()))
        generation_number = int(float(self.ui_resonator.edit_generation_number.text()))
        phi1 = float(self.ui_resonator.edit_phi1_float.text())
        phi2 = float(self.ui_resonator.edit_phi2_float.text())
        pmin = float(self.ui_resonator.edit_pmin.text())
        pmax = float(self.ui_resonator.edit_pmax.text())
        smin = float(self.ui_resonator.edit_smin.text())
        smax = float(self.ui_resonator.edit_smax.text())
        mutation_probability = float(self.ui_resonator.edit_mutation_probability.text())
        return num_runs, population_number, generation_number, phi1, phi2, pmin, pmax, smin, smax, mutation_probability

    def evaluate_resonator(self):
        """
        Starts the optimization process with multiple runs.
        """
        if self.temp_file_path is None or not path.exists(self.temp_file_path):
            QMessageBox.critical(
                self.resonator_window,
                "Error",
                "No temporary file found. Please add components and save them."
            )
            return

        # Get the number of runs from the UI
        try:
            num_runs = int(self.ui_resonator.edit_num_runs.text())
            if num_runs <= 0:
                raise ValueError("Number of runs must be greater than 0.")
        except ValueError:
            QMessageBox.critical(
                self.resonator_window,
                "Error",
                "Invalid number of runs. Please enter a positive integer."
            )
            return
        
        self.selected_class_name = self.ui_resonator.comboBox_problem_class.currentText()
        if self.selected_class_name == "BowTie":
            self.resonator_type = BowTie()
        elif self.selected_class_name == "FabryPerot":
            self.resonator_type = FabryPerot()
        elif self.selected_class_name == "Rectangle":
            self.resonator_type = Rectangle()
        elif self.selected_class_name == "Triangle":
            self.resonator_type = Triangle()
        else:
            self.resonator_type = None
        if self.selected_class_name is None:
            QMessageBox.critical(
                self.resonator_window,
                "Error",
                "No valid resonator type selected. Please select a valid resonator type."
            )
            return
                
        self.problem = Problem(self.resonator_type)

        # Verwende die temporäre Datei als Quelle
        selected_file_path = self.temp_file_path

        # Load mirror data from the selected file
        self.load_mirror_data(selected_file_path)

        if not self.mirror_curvatures:
            QMessageBox.critical(
                self.resonator_window,
                "Error",
                "The list 'mirror_curvatures' is empty. Please check the selected file."
            )
            return

        config.TEMP_FILE_PATH_LIB = self.temp_file_path

        # Get optimization parameters
        num_runs, population_number, generation_number, phi1, phi2, pmin, pmax, smin, smax, mutation_probability = self.get_optimization_parameters()

        inputs = self.get_input()
        self.target_sag, self.target_tan, self.nc, self.lc, self.n_prop, self.wavelength = inputs

        # DEAP setup for PSO with optimization parameters
        self.size = self.problem.problem_dimension()
        
        toolbox = base.Toolbox()
        toolbox.register("particle", self.generate, size=self.size, smin=smin, smax=smax)
        toolbox.register("population", tools.initRepeat, list, toolbox.particle)
        toolbox.register("update", self.update_particle, phi1=phi1, phi2=phi2, mutation_probability=mutation_probability)
        toolbox.register("evaluate", self.objective)

        # Create population with population_number
        population = toolbox.population(n=population_number)

        # Initialize optimization thread with multiple runs
        self.optimization_thread = OptimizationThread(
            self, population, toolbox, generation_number, num_runs
        )

        # Setup progress bar
        total_generations = num_runs * generation_number
        self.ui_resonator.progressBar_build_resonator.setMaximum(total_generations)
        self.ui_resonator.progressBar_build_resonator.setValue(0)

        # Connect signals and start thread
        self.optimization_thread.progress.connect(
            self.ui_resonator.progressBar_build_resonator.setValue
        )
        self.optimization_thread.finished.connect(self.optimization_finished)
        self.optimization_thread.start()

    def optimization_finished(self, best):
        # Entpacken der gespeicherten Input-Werte aus dem Thread
        thread = self.optimization_thread
        nc = thread.nc
        lc = thread.lc
        n_prop = thread.n_prop
        wavelength = thread.wavelength

        # Entpacken der Werte aus dem besten Partikel
        if self.selected_class_name == "BowTie":
            self.l1, self.l3, self.theta, mirror1, mirror2 = best
            self.l2 = ((2 * self.l1) + lc + self.l3) / (2 * np.cos(2*self.theta))
        elif self.selected_class_name == "FabryPerot":
            self.l1, mirror1 = best
            self.l2, self.l3, self.theta, mirror2 = 0, 0, 0
        elif self.selected_class_name == "Rectangle":
            self.l1, self.l2, mirror1, mirror2 = best
            self.l3, self.theta = 0, np.pi / 2
        elif self.selected_class_name == "Triangle":
            self.l1, self.l2, self.theta, mirror1, mirror2 = best
            self.l3 = 0

        # Berechnung der Krümmungswerte basierend auf den Indizes
        mirror1 = int(np.clip(mirror1, 0, len(self.mirror_curvatures) - 1))
        mirror2 = int(np.clip(mirror2, 0, len(self.mirror_curvatures) - 1))
        self.r1_sag, self.r1_tan = self.mirror_curvatures[mirror1][:2]
        self.r2_sag, self.r2_tan = self.mirror_curvatures[mirror2][:2]

        # Berechnung der Waist-Größen mit den gespeicherten Werten
        roundtrip_matrix_sag = self.problem.roundtrip_sagittal(nc, lc, n_prop, self.l1, self.l3, self.r1_sag, self.r2_sag, self.theta)
        roundtrip_matrix_tan = self.problem.roundtrip_tangential(nc, lc, n_prop, self.l1, self.l3, self.r1_tan, self.r2_tan, self.theta)
        m_sag = np.abs((roundtrip_matrix_sag[0, 0] + roundtrip_matrix_sag[1, 1])/2)
        m_tan = np.abs((roundtrip_matrix_tan[0, 0] + roundtrip_matrix_tan[1, 1])/2)
        b_sag = np.abs(roundtrip_matrix_sag[0, 1])
        b_tan = np.abs(roundtrip_matrix_tan[0, 1])
        self.waist_sag = np.sqrt(((b_sag * wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_sag**2)))))
        self.waist_tan = np.sqrt(((b_tan * wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_tan**2)))))

        r1_sag = "\u221e" if self.r1_sag >= 1e+15 else self.r1_sag
        r1_tan = "\u221e" if self.r1_tan >= 1e+15 else self.r1_tan
        r2_sag = "\u221e" if self.r2_sag >= 1e+15 else self.r2_sag
        r2_tan = "\u221e" if self.r2_tan >= 1e+15 else self.r2_tan        

        # Ausgabe der Ergebnisse
        if self.selected_class_name == "BowTie":
            config.set_temp_resonator_setup(self.waist_sag, self.waist_tan, self.l1, self.l2, self.l3, self.theta, self.r1_sag, self.r1_tan, self.r2_sag, self.r2_tan)
            self.ui_resonator.label_length1.setText(f"={self.l1:.3f} mm")
            self.ui_resonator.label_length2.setText(f"={(2*self.l1+lc+self.l3)/(2*np.cos(2*self.theta)):.3f} mm")
            self.ui_resonator.label_length3.setText(f"={self.l3:.3f} mm")
            self.ui_resonator.label_theta.setText(f"={np.rad2deg(2*self.theta):.3f} °")
            self.ui_resonator.label_mirror2.setText(f"={r2_sag} mm / {r2_tan} mm")
        elif self.selected_class_name == "FabryPerot":
            config.set_temp_resonator_setup(self.waist_sag, self.waist_tan, self.l1, self.r1_sag, self.r1_tan)
            self.ui_resonator.label_length1.setText(f"={self.l1:.3f} mm")
            self.ui_resonator.label_length2.setText(f"={self.l2:.3f} mm")
            self.ui_resonator.label_length3.setText(f"=0.0 mm")
            self.ui_resonator.label_theta.setText(f"=0.0 °")
            self.ui_resonator.label_mirror2.setText(f"=0 mm / 0 mm")
        elif self.selected_class_name == "Rectangle":
            config.set_temp_resonator_setup(self.waist_sag, self.waist_tan, self.l1, self.l2, self.r1_sag, self.r1_tan, self.r2_sag, self.r2_tan)
            self.ui_resonator.label_length1.setText(f"={self.l1:.3f} mm")
            self.ui_resonator.label_length2.setText(f"={self.l2:.3f} mm")
            self.ui_resonator.label_length3.setText(f"=0.0 mm")
            self.ui_resonator.label_theta.setText(f"=90 °")
            self.ui_resonator.label_mirror2.setText(f"={r2_sag} mm / {r2_tan} mm")
        elif self.selected_class_name == "Triangle":
            config.set_temp_resonator_setup(self.waist_sag, self.waist_tan, self.l1, self.l2, self.theta, self.r1_sag, self.r1_tan, self.r2_sag, self.r2_tan)
            self.ui_resonator.label_length1.setText(f"={self.l1:.3f} mm")
            self.ui_resonator.label_length2.setText(f"={self.l2:.3f} mm")
            self.ui_resonator.label_length3.setText(f"=0.0 mm")
            self.ui_resonator.label_theta.setText(f"={np.rad2deg(self.theta):.3f} °")
            self.ui_resonator.label_mirror2.setText(f"={r2_sag} mm / {r2_tan} mm")
        self.ui_resonator.label_mirror1.setText(f"={r1_sag} mm / {r1_tan} mm")
        self.ui_resonator.label_waist.setText(f"={self.waist_sag*1e3:.3f} µm / {self.waist_tan*1e3:.3f} µm")
        self.ui_resonator.label_fitness.setText(f"={best.fitness.values[0]:.3f}")
        self.ui_resonator.label_stability.setText(f"={m_sag:.3f} / {m_tan:.3f}")
        return best

    def stop_optimization(self):
        if hasattr(self, 'optimization_thread'):
            self.optimization_thread.stop()

    def objective(self, individual):
        """
        Fitness function for PSO optimization.
        Calculates resonator parameters and returns fitness value.
        
        Args:
            individual: Particle containing [l1, l3, theta, mirror1, mirror2]
        
        Returns:
            tuple: Single-element tuple containing the fitness value
        """
        if self.selected_class_name == "BowTie":
            # Extract individual parameters
            l1, l3, theta, mirror1, mirror2 = individual
        elif self.selected_class_name == "FabryPerot":
            l1, mirror1 = individual
            l3, theta, mirror2 = 0, 0, 0
        elif self.selected_class_name == "Rectangle":
            l1, l2, mirror1, mirror2 = individual
            l3, theta = 0, np.pi / 2
        elif self.selected_class_name == "Triangle":
            l1, l2, theta, mirror1, mirror2 = individual
            l3 = 0

        # Get mirror curvatures
        mirror1 = int(np.clip(mirror1, 0, len(self.mirror_curvatures) - 1))
        mirror2 = int(np.clip(mirror2, 0, len(self.mirror_curvatures) - 1))
        r1_sag, r1_tan = self.mirror_curvatures[mirror1][:2]
        r2_sag, r2_tan = self.mirror_curvatures[mirror2][:2]

        # Calculate roundtrip matrices
        if self.selected_class_name == "BowTie":
            roundtrip_matrix_sag = self.problem.roundtrip_sagittal(
                self.nc, self.lc, self.n_prop, l1, l3, r1_sag, r2_sag, theta
            )
            roundtrip_matrix_tan = self.problem.roundtrip_tangential(
                self.nc, self.lc, self.n_prop, l1, l3, r1_tan, r2_tan, theta
            )
        elif self.selected_class_name == "FabryPerot":
            roundtrip_matrix_sag = self.problem.roundtrip_sagittal(
                self.nc, self.lc, self.n_prop, l1, r1_sag
            )
            roundtrip_matrix_tan = self.problem.roundtrip_tangential(
                self.nc, self.lc, self.n_prop, l1, r1_tan
            )
        elif self.selected_class_name == "Rectangle":
            roundtrip_matrix_sag = self.problem.roundtrip_sagittal(
                self.nc, self.lc, self.n_prop, l1, l2, r1_sag, r2_sag
            )
            roundtrip_matrix_tan = self.problem.roundtrip_tangential(
                self.nc, self.lc, self.n_prop, l1, l2, r1_tan, r2_tan
            )
        elif self.selected_class_name == "Triangle":
            roundtrip_matrix_sag = self.problem.roundtrip_sagittal(
                self.nc, self.lc, self.n_prop, l1, l2, theta, r1_sag, r2_sag
            )
            roundtrip_matrix_tan = self.problem.roundtrip_tangential(
                self.nc, self.lc, self.n_prop, l1, l2, theta, r1_tan, r2_tan
            )

        # Extract matrix elements for stability calculation
        m_sag = np.abs((roundtrip_matrix_sag[0, 0] + roundtrip_matrix_sag[1, 1]) / 2)
        m_tan = np.abs((roundtrip_matrix_tan[0, 0] + roundtrip_matrix_tan[1, 1]) / 2)

        # Calculate beam parameters
        b_sag = np.abs(roundtrip_matrix_sag[0, 1])
        b_tan = np.abs(roundtrip_matrix_tan[0, 1])

        # Berechnung der Waist-Größen mit Sicherheitsprüfung
        if 1 - m_sag**2 <= 0:
            waist_sag = 1e6  # Bestrafe instabile Resonatoren
        else:
            waist_sag = np.sqrt(((b_sag * self.wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_sag**2)))))

        if 1 - m_tan**2 <= 0:
            waist_tan = 1e6  # Bestrafe instabile Resonatoren
        else:
            waist_tan = np.sqrt(((b_tan * self.wavelength) / (np.pi)) * (np.sqrt(np.abs(1 / (1 - m_tan**2)))))

        # Check for unstable resonators
        if abs(m_sag) > 1 or abs(m_tan) > 1:
            return 1e6,

        # Calculate fitness value using the Problem class
        fitness_value, = self.problem.fitness(waist_sag, waist_tan, self.target_sag, self.target_tan)

        return (fitness_value,)

    def generate(self, size, smin, smax):
        """
        Generates a new particle for PSO.

        Args:
            size (int): Number of parameters per particle
            smin (float): Minimum velocity value
            smax (float): Maximum velocity value

        Returns:
            Particle: New particle with random initial position and velocity
        """
        # Grenzen für l1, l3 und theta aus der UI
        l1_min, l1_max, l2_min, l2_max, l3_min, l3_max, theta_min, theta_max = self.getbounds()

        # Initialisiere Partikelpositionen und Geschwindigkeiten
        if self.selected_class_name == "BowTie":
            particle = creator.Particle([
                np.random.uniform(l1_min, l1_max) if i == 0 else
                np.random.uniform(l3_min, l3_max) if i == 1 else
                np.random.uniform(theta_min, theta_max) if i == 2 else
                np.random.randint(0, len(self.mirror_curvatures))
                for i in range(size)
            ])
        elif self.selected_class_name == "FabryPerot":
            particle = creator.Particle([
                np.random.uniform(l1_min, l1_max) if i == 0 else
                np.random.randint(0, len(self.mirror_curvatures))
                for i in range(size)
            ])
        elif self.selected_class_name == "Rectangle":
            particle = creator.Particle([
                np.random.uniform(l1_min, l1_max) if i == 0 else
                np.random.uniform(l2_min, l2_max) if i == 1 else
                np.random.randint(0, len(self.mirror_curvatures))
                for i in range(size)
            ])
        elif self.selected_class_name == "Triangle":
            particle = creator.Particle([
                np.random.uniform(l1_min, l1_max) if i == 0 else
                np.random.uniform(l2_min, l2_max) if i == 1 else
                np.random.uniform(theta_min, theta_max) if i == 2 else
                np.random.randint(0, len(self.mirror_curvatures))
                for i in range(size)
            ])
            
        particle.speed = [np.random.uniform(smin, smax) for _ in range(size)]
        particle.smin = smin
        particle.smax = smax
        return particle

    def update_particle(self, part, best, phi1, phi2, mutation_probability):
        """
        Updates particle position and velocity with optional mutation.
        
        Args:
            part: Particle to update
            best: Global best position
            phi1: Personal best weight
            phi2: Global best weight
            mutation_probability: Probability of mutation
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
        l1_min, l1_max, l2_min, l2_max, l3_min, l3_max, theta_min, theta_max = self.getbounds()
        if self.selected_class_name == "BowTie":
            part[:] = [
                np.clip(p + v, l1_min, l1_max) if i == 0 else
                np.clip(p + v, l3_min, l3_max) if i == 1 else
                np.clip(p + v, theta_min, theta_max) if i == 2 else
                int(np.clip(round(p + v), 0, len(self.mirror_curvatures) - 1))
                for i, (p, v) in enumerate(zip(part, part.speed))
            ]
        elif self.selected_class_name == "FabryPerot":
            part[:] = [
                np.clip(p + v, l1_min, l1_max) if i == 0 else
                int(np.clip(round(p + v), 0, len(self.mirror_curvatures) - 1))
                for i, (p, v) in enumerate(zip(part, part.speed))
            ]
        elif self.selected_class_name == "Rectangle":
            part[:] = [
                np.clip(p + v, l1_min, l1_max) if i == 0 else
                np.clip(p + v, l2_min, l2_max) if i == 1 else
                int(np.clip(round(p + v), 0, len(self.mirror_curvatures) - 1))
                for i, (p, v) in enumerate(zip(part, part.speed))
            ]
        elif self.selected_class_name == "Triangle":
            part[:] = [
                np.clip(p + v, l1_min, l1_max) if i == 0 else
                np.clip(p + v, l2_min, l2_max) if i == 1 else
                np.clip(p + v, theta_min, theta_max) if i == 2 else
                int(np.clip(round(p + v), 0, len(self.mirror_curvatures) - 1))
                for i, (p, v) in enumerate(zip(part, part.speed))
            ]

        # Mutation: Zufällige Änderung mit einer kleinen Wahrscheinlichkeit
        for i in range(len(part)):
            if np.random.rand() < mutation_probability:
                if self.selected_class_name == "BowTie":
                    if i == 0:  # l1
                        part[i] = np.random.uniform(l1_min, l1_max)
                    elif i == 1:  # l3
                        part[i] = np.random.uniform(l3_min, l3_max)
                    elif i == 2:  # theta
                        part[i] = np.random.uniform(theta_min, theta_max)
                    else:  # mirror indices
                        part[i] = np.random.randint(0, len(self.mirror_curvatures))
                elif self.selected_class_name == "FabryPerot":
                    if i == 0:  # l1
                        part[i] = np.random.uniform(l1_min, l1_max)
                    else:  # mirror index
                        part[i] = np.random.randint(0, len(self.mirror_curvatures))
                elif self.selected_class_name == "Rectangle":
                    if i == 0:  # l1
                        part[i] = np.random.uniform(l1_min, l1_max)
                    elif i == 1:  # l2
                        part[i] = np.random.uniform(l2_min, l2_max)
                    else:  # mirror index
                        part[i] = np.random.randint(0, len(self.mirror_curvatures))
                elif self.selected_class_name == "Triangle":
                    if i == 0:
                        part[i] = np.random.uniform(l1_min, l1_max)
                    elif i == 1:
                        part[i] = np.random.uniform(l2_min, l2_max)
                    elif i == 2:
                        part[i] = np.random.uniform(theta_min, theta_max)
                    else:  # mirror index
                        part[i] = np.random.randint(0, len(self.mirror_curvatures))


class OptimizationThread(QThread):
    progress = pyqtSignal(int)  # Signal für den Fortschritt
    finished = pyqtSignal(object)  # Signal für das beste Ergebnis

    def __init__(self, resonator, population, toolbox, generation_count, num_runs):
        super().__init__()
        self.resonator = resonator
        self.population = population
        self.toolbox = toolbox
        self.generation_count = generation_count
        self.num_runs = num_runs  # Anzahl der Läufe
        self.abort_flag = False
        self.best_overall = None  # Bestes Ergebnis über alle Läufe hinweg

        # Speichern der Input-Werte
        inputs = self.resonator.get_input()
        self.target_sag, self.target_tan, self.nc, self.lc, self.n_prop, self.wavelength = inputs

    def run(self):
        current_progress = 0

        for run in range(self.num_runs):
            if self.abort_flag:
                break

            # Initialisiere die Population für den aktuellen Lauf
            for part in self.population:
                part.fitness.values = (float('inf'),)  # Setze die Fitness auf einen hohen Wert
                part.best = None

            best = None  # Bestes Ergebnis für den aktuellen Lauf

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

                # Fortschritt melden
                current_progress += 1
                self.progress.emit(current_progress)

            # Vergleiche das beste Ergebnis des aktuellen Laufs mit dem besten Gesamt-Ergebnis
            if not self.best_overall or best.fitness.values[0] < self.best_overall.fitness.values[0]:
                self.best_overall = best

        # Signal mit dem besten Ergebnis aller Läufe senden
        self.finished.emit(self.best_overall)

    def stop(self):
        self.abort_flag = True