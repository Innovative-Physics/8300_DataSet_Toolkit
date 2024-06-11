from PyQt6.QtWidgets import (
    QDialog, QMainWindow, QApplication, QPushButton, QVBoxLayout, QWidget, QLabel,
    QMessageBox, QListWidget, QRadioButton, QButtonGroup,
    QHBoxLayout, QComboBox, QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import os
import sys
import re
import json
from scipy.ndimage import gaussian_filter1d

'''
Modular dependencies:
'''
from Utils import createHDivider, drag_enter_event, drop_event, browse_path
from DataStoreUpload import MetadataDialog
from PhotopeakTools import PhotopeakDetector, PeakTuningDialog
from QuickCalibrate import quick_calibrate



class GammaToolsWindow(QMainWindow):
    """
    Main application window for Gamma Spectra Database, handling the interface and interactions
    for managing gamma spectra data, including file and channel selection, peak detection, and data plotting.
    """
    closed = pyqtSignal()
    selected_file = None
    isotope_combo = None
    last_plot_all_channels = True 
    def __init__(self):
        """
        Constructor for the main window, initializing the user interface and connecting signals.
        """
        super().__init__()
        self.setWindowTitle("Gamma Spectra Database")
        self.setGeometry(300, 50, 1200, 600)

        '''
        Initialize file_path_label for drag & drop and browse
        '''
        
        self.file_path_label = QLabel("Drop a folder here")
        self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_path_label.setStyleSheet("background-color: white;")

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(lambda: browse_path(self.file_path_label, self.update_file_list, self.save_last_used_folder, folder=True))
        
        self.setAcceptDrops(True)
        self.dragEnterEvent = drag_enter_event
        self.dropEvent = lambda event: drop_event(event, self.file_path_label, self.update_file_list, self.save_last_used_folder, folder=True)
        
        self.dropped_folder_path=""
        self.update_file_list()
        '''
        Plotting initialization
        '''
        self.figure = plt.Figure(figsize=(15,9))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(1000, 350)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        '''
        Layout for plotting area
        '''
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)        

        '''
        Layout for list setup
        '''
        list_layout = QHBoxLayout() 

        '''
        File list setup
        '''
        file_layout = QVBoxLayout()
        file_layout.addWidget(QLabel("Files:"))
        self.file_list_widget = QListWidget()
        self.file_list_widget.setMaximumSize(500, 1000)
        self.file_list_widget.itemClicked.connect(self.update_channel_list)
        
        self.file_list_widget.itemClicked.connect(self.on_file_selected)
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selection_changed)
        file_layout.addWidget(self.file_list_widget)
        list_layout.addLayout(file_layout)
        
        '''
        List channels in file
        '''
        channel_layout = QVBoxLayout()
        channel_layout.addWidget(QLabel("Channels:"))
        self.channel_list_widget = QListWidget()
        self.channel_list_widget.setMaximumSize(100, 1000)
        self.channel_list_widget.itemClicked.connect(self.on_channel_selected)
        self.channel_list_widget.itemSelectionChanged.connect(self.on_channel_selection_changed)
        channel_layout.addWidget(self.channel_list_widget)
        list_layout.addLayout(channel_layout)
        
        '''
        List for detected Photopeaks
        '''
        peak_layout = QVBoxLayout()
        peak_layout.addWidget(QLabel("Detected Peaks:"))
        self.detected_peak_list = QListWidget()
        self.detected_peak_list.setMaximumSize(400, 1000)
        self.detected_peak_list.itemClicked.connect(self.on_peak_selected)
        peak_layout.addWidget(self.detected_peak_list)
        list_layout.addLayout(peak_layout)
        list_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        '''
        Combining plot and list layouts vertically
        '''
        plots_and_lists_layout = QVBoxLayout()
        path_entry_layout = QHBoxLayout()

        path_entry_layout.addWidget(self.file_path_label)
        path_entry_layout.addWidget(self.browse_button)


        self.isotope_combo = QComboBox()
        self.isotope_combo.addItem("Select Isotope:")
        self.isotope_combo.addItem("241Am")
        self.isotope_combo.addItem("137Cs")
        self.isotope_combo.addItem("60Co")
        self.isotope_combo.addItem("241Am | 137Cs")
        path_entry_layout.addWidget(self.isotope_combo)

        plots_and_lists_layout.addLayout(path_entry_layout)
        plots_and_lists_layout.addWidget(createHDivider())
        plots_and_lists_layout.addLayout(plot_layout)


        plots_and_lists_layout.addLayout(list_layout)
        
        '''
        Settings layout for options:
        '''
        settings_layout = QVBoxLayout()
        '''
        Photopeak settings for fine-tuning peak positions
        '''
        settings_layout.addWidget(QLabel("Photopeak settings:"))
        self.store_multiple_peaks_checkbox = QCheckBox("Multi-Iso")
        settings_layout.addWidget(self.store_multiple_peaks_checkbox)
        self.detect_peaks_button = QPushButton("Detect Photopeaks")
        self.detect_peaks_button.clicked.connect(self.detect_peaks)
        settings_layout.addWidget(self.detect_peaks_button)
        
        self.manual_peak_tuning_button = QPushButton("Fine-tune peak")
        self.manual_peak_tuning_button.clicked.connect(self.manual_peak_tuning)
        settings_layout.addWidget(self.manual_peak_tuning_button)

        '''
        Button for detecting all Photopeaks in file
        '''

        self.save_peaks_to_file_button = QPushButton("Save Photopeaks")
        self.save_peaks_to_file_button.clicked.connect(self.save_peaks_to_file)
        settings_layout.addWidget(self.save_peaks_to_file_button)

        '''
        Button for clearing all plots and detected peaks
        '''
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self.clear_all_peaks)
        settings_layout.addWidget(self.clear_all_button)

        '''
        Calibration settings for quick calibration options
        '''
        settings_layout.addWidget(QLabel("Calibration:"))
        self.quick_calibrate_button = QPushButton("Quick Calibrate")
        self.quick_calibrate_button.clicked.connect(self.quick_calibrate_channel)
        settings_layout.addWidget(self.quick_calibrate_button)

        '''
        Radio buttons for selecting data calibration mode
        '''
        settings_layout.addWidget(QLabel("Data Calibration:"))
        self.calibrated_radio = QRadioButton("Calibrated Data")
        self.raw_radio = QRadioButton("Raw Data")
        self.calibrated_radio.setChecked(True)
        self.calibration_group = QButtonGroup()
        self.calibration_group.addButton(self.calibrated_radio)
        self.calibration_group.addButton(self.raw_radio)
        settings_layout.addWidget(self.calibrated_radio)
        settings_layout.addWidget(self.raw_radio)

        '''
        Plotting function buttons for visual data analysis
        '''

        self.sum_channels_button = QPushButton("Sum All Channels")
        self.sum_channels_button.clicked.connect(self.sum_and_plot_all_channels)
        self.save_summed_spectrum_button = QPushButton("Save Summed spectra")
        self.save_summed_spectrum_button.clicked.connect(self.save_summed_spectrum)
        self.norm_chan_button = QPushButton("Normalize All Channels")
        self.norm_chan_button.clicked.connect(self.normalize_all_channels)
        
        settings_layout.addWidget(QLabel("Plotting:"))
        settings_layout.addWidget(self.sum_channels_button)
        settings_layout.addWidget(self.save_summed_spectrum_button)
        settings_layout.addWidget(self.norm_chan_button)
        
        '''
        Datastore options for saving detected peaks and spectra
        '''
        settings_layout.addWidget(QLabel("Datastore:"))

        self.open_metadata_dialog_button = QPushButton("Save Capture")
        self.open_metadata_dialog_button.clicked.connect(self.open_metadata_dialog)
        settings_layout.addWidget(self.open_metadata_dialog_button)

        list_layout.addLayout(settings_layout)

        '''
        Main layout combining plots, lists, and settings
        '''
        main_layout = QHBoxLayout()
        main_layout.addLayout(plots_and_lists_layout)


        '''
        Central drag and drop panel initialization
        '''
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setAcceptDrops(True)

        '''
        Initialization of file and channel dictionary/lists
        '''
        self.file_channels = {}
        self.selected_channel = None
        self.load_last_used_folder()
        self.showMaximized()
        
###### FILE-HANDLING METHODS ######
    def load_last_used_folder(self):
        """
        Load the last used folder path from a configuration file
        """
        config_path = os.path.join(os.path.expanduser("~"), ".gamma_tools_config.json")
        if os.path.isfile(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                last_used_folder = config.get("last_used_folder", "")
                if last_used_folder and os.path.isdir(last_used_folder):
                    self.file_path_label.setText(last_used_folder)
                    self.load_folder_contents(last_used_folder)
    
    
    def save_last_used_folder(self, folder_path):
        """
        Save the last used folder path to a configuration file
        """
        config_path = os.path.join(os.path.expanduser("~"), ".gamma_tools_config.json")
        config = {"last_used_folder": folder_path}
        with open(config_path, "w") as f:
            json.dump(config, f)
    
    ''' 
    Event handling methods
    '''

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
    
    def load_folder_contents(self, folder_path):
        """
        Load the contents of the specified folder and update the file list.
        """
        if os.path.isdir(folder_path):
            csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
            if csv_files:
                csv_files.sort(key=lambda x: self.extract_number_from_filename(x) if re.search(r'\d+', x) else x)
                self.file_list_widget.clear()
                self.file_list_widget.addItems(csv_files)
                self.file_path_label.setText(folder_path)
            else:
                QMessageBox.warning(self, "Warning", "No CSV files found in the selected directory.")
        else:
            QMessageBox.critical(self, "Error", f"The path {folder_path} is not a valid directory.")
            
            
    """
    Open a file dialog to browse and select a directory.
    """
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.file_path_label.setText(directory)
            self.dropped_folder_path = directory
            self.update_file_list()
            self.save_last_used_folder(directory)        
    
    '''
    Drag and drop functionality
    '''
    @staticmethod
    def extract_number_from_filename(filename):
        match = re.search(r'\d+', filename)
        return int(match.group()) if match else float('inf')

    def update_file_list(self):
        folder_path = self.file_path_label.text()
        if os.path.isdir(folder_path):
            csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
            if csv_files:
                csv_files.sort(key=lambda x: self.extract_number_from_filename(x))
                self.file_list_widget.clear()
                self.file_list_widget.addItems(csv_files)
    
    def connect_signals(self):
        self.channel_list_widget.itemClicked.connect(self.on_channel_selected)
        self.detected_peak_list.itemClicked.connect(self.on_peak_selected)
    
    
    '''
    Selecting peak also selects the corresponding channel
    '''
    def on_peak_selected(self, item):
        channel_text = item.text().split(':')[0]
        self.selected_peak = item.text()

        for i in range(self.channel_list_widget.count()):
            if self.channel_list_widget.item(i).text() == channel_text:
                self.channel_list_widget.setCurrentItem(self.channel_list_widget.item(i))
                self.selected_channel = self.channel_list_widget.item(i).text()
                break
    
    def disable_sum_channels_button(self):
        """
        Disable the sum_channels_button and change its color
        """
        self.sum_channels_button.setDisabled(True)
        self.sum_channels_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: lightgray; /* Change this to any color you prefer */
                color: darkgray;
            }
        """)
    
    def enable_sum_channels_button(self):
        """
        Enable the sum_channels_button and reset its style
        """
        self.sum_channels_button.setDisabled(False)
        self.sum_channels_button.setStyleSheet("")
    
    def on_channel_selected(self, item):
        """
        Handles the selection of a channel from the list, updating the corresponding peak selection,
        and plotting the channel's data.
        """
        channel_text = item.text()
        
        if channel_text != self.selected_channel:
            self.selected_channel = channel_text
            self.plot_single_channel()

        for i in range(self.detected_peak_list.count()):
            peak_info = self.detected_peak_list.item(i).text()
            if channel_text in peak_info:
                self.detected_peak_list.setCurrentItem(self.detected_peak_list.item(i))
                break
        
    def on_file_selected(self, item):
        self.selected_file = item.text()
        self.plot_all_channels()
            
        
    def on_file_selection_changed(self):
        selected_items = self.file_list_widget.selectedItems()
        if selected_items:
            self.on_file_selected(selected_items[0])   
    
    def on_channel_selection_changed(self):
        selected_items = self.channel_list_widget.selectedItems()
        if selected_items:
            self.on_channel_selected(selected_items[0])

    '''
    Updating channel list for different file selection
    '''
    def update_channel_list(self, item):
        selected_file = item.text()
        file_path = os.path.join(self.file_path_label.text(), selected_file)
        if os.path.isfile(file_path):
            df = pd.read_csv(file_path)
            if df.shape[1] == 2:
                self.channel_list_widget.clear()
                self.channel_list_widget.addItem("Single_Channel")
                self.file_channels[selected_file] = ["Single_Channel"]

                self.disable_sum_channels_button()
            else:
                channels = [f'Channel_{i}' for i in range(df.shape[0])]
                self.channel_list_widget.clear()
                self.channel_list_widget.addItems(channels)
                self.file_channels[selected_file] = channels
                self.enable_sum_channels_button()
    
######  PHOTOPEAK HANDLING  ######
    
    '''
    Automatic Photopeak detection for all channels
    '''
    def detect_peaks(self):
        PhotopeakDetector.run_detection(self)
    ''' 
    Plotting/visualization methods
    '''
    def clear_all_peaks(self):
        self.detected_peak_list.clear()
        self.selected_peak = None
        self.selected_channel = None
        self.last_detected_peak = None
        self.figure.clear()
        self.canvas.draw()
    
    def manual_peak_tuning(self):
        """
        Method for fine-tuning Photopeaks position.
        """
        if self.selected_channel is None:
            QMessageBox.warning(self, "Warning", "Please select a channel first.")
            return

        if self.detected_peak_list.currentItem() is None:
            QMessageBox.warning(self, "Warning", "No peak selected for tuning.")
            return

        peak_item = self.detected_peak_list.currentItem()
        peak_info = peak_item.text()
        selected_peak_position = float(peak_info.split(':')[1].strip().split(' ')[2])

        isotope = self.isotope_combo.currentText()
        if isotope == "Select Isotope":
            QMessageBox.warning(self, "Warning", "Please select an isotope first.")
            return

        file_path = os.path.join(self.file_path_label.text(), self.selected_file)
        df = pd.read_csv(file_path)

        if self.selected_channel == "Single_Channel":
            x_values = pd.to_numeric(df.iloc[:, 0], errors='coerce')
            y_values = df.iloc[:, 1].values
        else:
            channel_index = int(self.selected_channel.split('_')[1])
            channel_data = df.iloc[channel_index]
            x_values = pd.to_numeric(df.columns, errors='coerce')
            y_values = channel_data.values

        peak_range_mask = (x_values > selected_peak_position - 100) & (x_values < selected_peak_position + 100)
        peak_x_values = x_values[peak_range_mask]
        peak_y_values = y_values[peak_range_mask]

        dialog = PeakTuningDialog(self, selected_peak_position, peak_x_values, peak_y_values)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_peak_position = dialog.get_peak_position()

            updated_peak_info = f"{self.selected_channel}: Peak at {new_peak_position:.2f} keV"
            peak_item.setText(updated_peak_info)

            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            self.ax.plot(x_values, y_values, label='Channel Data')
            self.ax.set_title(f'{self.selected_channel}')
            self.ax.set_xlabel('Energy (keV)' if self.calibrated_radio.isChecked() else 'ADC')
            self.ax.set_ylabel('Counts')
            self.ax.axvline(x=new_peak_position, color='r', linewidth = 0.5, linestyle='--', label='Selected Peak')
            self.ax.legend()
            self.canvas.draw()
    
    '''
    Saving photopeak list to .csv file
    '''
    def save_peaks_to_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Error", "No file selected.")
            return

        peak_data = []
        for i in range(self.detected_peak_list.count()):
            item_text = self.detected_peak_list.item(i).text()
            channel, peak = item_text.split(':')
            peak_value = float(peak.strip().split(' ')[2])
            peak_data.append((channel.strip(), peak_value))
        
        original_filename = os.path.splitext(self.selected_file)[0]
        peaks_filename = f"{original_filename}_peaks.csv"
        
        df_peaks = pd.DataFrame(peak_data, columns=['Channel', 'Peak (keV)'])
        df_peaks.to_csv(peaks_filename, index=False)
        QMessageBox.information(self, "Save Complete", f"Peaks saved to file successfully: {peaks_filename}")           
    
    
    def get_detected_peaks(self):
        detected_peaks = []
        # Retrieve detected peaks from the list widget
        for i in range(self.detected_peak_list.count()):
            item_text = self.detected_peak_list.item(i).text()
            try:
                peak_value = float(item_text.split(':')[1].strip().split(' ')[2])
                detected_peaks.append(peak_value)
            except (IndexError, ValueError) as e:
                print(f"Error parsing detected peak from item text '{item_text}': {e}")
        print(f"Detected peaks: {detected_peaks}")
        return detected_peaks

    def get_known_energies(self):
        isotope = self.isotope_combo.currentText()
        known_energies = {
            "241Am": 59.54,
            "137Cs": 661.66,
            "60Co": 1173.23,
        }
        known_energy = known_energies.get(isotope, None)
        print(f"Known energy for {isotope}: {known_energy}")
        return [known_energy] if known_energy else []
    
    
######   PLOTTING METHODS   ######
    
    def plot_all_channels(self, df=None):
        """
        Plot all channels in the spectral file or a provided DataFrame.
        """
        if df is None:
            file_path = os.path.join(self.file_path_label.text(), self.selected_file)
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                print(f"Error in loading the file: {str(e)}")
                return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if df.shape[1] == 2:
            x_values = pd.to_numeric(df.iloc[:, 0], errors='coerce')
            y_values = df.iloc[:, 1].values
            ax.plot(x_values, y_values, label="Single_Channel")
        else:
            num_channels = df.shape[0]
            for index in range(num_channels):
                channel_data = df.iloc[index, :]
                channel_data.index = pd.to_numeric(channel_data.index, errors='coerce')
                channel_name = f'Channel_{index}'
                ax.plot(channel_data.index, channel_data.values, label=channel_name)

        ax.set_title(f'All Channels in {self.selected_file}')
        ax.set_xlabel('Energy (keV)' if self.calibrated_radio.isChecked() else 'ADC')
        ax.set_ylabel('Counts')

        self.canvas.draw()
        self.last_plot_all_channels = True
        
    def plot_all_channels_with_peaks(self, df, detected_peaks):
        """
        Plot all channels and mark detected peaks.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        for index, row in df.iterrows():
            channel_name = f'Channel_{index}'
            x_values = pd.to_numeric(df.columns, errors='coerce')
            y_values = row.values
            ax.plot(x_values, y_values, label=channel_name)

        for channel_name, peak_energy in detected_peaks:
            ax.axvline(x=peak_energy, color='r', linestyle='--', linewidth = 0.5, label=f'{channel_name} Peak at {peak_energy:.2f} keV')

        ax.set_title('All Channels with Detected Peaks')
        ax.set_xlabel('Energy (keV)' if self.calibrated_radio.isChecked() else 'ADC')
        ax.set_ylabel('Counts')


        self.canvas.draw() 
        self.last_plot_all_channels = True             
        
    '''
    Plotting a single channel spectra
    '''
    def plot_single_channel(self):        
        file_path = os.path.join(self.file_path_label.text(), self.selected_file)
        df = pd.read_csv(file_path)
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if self.selected_channel == "Single_Channel":
            x_values = df.iloc[:, 0]  
            y_values = df.iloc[:, 1]  
        else:
            try:
                channel_index = int(self.selected_channel.split('_')[1])
                channel_data = df.iloc[channel_index]
                x_values = pd.to_numeric(df.columns, errors='coerce')
                y_values = channel_data.values
            except ValueError as e:
                QMessageBox.critical(self, "Error", f"Failed to parse channel index from {self.selected_channel}: {e}")
                return
        ref_e = 0
        if self.isotope_combo.currentText() == "241Am":
            ref_e = 59.7
        if self.isotope_combo.currentText() == "137Cs":
            ref_e = 661.9
        if self.isotope_combo.currentText() == "60Co":
            ref_e = 1172.3
            ref_e1 = 1332.5
        else:
            ref_e1 = None
        ax.plot(x_values, y_values)
        if self.calibrated_radio.isChecked():
            ax.axvline(x = ref_e, linestyle = 'dotted', linewidth = 0.7, color = 'k', label = f'Iso ref energy @ {ref_e}')
        if ref_e1 is not None:
            ax.axvline(x = ref_e1)
        ax.set_title(f'{self.selected_channel}')
        ax.set_xlabel('Energy (keV)' if self.calibrated_radio.isChecked() else 'ADC')
        ax.set_ylabel('Counts')

        for i in range(self.detected_peak_list.count()):
            item_text = self.detected_peak_list.item(i).text()
            if item_text.startswith(self.selected_channel + ":"):
                peak_energy = float(item_text.split(':')[1].strip().split(' ')[2])
                self.last_detected_peak = peak_energy
                smoothed_y =  gaussian_filter1d(y_values, sigma=15)
                ax.plot(x_values, smoothed_y, label = 'Smoothed data', linewidth = 0.5, color ='r', alpha =0.5)
                
                ax.axvline(x=peak_energy, color='r', linestyle='--', linewidth = 0.5, label=f'Peak at {peak_energy:.2f} keV')
                ax.legend()
                break

        self.canvas.draw()
        self.last_plot_all_channels = False
            
###### DATA-PROCESSING METHODS ######
            
    def normalize_all_channels(self):
            """
            Normalize all channels in the DataFrame and replot.
            """
            file_path = os.path.join(self.file_path_label.text(), self.selected_file)
            try:
                df = pd.read_csv(file_path)
                normalized_df = df.div(df.sum(axis=0), axis=1)

                self.plot_all_channels(normalized_df)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred during normalization: {str(e)}")
                print(f"Error in normalization: {str(e)}")
    
    '''
    Plot channel-summed spectra
    '''
    def sum_and_plot_all_channels(self):
        if self.selected_file is None:
            QMessageBox.warning(self, "Error", "No file selected. Please select a file first.")
            return
        
        file_path = os.path.join(self.file_path_label.text(), self.selected_file)
        df = pd.read_csv(file_path)
        try:
            sum_spectrum = df.sum(axis=0)
            x_values = pd.to_numeric(df.columns, errors='coerce')


            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(x_values, sum_spectrum)
            ax.set_title(f'Summed Spectrum of All Channels in {self.selected_file}')
            ax.set_xlabel('Energy (kev)' if self.calibrated_radio.isChecked() else 'ADC')
            ax.set_ylabel('Counts')
            self.canvas.draw()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            print(f"Error in summing and plotting: {str(e)}")    
        
    '''
    Saving the channel-summed spectra
    '''
    def save_summed_spectrum(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Error", "No file selected. Please select a file first.")
            return
        
        file_path = os.path.join(self.file_path_label.text(), self.selected_file)
        df = pd.read_csv(file_path)
        try:
            summed_spectrum = df.sum(axis=0)
            x_values = pd.to_numeric(df.columns, errors='coerce')
            
            original_filename = os.path.splitext(self.selected_file)[0]
            summed_filename = f"{original_filename}_combined.csv"
            summed_file_path = os.path.join(self.file_path_label.text(), summed_filename)
            
            summed_spectrum_df = pd.DataFrame({'Channel/Energy': x_values, 'Counts': summed_spectrum})
            summed_spectrum_df.to_csv(summed_file_path, index=False)
            
            QMessageBox.information(self, "Save Complete", f"Summed spectrum saved successfully to {summed_file_path}.")
            self.update_file_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            print(f"Error in saving summed spectrum: {str(e)}") 
            

###### DATASTORE UPLOADING METHODS ######

    '''
    Opening metadata interface for saving capture to datastore
    '''
    def open_metadata_dialog(self):
        initial_folder_path = getattr(self, "dropped_folder_path", "")
        dialog = MetadataDialog(initial_folder_path)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            metadata = dialog.save_metadata()
            print("Metadata Saved:", metadata)


    def quick_calibrate_channel(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Error", "No file selected. Please select a file first.")
            return

        file_path = os.path.join(self.file_path_label.text(), self.selected_file)
        df = pd.read_csv(file_path)

        detected_peaks = self.get_detected_peaks()
        known_energies = self.get_known_energies()

        if len(detected_peaks) == 0:
            QMessageBox.warning(self, "Error", "No detected peaks found.")
            return

        if len(detected_peaks) != len(known_energies):
            QMessageBox.warning(self, "Error", f"Detected peaks count ({len(detected_peaks)}) does not match known energies count ({len(known_energies)})")
            return

        try:
            for detected_peak, known_energy in zip(detected_peaks, known_energies):
                # Use quick_calibrate function to adjust the index for each channel
                calibrated_df = quick_calibrate(df, detected_peak, known_energy)

                # Save the calibrated DataFrame to a new CSV file
                calibrated_filename = os.path.splitext(self.selected_file)[0] + f"_calibrated_{known_energy:.2f}keV.csv"
                calibrated_file_path = os.path.join(self.file_path_label.text(), calibrated_filename)
                calibrated_df.to_csv(calibrated_file_path, index=True)  # Index=True to save the index

                QMessageBox.information(self, "Calibration Complete", f"Calibrated spectrum saved to {calibrated_file_path}.")
                self.update_file_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during calibration: {str(e)}")
            print(f"Error in quick calibration: {str(e)}")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = GammaToolsWindow()
    main_window.show()
    sys.exit(app.exec())