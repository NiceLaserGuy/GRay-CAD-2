from PyQt5.QtCore import QObject, QDir, QModelIndex
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QListView, QInputDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from os import path, listdir
from PyQt5 import uic
import json
import os

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

    def open_library_window(self):
        """
        Creates and shows the library window.
        Loads and displays mirror configurations.
        """
        # Create new window instance without parent
        self.library_window = QMainWindow()
        
        # Load the library UI
        self.ui_library = uic.loadUi(
            path.abspath(path.join(path.dirname(__file__), 
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

        # Connect the is_round checkbox to the method
        self.ui_library.radioButton_is_spherical.toggled.connect(self.toggle_curvature_tangential)
    
    def toggle_curvature_tangential(self, checked):
        """
        Toggles the enabled state of the edit_curvature_tangential field
        based on the state of the radioButton_is_spherical.
        
        Args:
            checked (bool): True if the radio button is checked, False otherwise.
        """
        self.ui_library.edit_curvature_tangential.setEnabled(not checked)
        self.ui_library.label_6.setEnabled(not checked)
        if checked:
            # Set the value of edit_curvature_tangential to match edit_curvature_sagittal
            curvature_sagittal = self.ui_library.edit_curvature_sagittal.text().strip()
            self.ui_library.edit_curvature_tangential.setText(curvature_sagittal)
            self.ui_library.edit_curvature_tangential.setEnabled(False)  # Disable the field
        else:
            self.ui_library.edit_curvature_tangential.setEnabled(True)  # Enable the field

    def close_library_window(self):
        """
        Closes the library window.
        """
        if self.library_window:
            self.library_window.close()

    def load_library_files(self):
        """
        Loads files from the 'Library' folder and displays them in the listView_libraries.
        """
        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))

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
        self.ui_library.listView_libraries.setModel(model)

    def display_file_contents(self, index: QModelIndex):
        """
        Displays the 'components' entries of the selected file in the listView_lib_components.
        Sets up the data for further interaction.
        """
        # Get the selected file name
        selected_file = index.data()

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))
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
                self.ui_library.radioButton_is_spherical.setChecked(True)
            else:
                self.toggle_curvature_tangential(False)
                self.ui_library.radioButton_is_spherical.setChecked(False)

            # Replace 1e30 with "Infinity"
            if curvature_tangential == 1e30:
                curvature_tangential = "Infinity"
            if curvature_sagittal == 1e30:
                curvature_sagittal = "Infinity"

            # Set the values in the UI fields
            self.ui_library.edit_curvature_tangential.setText(str(curvature_tangential))
            self.ui_library.edit_curvature_sagittal.setText(str(curvature_sagittal))

            # Extract and set the type in comboBox_type
            component_type = component.get("type", "N/A")
            index_in_combobox = self.ui_library.comboBox_type.findText(component_type)
            if index_in_combobox != -1:
                self.ui_library.comboBox_type.setCurrentIndex(index_in_combobox)
            else:
                QMessageBox.warning(
                    self.library_window,
                    "Unknown Component Type",
                    f"Unknown component type: {component_type}"
                )

            # Set the name and manufacturer in the UI fields
            self.ui_library.edit_name.setText(component.get("name", ""))
            self.ui_library.edit_manufacturer.setText(component.get("manufacturer", ""))
        else:
            QMessageBox.warning(
                self.library_window,
                "Invalid Component Index",
                f"Invalid component index: {selected_index}"
            )
    
    def add_new_library(self):
        """
        Creates a new .json file with user-provided name and adds it to the listView_libraries.
        """
        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))

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
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))
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

    def accept_changes(self):
        """
        Saves the changes made in the UI fields to the selected component in the library file.
        """
        # Get the currently selected library file
        selected_file_index = self.ui_library.listView_libraries.currentIndex().row()
        model = self.ui_library.listView_libraries.model()

        if selected_file_index < 0:
            QMessageBox.warning(
                self.library_window,
                "No Library Selected",
                "Please select a library to save changes to a component."
            )
            return

        selected_file_name = model.item(selected_file_index).text()

        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))
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
                "Please select a component to save changes."
            )
            return

        component = library_data["components"][selected_component_index]

        # Update component data from the UI fields
        component["name"] = self.ui_library.edit_name.text().strip()
        component["manufacturer"] = self.ui_library.edit_manufacturer.text().strip()
        component["type"] = self.ui_library.comboBox_type.currentText()

        # Handle properties based on the type
        if component["type"] == "LENS":
            try:
                component["properties"]["CURVATURE_IN_SAG"] = float(self.ui_library.edit_curvature_in_sag.text().strip())
                component["properties"]["CURVATURE_OUT_SAG"] = float(self.ui_library.edit_curvature_out_sag.text().strip())
                component["properties"]["CURVATURE_IN_TAN"] = float(self.ui_library.edit_curvature_in_tan.text().strip())
                component["properties"]["CURVATURE_OUT_TAN"] = float(self.ui_library.edit_curvature_out_tan.text().strip())
                # Determine if the component is round
                if self.ui_library.radioButton_is_spherical.isChecked():
                    component["properties"]["IS_ROUND"] = 1.0 # True
                else:
                    component["properties"]["IS_ROUND"] = 0.0 # False
            except ValueError:
                QMessageBox.warning(
                    self.library_window,
                    "Invalid Input",
                    "Please enter valid numeric values for lens curvatures."
                )
                return
        else:  # Default to MIRROR
            try:
                curvature_tangential = self.ui_library.edit_curvature_tangential.text().strip()
                curvature_sagittal = self.ui_library.edit_curvature_sagittal.text().strip()

                if curvature_tangential.lower() == "infinity":
                    component["properties"]["CURVATURE_TANGENTIAL"] = 1e30
                else:
                    component["properties"]["CURVATURE_TANGENTIAL"] = float(curvature_tangential)

                if curvature_sagittal.lower() == "infinity":
                    component["properties"]["CURVATURE_SAGITTAL"] = 1e30
                else:
                    component["properties"]["CURVATURE_SAGITTAL"] = float(curvature_sagittal)

                # Determine if the component is round
                if self.ui_library.radioButton_is_spherical.isChecked():
                    component["properties"]["IS_ROUND"] = 1.0 # True
                else:
                    component["properties"]["IS_ROUND"] = 0.0 # False
            except ValueError:
                QMessageBox.warning(
                    self.library_window,
                    "Invalid Input",
                    "Please enter valid numeric values for mirror curvatures."
                )
                return

        # Save the updated library file
        try:
            with open(selected_file_path, 'w') as file:
                json.dump(library_data, file, indent=4)
            QMessageBox.information(
                self.library_window,
                "Success",
                f"Changes to the component '{component['name']}' have been saved."
            )
            # Update the listView_lib_components to reflect the changes
            self.display_file_contents(self.ui_library.listView_libraries.currentIndex())
        except Exception as e:
            QMessageBox.critical(
                self.library_window,
                "Error",
                f"An error occurred while saving the library file: {e}"
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
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))
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

        # Initialize the new component based on the type
        if selected_type == "LENS":
            new_component = {
                "type": "LENS",
                "name": "new lens",
                "manufacturer": "",
                "properties": {
                    "CURVATURE_IN_SAG": "",
                    "CURVATURE_OUT_SAG": "",
                    "CURVATURE_IN_TAN": "",
                    "CURVATURE_OUT_TAN": ""
                }
            }
        else:  # Default to MIRROR
            new_component = {
                "type": "MIRROR",
                "name": "new mirror",
                "manufacturer": "",
                "properties": {
                    "CURVATURE_TANGENTIAL": "",
                    "CURVATURE_SAGITTAL": "",
                    "IS_ROUND": ""
                }
            }

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
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))
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