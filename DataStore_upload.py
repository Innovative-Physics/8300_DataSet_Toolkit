from PyQt6.QtWidgets import (
    QDialog, QPushButton, QFormLayout, QApplication, QLabel,
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QFileDialog
)
from PyQt6.QtCore import QDate
import sys 

class MetadataDialog(QDialog):
    """
    A dialog for entering and saving metadata related to data acquisition activities.

    Attributes:
        date_acquired_input (QDateEdit): Input field for the date the data was acquired.
        location_input (QComboBox): Dropdown to select the location of data acquisition.
        personnel_involved_input (QComboBox): Dropdown to select personnel involved in data acquisition.
        purpose_of_capture_input (QComboBox): Dropdown to select the purpose of the data acquisition.
        camera_id_input (QLineEdit): Input field for the camera ID used in data acquisition.
        notes_input (QTextEdit): Text area for any additional notes about the data acquisition.
        filepath_input (QLineEdit): Input field for the file path where data is stored.
    """

    def __init__(self, initial_folder_path=""):
        """
        Initialize the dialog with optional initial folder path setting.

        Parameters:
            initial_folder_path (str): A default path to initialize the file path input field.
        """
        super().__init__()
        self.setWindowTitle("Metadata Input")
        self.setup_ui()

    def setup_ui(self):
        """
        Sets up the user interface components for the metadata dialog.
        """
        layout = QFormLayout()

        self.date_acquired_input = QDateEdit()
        self.date_acquired_input.setCalendarPopup(True)
        self.date_acquired_input.setDate(QDate.currentDate())
        self.date_acquired_input.setDisplayFormat("dd-MM-yyyy")
        layout.addRow("Date of acquisition:", self.date_acquired_input)

        self.location_input = QComboBox()
        locations = ["DSTL", "Inhouse", "NPL", "Nuvia", "Offshore", "Other (Please specify)"]
        self.location_input.addItems(locations)
        layout.addRow("Location:", self.location_input)

        self.personnel_involved_input = QComboBox()
        personnel = ["Adam Tyas", "Andrew Morrow", "Daniel Grosvenor", "Dr. David Prendergast",
                     "Halina Harvey", "Karl G. Plapp", "Michael MacLeod", "Muhammed Najeeb Ul Haq",
                     "Peter Kittermaster", "Sam Teale", "Shaun August", "Sripad Sahu", "Victoria Anderson",
                     "Other (Please specify)"]
        self.personnel_involved_input.addItems(personnel)
        layout.addRow("Personnel:", self.personnel_involved_input)

        self.purpose_of_capture_input = QComboBox()
        purposes = ["Calibration", "Hardware Testing", "Demonstration", "Client Data", "Other (Please specify)"]
        self.purpose_of_capture_input.addItems(purposes)
        layout.addRow("Purpose:", self.purpose_of_capture_input)

        self.camera_id_input = QLineEdit()
        self.notes_input = QTextEdit()
        layout.addRow("Camera ID:", self.camera_id_input)
        layout.addRow("Additional notes:", self.notes_input)


        self.Dataset_input = QLineEdit()
        browse_DS_button = QPushButton("Browse")
        self.CapLog_input = QLineEdit()
        browse_CapLog_button = QPushButton("Browse")
        browse_DS_button.clicked.connect(self.browse_folder)
        browse_CapLog_button.clicked.connect(self.browse_folder)
        

        file_path_layout = QFormLayout()

        file_path_layout.addRow("Dataset Path:", self.Dataset_input)
        file_path_layout.addWidget(browse_DS_button)


        file_path_layout.addRow("CaptureLog Path:", self.CapLog_input)
        file_path_layout.addWidget(browse_CapLog_button)
        layout.addRow(file_path_layout)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_metadata)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addRow(save_button, cancel_button)

        self.setLayout(layout)

    def browse_folder(self):
        """
        Opens a dialog for the user to select a folder, setting the folder path in the filepath input.
        """
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.filepath_input.setText(folder_path)


    def save_metadata(self):
        """
        Collects all metadata from the input fields and saves it.

        Returns:
            dict: A dictionary containing all the metadata fields and their values.
        """
        metadata = {
            "Date of acquisition": self.date_acquired_input.date().toString("yyyy-MM-dd"),
            "Location": self.location_input.currentText(),
            "Personnel Involved": self.personnel_involved_input.currentText(),
            "Purpose of capture": self.purpose_of_capture_input.currentText(),
            "Camera ID": self.camera_id_input.text(),
            "Additional notes": self.notes_input.toPlainText(),
            "File Path": self.filepath_input.text()
        }
        self.accept()
        return metadata


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MetadataDialog()
    main_window.show()
    sys.exit(app.exec())