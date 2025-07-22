from PyQt5.QtCore import QObject, QDir, QModelIndex
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QListView, QInputDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import QtWidgets
from os import path, listdir
from PyQt5 import uic
import json
import os
from src_physics.value_converter import ValueConverter

class Libraries(QObject):
    """
    Handles library functionality including window management
    and file operations for mirror configurations.
    """
    
    def __init__(self, parent=None):
        """Initialize the Libraries class with a parent object."""
        super().__init__(parent)
        self.library_window = None
        self.ui_library = None
        self.components_data = []  # Store components data
        self.value_converter = ValueConverter()

    def open_library_window(self):
        """
        Creates and shows the library window.
        Loads and displays mirror configurations.
        """
        # Create new window instance without parent
        self.library_window = QMainWindow()
        
        # Load the library UI
        self.ui_library = uic.loadUi(
            path.abspath(path.join(path.dirname(path.dirname(__file__)),
            "assets/library_window.ui")), 
            self.library_window
        )
        
        # Configure and show the window
        self.library_window.setWindowTitle("Library Editor")
        self.library_window.show()

        # Connect the accept_changes button to the method
        self.ui_library.button_accept_changes.clicked.connect(self.accept_changes)

        # Connect the close button to the method
        self.ui_library.button_close.clicked.connect(self.close_library_window)

        # Connect the add_lib button to the method
        self.ui_library.button_add_lib.clicked.connect(self.add_new_library)

        # Load files from the Library folder and display them
        self.load_library_files()

        # Connect the listView_libraries to a click event
        self.ui_library.listView_libraries.clicked.connect(self.display_file_contents)

        # Connect the add_component button to the method
        self.ui_library.button_add_component.clicked.connect(self.add_new_component)

        # Connect the delete_lib button to the method
        self.ui_library.button_delete_lib.clicked.connect(self.delete_library)

        # Connect the delete_component button to the method
        self.ui_library.button_delete_component.clicked.connect(self.delete_component)
        
        # NEU: Connect comboBox_type to show generic properties
        self.ui_library.comboBox_type.currentTextChanged.connect(self.on_component_type_changed)
        
        # NEU: Load generic components for initial display
        self.load_generic_components()

    def close_library_window(self):
        """
        Closes the library window.
        """
        if self.library_window:
            self.library_window.close()

    def load_library_files(self):
        """
        Loads files from the 'Library' folder and displays them in the listView_libraries,
        except 'Generic.json'.
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

        # Get a list of files in the Library folder, excluding 'Generic.json'
        files = [
            f for f in listdir(library_path)
            if path.isfile(path.join(library_path, f))
            and f.endswith(".json")
            and f != "Generic.json"
        ]

        # Create a model for the listView
        model = QStandardItemModel()

        # Add files to the model
        for file_name in files:
            item = QStandardItem(file_name)
            model.appendRow(item)

        # Set the model to the listView
        self.ui_library.listView_libraries.setModel(model)

    def display_file_contents(self, index: QModelIndex):
        """
        Displays the 'components' entries of the selected file in the listView_lib_components.
        Sets up the data for further interaction.
        """
        # Get the selected file name
        selected_file = index.data()

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)),  "Library"))
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
        self.ui_library.listView_lib_components.setModel(model)

        # Connect the listView_lib_components to a click event
        self.ui_library.listView_lib_components.clicked.connect(self.display_component_details)
    
    def add_new_library(self):
        """
        Creates a new .json file with user-provided name and adds it to the listView_libraries.
        """
        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)),  "Library"))

        # Prompt the user for a file name
        new_file_name, ok = QInputDialog.getText(
            self.library_window,
            "Create New Library File",
            "Enter the name for the new library file:"
        )

        # Check if the user pressed OK and entered a valid name
        if not ok or not new_file_name.strip():
            QMessageBox.warning(
                self.library_window,
                "Invalid Input",
                "The file name cannot be empty. Please try again."
            )
            return

        # Ensure the file name ends with .json
        if not new_file_name.endswith(".json"):
            new_file_name += ".json"

        # Full path to the new file
        new_file_path = path.join(library_path, new_file_name)

        # Check if the file already exists
        if path.exists(new_file_path):
            QMessageBox.warning(
                self.library_window,
                "File Already Exists",
                f"A file with the name '{new_file_name}' already exists. Please choose a different name."
            )
            return

        # Default content for the new file
        default_content = {
            "name": new_file_name.replace(".json", ""),
            "type": "LIBRARY",
            "components": []
        }

        # Create the new file
        try:
            with open(new_file_path, 'w') as file:
                json.dump(default_content, file, indent=4)
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error",
                f"An error occurred while creating the file: {e}"
            )
            return

        # Add the new file to the listView_libraries
        self.load_library_files()

        # Select the newly created file in the listView
        model = self.ui_library.listView_libraries.model()
        for row in range(model.rowCount()):
            if model.item(row).text() == new_file_name:
                self.ui_library.listView_libraries.setCurrentIndex(model.index(row, 0))
                break

        QMessageBox.information(
            self.library_window,
            "Success",
            f"New library file '{new_file_name}' created successfully."
        )

    def delete_library(self):
        """
        Deletes the currently selected library after user confirmation.
        """
        # Get the currently selected library file
        selected_file_index = self.ui_library.listView_libraries.currentIndex().row()
        model = self.ui_library.listView_libraries.model()

        if selected_file_index < 0:
            QMessageBox.warning(
                self.library_window,
                "No Selection",
                "Please select a library to delete."
            )
            return

        selected_file_name = model.item(selected_file_index).text()

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)),  "Library"))
        selected_file_path = path.join(library_path, selected_file_name)

        # Confirm deletion with the user
        reply = QMessageBox.question(
            self.library_window,
            "Confirm Deletion",
            f"Are you sure you want to delete the library '{selected_file_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Delete the file
                if path.exists(selected_file_path):
                    os.remove(selected_file_path)
                    self.load_library_files()
                    QMessageBox.information(
                        self.library_window,
                        "Success",
                        f"The library '{selected_file_name}' has been deleted."
                    )
                else:
                    QMessageBox.warning(
                        self.library_window,
                        "File Not Found",
                        f"The file '{selected_file_name}' does not exist."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self.library_window,
                    "Error",
                    f"An error occurred while deleting the file: {e}"
                )

    def add_new_component(self):
        """
        Adds a new component to the currently selected library.
        """
        # Get the currently selected library file
        selected_file_index = self.ui_library.listView_libraries.currentIndex().row()
        model = self.ui_library.listView_libraries.model()

        if selected_file_index < 0:
            QMessageBox.warning(
                self.library_window,
                "No Library Selected",
                "Please select a library to add a component to."
            )
            return

        selected_file_name = model.item(selected_file_index).text()

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)),  "Library"))
        selected_file_path = path.join(library_path, selected_file_name)

        # Read the current library file
        try:
            with open(selected_file_path, 'r') as file:
                library_data = json.load(file)
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error",
                f"An error occurred while reading the library file: {e}"
            )
            return

        # Get the selected type from comboBox_type
        selected_type = self.ui_library.comboBox_type.currentText()
        
        # Mapping von ComboBox-Text zu Component-Type
        type_mapping = {
            "Lens": "LENS",
            "Mirror": "MIRROR", 
            "Thick Lens": "THICK LENS",
            "ABCD": "ABCD"
        }
        
        component_type = type_mapping.get(selected_type)
        
        # Finde die entsprechende Generic-Komponente
        if not hasattr(self, 'generic_data'):
            self.load_generic_components()
    
        new_component = None
        for component in self.generic_data.get("components", []):
            if component.get("type") == component_type:
                # Deep copy der Generic-Komponente
                import copy
                new_component = copy.deepcopy(component)
                break
    
        if not new_component:
            QMessageBox.warning(
                self.library_window,
                "Component Template Not Found",
                f"No template found for component type: {selected_type}"
            )
            return

        # Add the new component to the library
        if "components" not in library_data:
            library_data["components"] = []
        library_data["components"].append(new_component)

        # Save the updated library file
        try:
            with open(selected_file_path, 'w') as file:
                json.dump(library_data, file, indent=4)
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error",
                f"An error occurred while saving the library file: {e}"
            )
            return

        # Update the listView_lib_components to display the new component
        self.display_file_contents(self.ui_library.listView_libraries.currentIndex())
    
    def delete_component(self):
        """
        Deletes the currently selected component from the selected library after user confirmation.
        """
        # Get the currently selected library file
        selected_file_index = self.ui_library.listView_libraries.currentIndex().row()
        model = self.ui_library.listView_libraries.model()

        if selected_file_index < 0:
            QMessageBox.warning(
                self.library_window,
                "No Library Selected",
                "Please select a library to delete a component from."
            )
            return

        selected_file_name = model.item(selected_file_index).text()

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)),  "Library"))
        selected_file_path = path.join(library_path, selected_file_name)

        # Read the current library file
        try:
            with open(selected_file_path, 'r') as file:
                library_data = json.load(file)
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error",
                f"An error occurred while reading the library file: {e}"
            )
            return

        # Get the currently selected component
        selected_component_index = self.ui_library.listView_lib_components.currentIndex().row()

        if selected_component_index < 0 or "components" not in library_data or selected_component_index >= len(library_data["components"]):
            QMessageBox.warning(
                self.library_window,
                "No Component Selected",
                "Please select a component to delete."
            )
            return

        selected_component = library_data["components"][selected_component_index]

        # Confirm deletion with the user
        reply = QMessageBox.question(
            self.library_window,
            "Confirm Deletion",
            f"Are you sure you want to delete the component '{selected_component.get('name', 'Unnamed')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Remove the component from the library
                del library_data["components"][selected_component_index]

                # Save the updated library file
                with open(selected_file_path, 'w') as file:
                    json.dump(library_data, file, indent=4)

                # Reload the components in the UI
                self.display_file_contents(self.ui_library.listView_libraries.currentIndex())

                QMessageBox.information(
                    self.library_window,
                    "Success",
                    f"The component '{selected_component.get('name', 'Unnamed')}' has been deleted."
                )
            except Exception as e:
                QMessageBox.critical(
                    self.library_window,
                    "Error",
                    f"An error occurred while deleting the component: {e}"
                )

    def show_component_properties(self, component_data=None):
        """
        Zeigt die Properties der ausgewählten Komponente im propertyLayout (GridLayout) an.
        """
        # PropertyLayout aus dem UI holen
        layout = self.ui_library.propertyLayout
        
        # Layout leeren
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Property-Felder Dictionary für Zugriff
        if not hasattr(self, '_property_fields'):
            self._property_fields = {}
        self._property_fields.clear()
        
        if not component_data:
            return
            
        # NEU: Komponententyp für Berechnungen speichern
        self._current_component_type = component_data.get("type", "").upper()
    
        properties = component_data.get("properties", {})
        component_type = component_data.get("type", "").upper()
        row = 0

        # NEU: Dynamisch Properties hinzufügen für Linsen (wie in graycad_mainwindow.py)
        if component_type == "LENS":
            if "Variable parameter" not in properties:
                properties["Variable parameter"] = "Edit focal length"
            if "Plan lens" not in properties:
                properties["Plan lens"] = False
            if "Lens material" not in properties:
                properties["Lens material"] = "NBK7"
            
            # Aktualisiere die Komponente mit den neuen Properties
            component_data["properties"] = properties

        # Definiere Paare für sagittal/tangential Properties
        paired_props = [
            ("Waist radius sagittal", "Waist radius tangential", "Waist radius"),
            ("Waist position sagittal", "Waist position tangential", "Waist position"),
            ("Rayleigh range sagittal", "Rayleigh range tangential", "Rayleigh range"),
            ("Focal length sagittal", "Focal length tangential", "Focal length"),
            ("Radius of curvature sagittal", "Radius of curvature tangential", "Radius of curvature"),
            ("Input radius of curvature sagittal", "Input radius of curvature tangential", "Input radius of curvature"),
            ("Output radius of curvature sagittal", "Output radius of curvature tangential", "Output radius of curvature"),
            ("A sagittal", "A tangential", "A"),
            ("B sagittal", "B tangential", "B"),
            ("C sagittal", "C tangential", "C"),
            ("D sagittal", "D tangential", "D")
        ]

        # Set zum schnellen Nachschlagen
        paired_keys = set()
        for sag, tan, _ in paired_props:
            paired_keys.add(sag)
            paired_keys.add(tan)

        # Zeige Paare in einer Zeile
        for sag_key, tan_key, display_name in paired_props:
            if sag_key in properties or tan_key in properties:
                label = QtWidgets.QLabel(display_name + ":")
                layout.addWidget(label, row, 0)
                
                # Sagittal
                if sag_key in properties:
                    value = properties.get(sag_key, "")
                    field_sag = QtWidgets.QLineEdit(self.value_converter.convert_to_nearest_string(value) if isinstance(value, (int, float)) else str(value))
                    layout.addWidget(field_sag, row, 1)
                    self._property_fields[sag_key] = field_sag
                    field_sag.textChanged.connect(self.on_property_changed)
                else:
                    layout.addWidget(QtWidgets.QLabel(""), row, 1)
                    
                # Tangential
                if tan_key in properties:
                    value = properties.get(tan_key, "")
                    field_tan = QtWidgets.QLineEdit(self.value_converter.convert_to_nearest_string(value) if isinstance(value, (int, float)) else str(value))
                    layout.addWidget(field_tan, row, 2)
                    self._property_fields[tan_key] = field_tan
                    field_tan.textChanged.connect(self.on_property_changed)
                else:
                    layout.addWidget(QtWidgets.QLabel(""), row, 2)
                    
                row += 1

        # Zeige alle anderen Properties einzeln
        for key, value in properties.items():
            if key in paired_keys:
                continue  # Schon als Paar behandelt
                
            # Spezielles Label für IS_ROUND
            if key == "IS_ROUND":
                label = QtWidgets.QLabel("Spherical:")
            else:
                label = QtWidgets.QLabel(key + ":")
            layout.addWidget(label, row, 0)
            
            # Checkbox für boolsche Werte und IS_ROUND
            if key == "IS_ROUND" or key == "Plan lens":
                field = QtWidgets.QCheckBox()
                field.setChecked(bool(value))
                layout.addWidget(field, row, 1)
                self._property_fields[key] = field
                field.stateChanged.connect(self.on_property_changed)
                
            # Dropdown für spezielle Felder
            elif key == "Lens material":
                field = QtWidgets.QComboBox()
                field.addItems(["NBK7", "Fused Silica"])
                if value in ["NBK7", "Fused Silica"]:
                    field.setCurrentText(value)
                layout.addWidget(field, row, 1)
                self._property_fields[key] = field
                field.currentIndexChanged.connect(self.on_property_changed)
                
            # NEU: Variable parameter Dropdown (wie in graycad_mainwindow.py)
            elif key == "Variable parameter":
                field = QtWidgets.QComboBox()
                field.addItems(["Edit both curvatures", "Edit focal length"])
                if value in ["Edit both curvatures", "Edit focal length"]:
                    field.setCurrentText(value)
                layout.addWidget(field, row, 1)
                self._property_fields[key] = field
                
                def on_variable_param_changed():
                    self.update_field_states()
                    
                field.currentIndexChanged.connect(on_variable_param_changed)
                
            # Standard: QLineEdit
            else:
                try:
                    field_value = self.value_converter.convert_to_nearest_string(value) if isinstance(value, (int, float)) else str(value)
                except:
                    field_value = str(value)
                field = QtWidgets.QLineEdit(field_value)
                layout.addWidget(field, row, 1)
                self._property_fields[key] = field
                field.textChanged.connect(self.on_property_changed)
                
            row += 1

        # Spacer am Ende
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        layout.addItem(spacer, row, 0, 1, 3)

        # IS_ROUND Synchronisierung einrichten
        if "IS_ROUND" in self._property_fields:
            self._property_fields["IS_ROUND"].stateChanged.connect(self.update_field_states)
            
        # NEU: Variable parameter Synchronisierung einrichten
        if "Variable parameter" in self._property_fields:
            self._property_fields["Variable parameter"].currentIndexChanged.connect(self.update_field_states)
            
        # Live-Synchronisierung für sagittal/tangential Paare
        for sag_key, tan_key, _ in paired_props:
            if sag_key in self._property_fields and tan_key in self._property_fields:
                field_sag = self._property_fields[sag_key]
                field_tan = self._property_fields[tan_key]
                
                def make_sync_function(field_sag, field_tan):
                    def sync_sagittal_to_tangential():
                        if "IS_ROUND" in self._property_fields:
                            is_round_field = self._property_fields["IS_ROUND"]
                            if isinstance(is_round_field, QtWidgets.QCheckBox) and is_round_field.isChecked():
                                field_tan.blockSignals(True)
                                field_tan.setText(field_sag.text())
                                field_tan.blockSignals(False)
                    return sync_sagittal_to_tangential
                
                if "Focal length" in sag_key or "Radius of curvature" in sag_key:
                    field_sag.textChanged.connect(self.on_property_changed)
                if "Focal length" in tan_key or "Radius of curvature" in tan_key:
                    field_tan.textChanged.connect(self.on_property_changed)
                
                field_sag.textChanged.connect(make_sync_function(field_sag, field_tan))
        
        # Initiale Feldstatus-Aktualisierung
        self.update_field_states()

    def update_field_states(self):
        """Aktualisiert Feldstatus basierend auf IS_ROUND und Variable parameter (wie in graycad_mainwindow.py)"""
        if not hasattr(self, '_property_fields'):
            return
        
        # Zustände ermitteln
        is_round = False
        edit_focal_length = True  # Default
        
        is_round_field = self._property_fields.get("IS_ROUND")
        if isinstance(is_round_field, QtWidgets.QCheckBox):
            is_round = is_round_field.isChecked()
            
        var_param_field = self._property_fields.get("Variable parameter")
        if isinstance(var_param_field, QtWidgets.QComboBox):
            edit_focal_length = var_param_field.currentText() == "Edit focal length"

        # Die zu prüfenden Feldgruppen
        focal_length_fields = ["Focal length sagittal", "Focal length tangential"]
        curvature_fields = [
            "Radius of curvature sagittal", "Radius of curvature tangential",
            "Input radius of curvature sagittal", "Input radius of curvature tangential",
            "Output radius of curvature sagittal", "Output radius of curvature tangential"
        ]
        
        # 1. Variable parameter Logik NUR anwenden wenn das Feld existiert (nur für LENS)
        has_variable_parameter = "Variable parameter" in self._property_fields
    
        if has_variable_parameter:
            # Felder nach Variable parameter setzen (nur für LENS)
            for key in focal_length_fields:
                field = self._property_fields.get(key)
                if field:
                    if edit_focal_length:
                        field.setReadOnly(False)
                        field.setStyleSheet("")
                    else:
                        field.setReadOnly(True)
                        field.setStyleSheet("background-color: #eee; color: #888;")

            for key in curvature_fields:
                field = self._property_fields.get(key)
                if field:
                    if edit_focal_length:
                        field.setReadOnly(True)
                        field.setStyleSheet("background-color: #eee; color: #888;")
                    else:
                        field.setReadOnly(False)
                        field.setStyleSheet("")

        # ERWEITERTE Liste aller sagittal/tangential Paare
        paired_props = [
            ("Waist radius sagittal", "Waist radius tangential"),
            ("Waist position sagittal", "Waist position tangential"),
            ("Rayleigh range sagittal", "Rayleigh range tangential"),
            ("Focal length sagittal", "Focal length tangential"),
            ("Radius of curvature sagittal", "Radius of curvature tangential"),
            ("Input radius of curvature sagittal", "Input radius of curvature tangential"),
            ("Output radius of curvature sagittal", "Output radius of curvature tangential"),
            # NEU: ABCD Matrix Paare
            ("A sagittal", "A tangential"),
            ("B sagittal", "B tangential"), 
            ("C sagittal", "C tangential"),
            ("D sagittal", "D tangential"),
        ]
        
        # 2. IS_ROUND-Logik anwenden
        for sag_key, tan_key in paired_props:
            if sag_key in self._property_fields and tan_key in self._property_fields:
                field_sag = self._property_fields[sag_key]
                field_tan = self._property_fields[tan_key]
                
                if is_round:
                    # Tangential-Feld sperren bei IS_ROUND=True
                    field_tan.setReadOnly(True)
                    field_tan.setStyleSheet("background-color: #eee; color: #888;")
                    
                    # Wert synchronisieren
                    if field_tan.text() != field_sag.text():
                        field_tan.blockSignals(True)
                        field_tan.setText(field_sag.text())
                        field_tan.blockSignals(False)
                else:
                    # Tangential-Feld entsperren bei IS_ROUND=False
                    if has_variable_parameter:
                        # Respektiere Variable parameter für Lens-Felder
                        if tan_key in focal_length_fields:
                            if edit_focal_length:
                                field_tan.setReadOnly(False)
                                field_tan.setStyleSheet("")
                            # else: bleibt gesperrt durch Variable parameter
                        elif tan_key in curvature_fields:
                            if not edit_focal_length:
                                field_tan.setReadOnly(False)
                                field_tan.setStyleSheet("")
                            # else: bleibt gesperrt durch Variable parameter
                        else:
                            # Für alle anderen Felder
                            field_tan.setReadOnly(False)
                            field_tan.setStyleSheet("")
                    else:
                        # Für Komponenten OHNE Variable parameter (Mirror, ABCD, etc.)
                        field_tan.setReadOnly(False)
                        field_tan.setStyleSheet("")

    def on_property_changed(self):
        """Callback für Property-Änderungen mit Berechnung der abhängigen Werte"""
        if not hasattr(self, '_property_fields'):
            return
        
        # Prüfe ob es sich um eine Linse handelt
        if not hasattr(self, '_current_component_type') or self._current_component_type != "LENS":
            self.update_field_states()
            return
        
        # Hole die aktuellen Werte
        try:
            # Material und Wellenlängen
            material = self._property_fields.get("Lens material", {}).currentText() if "Lens material" in self._property_fields else "NBK7"
            lambda_design = self.value_converter.convert_to_float(self._property_fields.get("Design wavelength", {}).text()) if "Design wavelength" in self._property_fields else 514e-9
            
            # Material-Brechungsindizes (vereinfacht)
            if material == "NBK7":
                n_design = 1.5168
                n = 1.5168  # Vereinfacht: gleiche Wellenlänge
            else:  # Fused Silica
                n_design = 1.4607
                n = 1.4607
                
            is_plane = self._property_fields.get("Plan lens", {}).isChecked() if "Plan lens" in self._property_fields else False
            var_param = self._property_fields.get("Variable parameter", {}).currentText() if "Variable parameter" in self._property_fields else "Edit focal length"
            
            # Für beide Modi (sagittal und tangential)
            for mode in ["sagittal", "tangential"]:
                f_key = f"Focal length {mode}"
                r_key = f"Radius of curvature {mode}"
                
                if f_key not in self._property_fields or r_key not in self._property_fields:
                    continue
                    
                f_field = self._property_fields[f_key]
                r_field = self._property_fields[r_key]
                
                # Nur berechnen wenn das Feld nicht readonly ist
                if var_param == "Edit both curvatures" and not r_field.isReadOnly():
                    # Von Krümmungsradius zu Brennweite
                    try:
                        r_in = self.value_converter.convert_to_float(r_field.text())
                        if is_plane:
                            r_out = 1e100
                        else:
                            r_out = -r_in
                        
                        # Formeln aus graycad_mainwindow.py Zeile 833
                        f_design_calculated = ((n_design-1) * ((1/r_in) - (1/r_out)))**(-1)
                        
                        # Aktualisiere Brennweite
                        f_field.blockSignals(True)
                        f_field.setText(self.value_converter.convert_to_nearest_string(f_design_calculated))
                        f_field.blockSignals(False)
                        
                    except Exception:
                        pass
                        
                elif var_param == "Edit focal length" and not f_field.isReadOnly():
                    # Von Brennweite zu Krümmungsradius
                    try:
                        f_design = self.value_converter.convert_to_float(f_field.text())
                        
                        # Formeln aus graycad_mainwindow.py Zeile 847
                        if is_plane:
                            r_in_calculated = ((n_design - 1)**2)/(n - 1) * f_design
                        else:
                            r_in_calculated = 2*((n_design - 1)**2)/(n - 1) * f_design
                        
                        # Aktualisiere Krümmungsradius
                        r_field.blockSignals(True)
                        r_field.setText(self.value_converter.convert_to_nearest_string(r_in_calculated))
                        r_field.blockSignals(False)
                        
                    except Exception:
                        pass
            
        except Exception:
            pass
        
        # Normale Feldstatus-Aktualisierung
        self.update_field_states()
    
    def display_component_details(self, index: QModelIndex):
        """
        Displays the details of the selected component in the propertyLayout.
        """
        # Get the selected component index
        selected_index = index.row()

        # Retrieve the corresponding component data
        if 0 <= selected_index < len(self.components_data):
            component = self.components_data[selected_index]
            
            # Zeige Properties im Grid-Layout an
            self.show_component_properties(component)
            
        else:
            QMessageBox.warning(
                self.library_window,
                "Invalid Component Index",
                f"Invalid component index: {selected_index}"
            )

    def accept_changes(self):
        """
        Speichert die Änderungen der Properties zurück in die JSON-Datei
        """
        if not hasattr(self, '_property_fields') or not self._property_fields:
            return
            
        # Get the currently selected library file
        selected_file_index = self.ui_library.listView_libraries.currentIndex().row()
        model = self.ui_library.listView_libraries.model()

        if selected_file_index < 0:
            QMessageBox.warning(
                self.library_window,
                "No Library Selected",
                "Please select a library."
            )
            return

        selected_file_name = model.item(selected_file_index).text()

        # Get selected component
        selected_component_index = self.ui_library.listView_lib_components.currentIndex().row()
        
        if selected_component_index < 0:
            QMessageBox.warning(
                self.library_window,
                "No Component Selected",
                "Please select a component."
            )
            return

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(path.dirname(__file__)),  "Library"))
        selected_file_path = path.join(library_path, selected_file_name)

        # Read the current library file
        try:
            with open(selected_file_path, 'r') as file:
                library_data = json.load(file)
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error",
                f"An error occurred while reading the library file: {e}"
            )
            return

        # Update component properties from UI fields
        component = library_data["components"][selected_component_index]
        
        for key, field in self._property_fields.items():
            if isinstance(field, QtWidgets.QCheckBox):
                component["properties"][key] = field.isChecked()
            elif isinstance(field, QtWidgets.QComboBox):
                component["properties"][key] = field.currentText()
            elif isinstance(field, QtWidgets.QLineEdit):
                try:
                    # Versuche als float zu konvertieren
                    value = self.value_converter.convert_to_float(field.text())
                    component["properties"][key] = value
                except:
                    # Falls das fehlschlägt, als String speichern
                    component["properties"][key] = field.text()

        # Save the updated library file
        try:
            with open(selected_file_path, 'w') as file:
                json.dump(library_data, file, indent=4)
                
            QMessageBox.information(
                self.library_window,
                "Success",
                "Changes saved successfully."
            )
            
            # Reload the components to reflect changes
            self.display_file_contents(self.ui_library.listView_libraries.currentIndex())
            
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error",
                f"An error occurred while saving the library file: {e}"
            )

    def load_generic_components(self):
        """
        Lädt die Generic.json Komponenten für die Typ-Auswahl
        """
        # Path to Generic.json
        generic_path = path.abspath(path.join(path.dirname(path.dirname(__file__)), "Library", "Generic.json"))
        
        if not path.exists(generic_path):
            QMessageBox.warning(
                self.library_window,
                "Generic File Not Found",
                f"Generic.json not found: {generic_path}"
            )
            return
        
        try:
            with open(generic_path, 'r') as file:
                self.generic_data = json.load(file)
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error Reading Generic File",
                f"An error occurred while reading Generic.json: {e}"
            )
            self.generic_data = {"components": []}

    def on_component_type_changed(self, selected_type):
        """
        Wird aufgerufen wenn sich die Auswahl in comboBox_type ändert.
        Zeigt die entsprechenden Properties aus Generic.json an.
        """
        if not hasattr(self, 'generic_data'):
            self.load_generic_components()
        
        # Mapping von ComboBox-Text zu Component-Type
        type_mapping = {
            "Lens": "LENS",
            "Mirror": "MIRROR", 
            "Thick Lens": "THICK LENS",
            "ABCD": "ABCD"
        }
        
        component_type = type_mapping.get(selected_type)
        if not component_type:
            return
        
        # Finde die entsprechende Komponente in Generic.json
        generic_component = None
        for component in self.generic_data.get("components", []):
            if component.get("type") == component_type:
                generic_component = component
                break
        
        if generic_component:
            # Zeige die Properties der Generic-Komponente an
            self.show_component_properties(generic_component)
        else:
            QMessageBox.warning(
                self.library_window,
                "Component Not Found",
                f"No generic component found for type: {selected_type}"
            )

