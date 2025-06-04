from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt5.QtCore import *

class Action:

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
            "1. Use the library to manage your components.<br>"
            "2. Take advantage of the simulation features like the Modematcher and the Cavity Designer.<br>"
            "3. Don't forget to save your work!<br>"
            '4. Report bugs on GitHub: <a href="https://github.com/NiceLaserGuy/GRay-CAD-2">https://github.com/NiceLaserGuy/GRay-CAD-2</a>'
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