from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtWidgets
import copy

class Action:

    #TODO
    def action_open(self, parent):
        """
        Handles the 'Open' menu action.
        Opens a file dialog for selecting and loading files.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            parent, 
            "Open File", 
            "", 
            "All Files (*);;Python Files (*.py)"
        )
        if file_name:
            with open(file_name, 'r') as file:
                content = file.read()
                print(content)  # Placeholder

    #TODO
    def action_save(self, parent):
        print("Save action triggered")  # Placeholder
    
    #TODO: Implement save functionality
    def action_save_as(self, parent):
        file_name, _ = QFileDialog.getSaveFileName(
            parent, 
            "Save File As", 
            "", 
            "All Files (*);;Python Files (*.py)"
        )
        if file_name:
            with open(file_name, 'w') as file:
                file.write("test")  # Placeholder

    def action_about(self, parent):
        QMessageBox.information(
            parent, 
            "About", 
            "GRay-CAD 2\nVersion 1.0\nDeveloped by Jens Gumm, TU Darmstadt, LQO-Group"
        )

    def action_tips_and_tricks(self, parent):
        """
        Handles the 'Tips and Tricks' menu action.
        Displays helpful tips for using the application.
        """
        msg = QMessageBox(parent)
        msg.setWindowTitle("Tips and Tricks")
        msg.setTextFormat(Qt.RichText)
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            "1. Use the Edit/Library to manage your components.<br>"
            "2. You can drag and drop components into the setup list.<br>"
            "3. If you dont type a unit, it will be interpreted as meters.<br>"
            "4. Take advantage of the simulation features like the Modematcher and the Cavity Designer.<br>"
            "5. Don't forget to save your work!<br>"
            '6. Report bugs on GitHub: <a href="https://github.com/NiceLaserGuy/GRay-CAD-2">https://github.com/NiceLaserGuy/GRay-CAD-2</a>'
        )
        msg.exec()

    def action_exit(self, parent):
        reply = QMessageBox.question(
            parent, 
            "Exit", 
            "Do you really want to close the program? All unsaved data will be lost!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            parent.close()

    def handle_build_resonator(self, parent):
        """
        Handles the 'Build Resonator' button action.
        Sets the current context to 'resonator' and opens the library window.
        """
        parent.current_context = "resonator"
        parent.item_selector_res.open_library_window(parent)

    def handle_modematcher(self, parent):
        """
        Handles the 'Modematcher' button action.
        Sets the current context to 'modematcher' and opens the library window.
        """
        parent.current_context = "modematcher"
        parent.item_selector_modematcher.open_library_window()

    def delete_selected_setup_item(self, parent):
        for item in parent.setupList.selectedItems():
            row = parent.setupList.row(item)
            # Beam (immer an Position 0) darf nicht gelöscht werden
            if row == 0:
                continue
            parent.setupList.takeItem(row)

    def move_selected_setup_item_up(self, parent):
        listw = parent.setupList
        items = listw.selectedItems()
        if not items:
            return
        item = items[0]
        row = listw.row(item)
        # Beam (immer an Position 0) darf nicht verschoben werden
        if row <= 1:
            return
        listw.takeItem(row)
        listw.insertItem(row - 1, item)
        listw.setCurrentItem(item)

    def move_selected_setup_item_down(self, parent):
        listw = parent.setupList
        items = listw.selectedItems()
        if not items:
            return
        item = items[0]
        row = listw.row(item)
        # Beam (immer an Position 0) darf nicht verschoben werden
        if row == 0 or row >= listw.count() - 1:
            return
        listw.takeItem(row)
        listw.insertItem(row + 1, item)
        listw.setCurrentItem(item)
    
    def is_beam_item(self, item):
        component = item.data(0, QtCore.Qt.UserRole)
        if not isinstance(component, dict):
            return False
        return component.get("type", "").lower() == "beam"
    
    def move_selected_component_to_setupList(self, parent):
        # Hole das aktuell ausgewählte Item aus der componentList
        items = parent.componentList.selectedItems()
        if not items:
            return
        item = items[0]
        component = item.data(QtCore.Qt.UserRole)
        if not isinstance(component, dict):
            return

        is_beam = (
            component.get("name", "").strip().lower() == "beam"
            or component.get("type", "").strip().lower() == "beam"
        )
        # Prüfe, ob schon ein Beam in setupList existiert
        if is_beam:
            for i in range(parent.setupList.count()):
                c = parent.setupList.item(i).data(QtCore.Qt.UserRole)
                if isinstance(c, dict) and (
                    c.get("name", "").strip().lower() == "beam"
                    or c.get("type", "").strip().lower() == "beam"
                ):
                    return  # Kein zweiter Beam erlaubt

        # Füge das Item nur EINMAL in setupList ein (mit deepcopy!)
        new_item = QtWidgets.QListWidgetItem(component.get("name", "Unnamed"))
        new_item.setData(QtCore.Qt.UserRole, copy.deepcopy(component))
        if is_beam:
            parent.setupList.insertItem(0, new_item)
        else:
            parent.setupList.addItem(new_item)
        parent.setupList.setCurrentItem(new_item)