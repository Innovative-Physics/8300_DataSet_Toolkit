from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
import sys

'''
Modular imports
'''
from GammaSpecTools import GammaToolsWindow
from DataStoreUpload import MetadataDialog
from SimSpecTools import DataComparisonDialog
from Utils import createHDivider


class MainMenu(QWidget):
    """
    Main menu for the DataStore Application, facilitating navigation to various features
    such as uploading, retrieving data, and accessing comparison, visualization and 
    basic peak detection tools for gamma and neutron datasets.
    """

    def __init__(self):
        """Initialize the main menu."""
        super().__init__()
        self.initUI()

    def initUI(self):
        """Set up the user interface components for the main menu, including layout, buttons, and events."""
        self.setWindowTitle("Datastore Upload & Retrieval")
        self.setGeometry(500, 200, 450, 250)

        self.logoLabel = QLabel(self)
        self.logoPixmap = QPixmap(r"Logo2.png")
        self.logoLabel.setPixmap(self.logoPixmap)
        self.logoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttonFont = QFont('Arial', 10)
        buttonFont.setBold(True)

        self.openMainAppButton = QPushButton("Gamma Spectra Tools", self)
        self.openMainAppButton.setFont(buttonFont)
        self.openMainAppButton.clicked.connect(self.showGammaToolsWindow)

        self.openComparisonDialogButton = QPushButton("Simulated Spectra Tools", self)
        self.openComparisonDialogButton.setFont(buttonFont)
        self.openComparisonDialogButton.clicked.connect(self.openComparisonDialog)

        self.saveGammaFilesButton = QPushButton("Upload Gamma Dataset", self)
        self.saveGammaFilesButton.setFont(buttonFont)
        self.saveGammaFilesButton.clicked.connect(self.openGammaMetadataDialog)

        self.openNeutronDialogButton = QPushButton("Upload Neutron Dataset", self)
        self.openNeutronDialogButton.setFont(buttonFont)
        self.openNeutronDialogButton.clicked.connect(self.openNeutronMetadataDialog)

        self.retrieveFromDataStoreButton = QPushButton("Access DataStore", self)
        self.retrieveFromDataStoreButton.setFont(buttonFont)
        self.retrieveFromDataStoreButton.clicked.connect(self.retrieveFromDataStore)

        self.closeMenuButton = QPushButton('Close', self)
        self.closeMenuButton.setFont(buttonFont)
        self.closeMenuButton.clicked.connect(self.closeApplication)

        layout = QVBoxLayout()
        layout.addWidget(createHDivider())
        layout.addWidget(self.logoLabel)
        layout.addWidget(createHDivider())
        layout.addWidget(self.retrieveFromDataStoreButton)
        layout.addWidget(createHDivider())
        layout.addWidget(self.saveGammaFilesButton)
        layout.addWidget(self.openNeutronDialogButton)
        layout.addWidget(createHDivider())
        layout.addWidget(self.openMainAppButton)
        layout.addWidget(self.openComparisonDialogButton)
        layout.addWidget(createHDivider())
        layout.addWidget(self.closeMenuButton)
        layout.addWidget(createHDivider())
        self.setLayout(layout)
        self.Gamma_tools_window = None
        self.comparison_dialog=None
        
    def showGammaToolsWindow(self):
        """
        Display the main application window and hide the main menu.
        """
        if not self.Gamma_tools_window:
            self.Gamma_tools_window = GammaToolsWindow()
            self.Gamma_tools_window.closed.connect(self.show)
        self.Gamma_tools_window.show()
        self.hide()

    def openComparisonDialog(self):
        """Open the spectral comparison dialog and hide the main menu temporarily."""
        if not self.comparison_dialog:
            self.comparison_dialog = DataComparisonDialog()
            self.comparison_dialog.finished.connect(self.show)
        self.comparison_dialog.show()
        self.hide()

    def openGammaMetadataDialog(self):
        """Open a dialog to enter and save metadata for the gamma dataset."""
        self.openMetadataDialog("Gamma")

    def openNeutronMetadataDialog(self):
        """Open a dialog to enter and save metadata for the neutron dataset."""
        self.openMetadataDialog("Neutron")

    def openMetadataDialog(self, dataset_type):
        """
        Open a dialog for uploading metadata related to a specified dataset type.
        Parameters:
            dataset_type (str): The type of dataset, e.g., 'Gamma' or 'Neutron'.
        Outputs:
            Saves metadata to a specified location or server if the dialog is accepted.
        """
        dialog = MetadataDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            metadata = dialog.save_metadata()
            print(f"Metadata Saved for {dataset_type} Dataset:", metadata)

    def retrieveFromDataStore(self):
        """Placeholder method for retrieving datasets from the DataStore."""
        pass

    def closeApplication(self):
        """Terminate the application."""
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainMenu()
    ex.show()
    sys.exit(app.exec())
