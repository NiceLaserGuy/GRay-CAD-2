from PyQt5.QtCore import QObject, QDir, QModelIndex
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from os import path, listdir, rename
from PyQt5 import uic
import json

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

    def load_library_files(self):
        """
        Loads files from the 'Library' folder and displays them in the listView_libraries.
        """
        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))

        # Check if the folder exists
        if not path.exists(library_path):
            print(f"Library folder not found: {library_path}")
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
            print(f"File not found: {file_path}")
            return

        # Read the contents of the file
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)  # Parse the JSON file
        except Exception as e:
            print(f"Error reading file: {e}")
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
                    print(f"Component without 'name' attribute found: {component}")
        else:
            print(f"No 'components' list found in {selected_file}")

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
                print(f"Unknown component type: {component_type}")

            # Set the name and manufacturer in the UI fields
            self.ui_library.edit_name.setText(component.get("name", ""))
            self.ui_library.edit_manufacturer.setText(component.get("manufacturer", ""))
        else:
            print(f"Invalid component index: {selected_index}")

    def accept_changes(self):
        """
        Saves the changes made in the listView_libraries to the selected library file.
        """
        # Get the currently selected file in the listView_libraries
        selected_file_index = self.ui_library.listView_libraries.currentIndex().row()
        model = self.ui_library.listView_libraries.model()

        if selected_file_index >= 0:
            selected_file_name = model.item(selected_file_index).text()

            # Path to the Library folder
            library_path = path.abspath(path.join(path.dirname(__file__), "Library"))
            old_file_path = path.join(library_path, selected_file_name)

            # Update the file name if it has been changed
            new_file_name = model.item(selected_file_index).text().strip()  # Get the edited name
            if not new_file_name:  # Check if the new file name is empty
                print("Error: File name cannot be empty.")
                return

            if new_file_name != selected_file_name:
                new_file_path = path.join(library_path, f"{new_file_name}.json")
                try:
                    rename(old_file_path, new_file_path)  # Rename the file
                    print(f"File renamed from {selected_file_name} to {new_file_name}.json")
                    self.load_library_files()
                except Exception as e:
                    print(f"Error renaming file: {e}")
                    return

        # Save changes to the selected component (if applicable)
        selected_index = self.ui_library.listView_lib_components.currentIndex().row()
        if 0 <= selected_index < len(self.components_data):
            component = self.components_data[selected_index]

            # Update component data
            component["name"] = model.item(selected_file_index).text()
            component["manufacturer"] = self.ui_library.edit_manufacturer.text()

            # Confirm the changes
            print(f"Changes accepted for component: {component.get('name', 'Unnamed')}")
        else:
            print("No valid component selected.")

    def close_library_window(self):
        """
        Closes the library window.
        """
        if self.library_window:
            self.library_window.close()

    def add_new_library(self):
        """
        Creates a new .json file with default content and adds it to the listView_libraries.
        """
        # Path to the Library folder
        library_path = path.abspath(path.join(path.dirname(__file__), "Library"))

        # Default file name and content
        new_file_name = "new_file.json"
        new_file_path = path.join(library_path, new_file_name)
        default_content = {
            "name": "new file",
            "type": "LIBRARY",
            "components": []
        }

        # Ensure the file does not already exist
        counter = 1
        while path.exists(new_file_path):
            new_file_name = f"new_file_{counter}.json"
            new_file_path = path.join(library_path, new_file_name)
            counter += 1

        # Create the new file
        try:
            with open(new_file_path, 'w') as file:
                json.dump(default_content, file, indent=4)
        except Exception as e:
            print(f"Error creating new file: {e}")
            return

        # Add the new file to the listView_libraries
        self.load_library_files()

        # Select the newly created file in the listView
        model = self.ui_library.listView_libraries.model()
        for row in range(model.rowCount()):
            if model.item(row).text() == new_file_name:
                self.ui_library.listView_libraries.setCurrentIndex(model.index(row, 0))
                break

        print(f"New library file created: {new_file_name}")