import json, tempfile
from os import path, listdir
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import QModelIndex, QObject
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from src_resonator.resonators import Resonator
import config

class ItemSelector(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.library_window = None
        self.ui_select_components_resonator = None
        self.components_data = []  # Store components data
        
        self.res = Resonator()
        
    def open_library_window(self):
        """
        Creates and shows the library window.
        Loads and displays mirror configurations.
        """
        # Create new window instance without parent
        self.lib_resonator_window = QMainWindow()
        
        
        # Load the library UI
        ui_path = path.abspath(path.join(path.dirname(path.dirname(__file__)), "assets/lib_resonator_window.ui"))
        self.ui_select_components_resonator = uic.loadUi(ui_path, 
            self.lib_resonator_window
        )
        
        # Configure and show the window
        self.lib_resonator_window.setWindowTitle("Select Components")
        self.lib_resonator_window.show()
        
        # Connect the next button to the method
        self.ui_select_components_resonator.button_next.clicked.connect(self.handle_next_button)

        # Connect the close button to the method
        self.ui_select_components_resonator.button_close.clicked.connect(self.close_library_window)

        # Load files from the Library folder and display them
        self.load_library_files()

        # Connect the listView_libraries to a click event
        self.ui_select_components_resonator.listView_libraries.clicked.connect(self.display_file_contents)
        
        # Connect the pushButton_add_all to the method
        self.ui_select_components_resonator.pushButton_add_all.clicked.connect(self.add_all_components_to_temporary_list)
        
        # Connect the pushButton_add to the method
        self.ui_select_components_resonator.toolButton_add_component.clicked.connect(self.add_component_to_temporary_list)
        
    def handle_next_button(self):
        """
        Speichert die temporäre Datei und öffnet das nächste Fenster.
        """
        # Temporäre Datei speichern
        self.save_temporary_file()

        # Nächstes Fenster öffnen
        self.res.open_resonator_window()
        
    def close_library_window(self):
        """
        Closes the library window.
        """
        if self.lib_resonator_window:
            self.ui_select_components_resonator.close()
     
    def load_library_files(self):
        """
        Loads files from the 'Library' folder and displays them in the listView_libraries.
        """
        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)), "Library"))

        # Check if the folder exists
        if not path.exists(library_path):
            QMessageBox.warning(
                self.library_window,
                "Library Folder Not Found",
                f"Library folder not found: {library_path}"
            )
            return

        # Get a list of files in the Library folder
        files = [f for f in listdir(library_path) if path.isfile(path.join(library_path, f))]

        # Create a model for the listView
        model = QStandardItemModel()

        # Add files to the model
        for file_name in files:
            item = QStandardItem(file_name)
            model.appendRow(item)

        # Set the model to the listView
        self.ui_select_components_resonator.listView_libraries.setModel(model)
               
    def display_file_contents(self, index: QModelIndex):
        """
        Displays the 'components' entries of the selected file in the listView_lib_components.
        Sets up the data for further interaction.
        """
        # Get the selected file name
        selected_file = index.data()

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)), "Library"))
        file_path = path.join(library_path, selected_file)

        # Check if the file exists
        if not path.exists(file_path):
            QMessageBox.warning(
                self.library_window,
                "File Not Found",
                f"File not found: {file_path}"
            )
            return

        # Read the contents of the file
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)  # Parse the JSON file
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error Reading File",
                f"An error occurred while reading the file: {e}"
            )
            return

        # Create a model for the listView_lib_components
        model = QStandardItemModel()

        # Extract and display the 'components' entries
        self.components_data = []  # Clear previous data
        if "components" in data and isinstance(data["components"], list):
            for component in data["components"]:
                # Check if the component has a 'name' attribute
                if "name" in component:
                    item = QStandardItem(component["name"])  # Add the 'name' of the component to the list
                    model.appendRow(item)
                    self.components_data.append(component)  # Store the full component data
                else:
                    QMessageBox.warning(
                        self.library_window,
                        "Component Missing Name",
                        f"Component without 'name' attribute found: {component}"
                    )
        else:
            QMessageBox.warning(
                self.library_window,
                "No Components Found",
                f"No 'components' list found in {selected_file}"
            )

        # Set the model to the listView_lib_components
        self.ui_select_components_resonator.listView_lib_components.setModel(model)

        # Connect the listView_lib_components to a click event
        self.ui_select_components_resonator.listView_lib_components.clicked.connect(self.display_component_details)
        
    def display_component_details(self, index: QModelIndex):
        """
        Displays the details of the selected component in the UI fields.
        """
        # Get the selected component index
        selected_index = index.row()

        # Retrieve the corresponding component data
        if 0 <= selected_index < len(self.components_data):
            component = self.components_data[selected_index]

            # Extract CURVATURE_TANGENTIAL and CURVATURE_SAGITTAL
            curvature_tangential = component.get("properties", {}).get("CURVATURE_TANGENTIAL", "N/A")
            curvature_sagittal = component.get("properties", {}).get("CURVATURE_SAGITTAL", "N/A")

            if component.get("properties", {}).get("IS_ROUND", 0.0) == 1.0:
                self.toggle_curvature_tangential(True)
                self.ui_select_components_resonator.radioButton_is_spherical.setChecked(True)
            else:
                self.toggle_curvature_tangential(False)
                self.ui_select_components_resonator.radioButton_is_spherical.setChecked(False)

            # Replace 1e30 with "Infinity"
            if curvature_tangential == 1e30:
                curvature_tangential = "Infinity"
            if curvature_sagittal == 1e30:
                curvature_sagittal = "Infinity"

            # Set the values in the UI fields
            self.ui_select_components_resonator.edit_curvature_tangential.setText(str(curvature_tangential))
            self.ui_select_components_resonator.edit_curvature_sagittal.setText(str(curvature_sagittal))

            # Extract and set the type in comboBox_type
            component_type = component.get("type", "N/A")
            index_in_combobox = self.ui_select_components_resonator.comboBox_type.findText(component_type)
            if index_in_combobox != -1:
                self.ui_select_components_resonator.comboBox_type.setCurrentIndex(index_in_combobox)
            else:
                QMessageBox.warning(
                    self.library_window,
                    "Unknown Component Type",
                    f"Unknown component type: {component_type}"
                )

            # Set the name and manufacturer in the UI fields
            self.ui_select_components_resonator.edit_name.setText(component.get("name", ""))
            self.ui_select_components_resonator.edit_manufacturer.setText(component.get("manufacturer", ""))
        else:
            QMessageBox.warning(
                self.library_window,
                "Invalid Component Index",
                f"Invalid component index: {selected_index}"
            )
            
    def toggle_curvature_tangential(self, checked):
        """
        Toggles the enabled state of the edit_curvature_tangential field
        based on the state of the radioButton_is_spherical.
        
        Args:
            checked (bool): True if the radio button is checked, False otherwise.
        """
        self.ui_select_components_resonator.edit_curvature_tangential.setEnabled(not checked)
        self.ui_select_components_resonator.label_6.setEnabled(not checked)
        if checked:
            # Set the value of edit_curvature_tangential to match edit_curvature_sagittal
            curvature_sagittal = self.ui_select_components_resonator.edit_curvature_sagittal.text().strip()
            self.ui_select_components_resonator.edit_curvature_tangential.setText(curvature_sagittal)
            self.ui_select_components_resonator.edit_curvature_tangential.setEnabled(False)  # Disable the field
        else:
            self.ui_select_components_resonator.edit_curvature_tangential.setEnabled(True)  # Enable the field

    def save_temporary_file(self):
        """
        Speichert die temporäre Liste in einer temporären Datei.
        Diese Methode wird beim Klicken auf button_next aufgerufen.
        """
        if not hasattr(self, "temporary_components") or not self.temporary_components:
            QMessageBox.warning(
                self.library_window,
                "No Components to Save",
                "Es gibt keine Komponenten, die gespeichert werden können."
            )
            return

        # Temporäre Datei erstellen
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
        self.temp_file_path = temp_file.name

        # Daten in die temporäre Datei schreiben
        try:
            # Speichern als Dictionary mit dem Schlüssel "components"
            json.dump({"components": self.temporary_components}, temp_file, indent=4)
            temp_file.close()
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error Saving File",
                f"Fehler beim Speichern der temporären Datei: {e}"
            )
            return

        # Setzen der globalen Variable
        config.set_temp_file_path(self.temp_file_path)
        
    def display_temporary_file(self, temp_file_path):
        """
        Zeigt die temporäre Datei in der listView_temporary_component an.
        """
        # Erstellen eines Modells für die listView
        model = QStandardItemModel()

        # Temporäre Datei zur Liste hinzufügen
        item = QStandardItem(temp_file_path)
        model.appendRow(item)

        # Modell in der listView setzen (Widget-Name anpassen, falls erforderlich)
        self.ui_select_components_resonator.listView_temporary_component.setModel(model)
        
    def add_component_to_temporary_list(self):
        """
        Fügt die ausgewählte Komponente von listView_lib_components zur temporären Liste hinzu
        und speichert sie in der temporären Datei.
        """
        # Überprüfen, ob eine Komponente ausgewählt ist
        selected_indexes = self.ui_select_components_resonator.listView_lib_components.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(
                self.library_window,
                "No Component Selected",
                "Bitte wählen Sie eine Komponente aus der Liste aus."
            )
            return

        # Hole die ausgewählte Komponente
        selected_index = selected_indexes[0].row()
        if 0 <= selected_index < len(self.components_data):
            selected_component = self.components_data[selected_index]
        else:
            QMessageBox.warning(
                self.library_window,
                "Invalid Selection",
                "Die ausgewählte Komponente ist ungültig."
            )
            return

        # Füge die Komponente zur temporären Liste hinzu
        if not hasattr(self, "temporary_components"):
            self.temporary_components = []  # Initialisiere die temporäre Liste
        self.temporary_components.append(selected_component)

        # Aktualisiere die temporäre Datei
        self.update_temporary_file()

        # Zeige die temporäre Liste in listView_temporary_component an
        self.update_temporary_list_view()

    def update_temporary_file(self):
        """
        Speichert die temporäre Liste in einer temporären Datei.
        """
        # Temporäre Datei erstellen
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
        self.temp_file_path = temp_file.name

        # Daten in die temporäre Datei schreiben
        try:
            json.dump({"components": self.temporary_components}, temp_file, indent=4)
            temp_file.close()
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error Saving File",
                f"Fehler beim Speichern der temporären Datei: {e}"
            )
            return

        # Setzen der globalen Variable
        config.TEMP_FILE_PATH = self.temp_file_path

    def update_temporary_list_view(self):
        """
        Zeigt die temporäre Liste in listView_temporary_component an.
        """
        if not hasattr(self, "temporary_components") or not self.temporary_components:
            return

        # Erstellen eines Modells für die listView
        model = QStandardItemModel()

        # Füge die Namen der Komponenten zur Liste hinzu
        for component in self.temporary_components:
            item_name = component.get("name", "Unbenannte Komponente")
            item = QStandardItem(item_name)
            model.appendRow(item)

        # Setze das Modell in listView_temporary_component
        self.ui_select_components_resonator.listView_temporary_component.setModel(model)

    def add_all_components_to_temporary_list(self):
        """
        Fügt alle Komponenten aus listView_lib_components zur temporären Liste hinzu
        und speichert sie in der temporären Datei.
        """
        if not self.components_data:
            QMessageBox.warning(
                self.library_window,
                "No Components Available",
                "Es gibt keine Komponenten, die hinzugefügt werden können."
            )
            return

        # Initialisiere die temporäre Liste, falls sie nicht existiert
        if not hasattr(self, "temporary_components"):
            self.temporary_components = []

        # Füge alle Komponenten aus components_data zur temporären Liste hinzu
        self.temporary_components.extend(self.components_data)

        # Entferne Duplikate (optional, falls erforderlich)
        self.temporary_components = list({comp["name"]: comp for comp in self.temporary_components}.values())

        # Aktualisiere die temporäre Datei
        self.update_temporary_file()

        # Zeige die temporäre Liste in listView_temporary_component an
        self.update_temporary_list_view()