from PyQt6.QtWidgets import (
    QDialog, QPushButton, QFormLayout, QApplication, QLabel,
    QLineEdit, QTextEdit, QComboBox, QDateEdit, QVBoxLayout
)
from PyQt6.QtCore import QDate, QEvent, Qt, QSize
from Utils import drag_enter_event, drop_event, browse_path

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
        Dataset Path: Folder path for dataset upload to DataStore.
        Capture-Log Path: File path for Companion Capture-Log for the corresponding Dataset.
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
        self.setMinimumSize(600, 400)
    
    def setup_ui(self):
        """
        Sets up the user interface components for the metadata dialog.
        """
        layout = QFormLayout()

        self.date_acquired_input = QDateEdit()
        self.date_acquired_input.setCalendarPopup(True)
        self.date_acquired_input.setDate(QDate.currentDate())
        self.date_acquired_input.setDisplayFormat("dd-MM-yyyy")
        self.date_acquired_input.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.date_acquired_input.installEventFilter(self)
        calendar = self.date_acquired_input.calendarWidget()
        calendar.setMinimumSize(QSize(400, 300))
        calendar.setStyleSheet("""
            QCalendarWidget {
                font-size: 12pt;
                color: black;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: lightblue;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: white;
            }
            QCalendarWidget QAbstractItemView:hover {
                background-color: lightblue;
                color: green;
            }
            QCalendarWidget QAbstractItemView:selected {
                background-color: blue;
                color: red;
            }
        """)
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
        self.Dataset_input.setPlaceholderText("Drag and drop a folder here or click 'Browse'")
        self.Dataset_input.setStyleSheet("QLineEdit { color: gray; }")
        browse_DS_button = QPushButton("Browse")
        self.CapLog_input = QLineEdit()
        self.CapLog_input.setPlaceholderText("Drag and drop a file here or click 'Browse'")
        self.CapLog_input.setStyleSheet("QLineEdit { color: gray; }")
        browse_CapLog_button = QPushButton("Browse")
        browse_DS_button.clicked.connect(lambda: browse_path(self.Dataset_input, folder=True))
        browse_CapLog_button.clicked.connect(lambda: browse_path(self.CapLog_input))

        self.Dataset_input.setAcceptDrops(True)
        self.CapLog_input.setAcceptDrops(True)

        self.Dataset_input.dragEnterEvent = drag_enter_event
        self.Dataset_input.dropEvent = lambda event: drop_event(event, self.Dataset_input, folder=True)
        self.CapLog_input.dragEnterEvent = drag_enter_event
        self.CapLog_input.dropEvent = lambda event: drop_event(event, self.CapLog_input, folder=False)

        dataset_layout = QVBoxLayout()
        dataset_label = QLabel("Dataset Path:")
        dataset_layout.addWidget(dataset_label)
        dataset_layout.addWidget(self.Dataset_input)
        dataset_layout.addWidget(browse_DS_button)

        caplog_layout = QVBoxLayout()
        caplog_label = QLabel("CaptureLog Path:")
        caplog_layout.addWidget(caplog_label)
        caplog_layout.addWidget(self.CapLog_input)
        caplog_layout.addWidget(browse_CapLog_button)

        # Add layouts to the main form layout
        layout.addRow(dataset_layout)
        layout.addRow(caplog_layout)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_metadata)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addRow(save_button, cancel_button)

        self.setLayout(layout)
        
            
    def eventFilter(self, source, event):
        # Block key press events for the QDateEdit
        if event.type() == QEvent.Type.KeyPress and source is self.date_acquired_input:
            return True  # Ignore key presses
        return super().eventFilter(source, event)

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
            "Dataset Path": self.Dataset_input.text(),
            "Capture-Log Path": self.CapLog_input.text()
        }
        self.accept()
        return metadata

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { font-size: 15pt; }")
    main_window = MetadataDialog()
    main_window.show()
    sys.exit(app.exec())