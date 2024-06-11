import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


def load_and_normalize_data(filepath):
    try:
        df = pd.read_csv(filepath, header=0, dtype=np.float64)

        # Check if any non-numeric data still persists and handle it
        if df.select_dtypes(include=[np.number]).empty:
            raise ValueError("No numeric data found in the file.")
        
        # Decide based on dimensions whether rows or columns are channels
        if df.shape[0] < df.shape[1]:  # More columns than rows, so columns are the bins (x-axis)
            summed_data = df.sum(axis=0)
            channel_index = np.arange(len(summed_data))
        else:  # More rows than columns, so rows are the bins (x-axis)
            summed_data = df.sum(axis=1)
            channel_index = np.arange(len(summed_data))
        
        summed_data = pd.to_numeric(summed_data, errors='coerce')

        if summed_data.isnull().any():
            print("Non-numeric data found and ignored in the dataset.")

        # Normalize the area under the curve
        area = np.trapz(summed_data.dropna(), channel_index[:len(summed_data.dropna())])
        normalized_counts = summed_data / area

        return pd.DataFrame({'Channel': channel_index, 'Counts': normalized_counts})
    except ValueError as e:
        QMessageBox.critical(None, "Error", f"Failed to load or process the file: {str(e)}")
        return None


class DataComparisonDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Comparison")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        self.load_benchmark_button = QPushButton("Load Benchmark Data")
        self.load_benchmark_button.clicked.connect(self.load_benchmark_data)
        layout.addWidget(self.load_benchmark_button)
        
        self.load_simulated_button = QPushButton("Load Simulated Data")
        self.load_simulated_button.clicked.connect(self.load_simulated_data)
        layout.addWidget(self.load_simulated_button)
        
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.benchmark_data = None
        self.simulated_data = None
        
        self.setLayout(layout)

    def load_benchmark_data(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Benchmark Data File", "", "CSV Files (*.csv)")
        if filepath:
            self.benchmark_data = load_and_normalize_data(filepath)
            if self.benchmark_data is not None:
                self.update_plot()
                self.status_label.setText("Benchmark data loaded and normalized.")
            else:
                self.status_label.setText("Failed to load benchmark data.")

    def load_simulated_data(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Simulated Data File", "", "CSV Files (*.csv)")
        if filepath:
            self.simulated_data = load_and_normalize_data(filepath)
            if self.simulated_data is not None:
                self.update_plot()
                self.status_label.setText("Simulated data loaded and normalized.")
            else:
                self.status_label.setText("Failed to load simulated data.")

    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if self.benchmark_data is not None:
            ax.plot(self.benchmark_data['Channel'], self.benchmark_data['Counts'], label='Benchmark', color='blue')
        
        if self.simulated_data is not None:
            ax.plot(self.simulated_data['Channel'], self.simulated_data['Counts'], label='Simulated', color='red')
        
        ax.set_title("Data Comparison")
        ax.set_xlabel("Channel")
        ax.set_ylabel("Normalized Counts")
        ax.legend()
        
        self.canvas.draw()