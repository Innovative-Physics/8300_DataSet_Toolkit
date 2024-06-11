from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QMessageBox
)
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class PhotopeakDetector:
    """
    Detects peaks across all channels of spectroscopic data for a selected file and isotope.

    Steps:
    1. Validate that a file and an isotope are selected.
    2. Read the spectral data from the file.
    3. Clear any previously detected peaks.
    4. For each channel, detect peaks based on x-values and y-values using adjust_ROI.
    5. Append detected peaks and update the GUI with peak information.
    6. Display completion message and update the plot based on user selection.
    """
    @staticmethod
    def run_detection(main_window):
        if main_window.selected_file is None:
            QMessageBox.warning(main_window, "Error", "No file selected. Please select a file first.")
            return

        isotope = main_window.isotope_combo.currentText()
        if isotope == "Select Isotope:":
            QMessageBox.warning(main_window, "Warning", "Please select an isotope first.")
            return

        file_path = os.path.join(main_window.file_path_label.text(), main_window.selected_file)
        df = pd.read_csv(file_path)
        main_window.detected_peak_list.clear()

        detected_peaks = []
        user_defined_range = None

        for index, row in df.iterrows():
            channel_name = f'Channel_{index}'
            x_values = pd.to_numeric(df.columns, errors='coerce')
            y_values = row.values

            # Use a specific method based on isotope
            if isotope == "60Co":
                found_peak, peak_energy = PhotopeakDetector.adjust_ROI(main_window, isotope, channel_name, x_values, y_values)
                if not found_peak:
                    found_peak, peak_energy, user_defined_range = PhotopeakDetector.prompt_for_new_range_until_peaks_found(
                        main_window, channel_name, x_values, y_values, user_defined_range)
            else:
                mask = PhotopeakDetector.get_initial_mask(main_window, isotope, x_values)
                found_peak, peak_energy = PhotopeakDetector.detect_peaks(main_window, channel_name, x_values, y_values, mask)
                if not found_peak:
                    found_peak, peak_energy, user_defined_range = PhotopeakDetector.prompt_for_new_range_until_peaks_found(
                        main_window, channel_name, x_values, y_values, user_defined_range)

            if found_peak:
                detected_peaks.append((channel_name, peak_energy))

        QMessageBox.information(main_window, "Peak Detection Complete", "All channels have been processed for peaks.")

        if main_window.selected_channel is None or main_window.last_plot_all_channels:
            main_window.plot_all_channels_with_peaks(df, detected_peaks)
        else:
            main_window.plot_single_channel()

    @staticmethod
    def adjust_ROI(main_window, isotope, channel_name, x_values, y_values):
        """
        Adjusts search range based on initial peak detection and detects peaks within the expanded range.
        The range is limited to 25% outside the original mask range.
        """
        # Get initial mask and range
        mask = PhotopeakDetector.get_initial_mask(main_window, isotope, x_values)
        initial_x_values = x_values[mask]
        initial_y_values = y_values[mask]

        if not initial_x_values.size:
            return False, None

        # Calculate the expansion of 20% outside the original mask range
        initial_range = [np.min(initial_x_values), np.max(initial_x_values)]
        range_width = initial_range[1] - initial_range[0]
        expansion = range_width * 0.25

        # Define the new search boundaries
        expanded_range = [initial_range[0] - expansion, initial_range[1] + expansion]

        # Apply the new range to filter values
        mask = (x_values >= expanded_range[0]) & (x_values <= expanded_range[1])
        restricted_x_values = x_values[mask]
        restricted_y_values = y_values[mask]

        # Detect peaks in the new filtered range
        found_peak, peak_energy = PhotopeakDetector.detect_peaks(main_window, channel_name, restricted_x_values, restricted_y_values, mask)
        if found_peak:
            peak_info = f"{channel_name}: Peak at {peak_energy:.2f} keV"
            main_window.detected_peak_list.addItem(peak_info)
            return True, peak_energy
        return False, None

    @staticmethod
    def get_initial_mask(main_window, isotope, x_values):
        """
        Returns a mask for x_values based on the selected isotope and calibration setting.

        Steps:
        1. Check isotope and calibration status.
        2. Return a boolean array where True values correspond to x_values within the desired range.
        """
        if isotope == "241Am":
            return (x_values >= 20) & (x_values <= 70) if main_window.calibrated_radio.isChecked() else (x_values >= 70) & (x_values <= 800)
        elif isotope == "137Cs":
            return (x_values >= 400) & (x_values <= 1000) if main_window.calibrated_radio.isChecked() else (x_values >= 1000) & (x_values <= 2500)
        elif isotope == "60Co":
            return (x_values >= 1100) & (x_values <= 1700) if main_window.calibrated_radio.isChecked() else (x_values >= 5000) & (x_values <= 8000)
        return np.full(x_values.shape, False, dtype=bool)

    @staticmethod
    def detect_peaks(main_window, channel_name, x_values, y_values, mask):
        """
        Detects peaks within given x and y values using Gaussian smoothing and peak finding.

        Steps:
        1. Apply Gaussian smoothing to y-values.
        2. Identify peaks with a specified prominence.
        3. If peaks are found, return the highest peak and its energy.
        4. Add detected peak information to the GUI.
        """
        restricted_x_values = x_values[mask]
        restricted_y_values = y_values[mask]

        if not restricted_x_values.size:
            return False, None

        smoothed_y_values = gaussian_filter1d(restricted_y_values, sigma=5)
        peaks, properties = find_peaks(smoothed_y_values, prominence=1.5)  # Adjust parameters as necessary

        if peaks.size > 0:
            highest_peak_index = peaks[np.argmax(properties['prominences'])]
            peak_energy = restricted_x_values[highest_peak_index]
            peak_info = f"{channel_name}: Peak at {peak_energy:.2f} keV"
            main_window.detected_peak_list.addItem(peak_info)
            return True, peak_energy

        return False, None

    @staticmethod
    def prompt_for_new_range_until_peaks_found(main_window, channel_name, x_values, y_values, user_defined_range):
        while True:
            if user_defined_range:
                new_range = user_defined_range
            else:
                new_range = PhotopeakDetector.prompt_for_new_range(main_window, x_values, y_values, channel_name)
                if new_range is None:
                    return False, None, None  # User cancelled the operation

            mask = (x_values >= new_range[0]) & (x_values <= new_range[1])
            found_peak, peak_energy = PhotopeakDetector.detect_peaks(main_window, channel_name, x_values, y_values, mask)
            if found_peak:
                peak_info = f"{channel_name}: Peak at {peak_energy:.2f} keV"
                main_window.detected_peak_list.addItem(peak_info)
                return True, peak_energy, new_range

            user_defined_range = None  # Reset user-defined range if no peak is found

    @staticmethod
    def prompt_for_new_range(main_window, x_values, y_values, channel_name):
        QMessageBox.warning(main_window, "Error", f"No characteristic peaks {main_window.isotope_combo.currentText()} detected in the expected ROI. Please select a new ROI.")
        dialog = QDialog()
        dialog.setWindowTitle(f"Select new range for {channel_name}")
        layout = QVBoxLayout(dialog)

        # Add plot
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.plot(x_values, y_values)
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        # Instructions label
        label = QLabel("Click to select the new range.")
        layout.addWidget(label)

        range_selector = []
        cursor_line = ax.axvline(color='r', linestyle='--')

        def on_click(event):
            if event.xdata is not None:
                if len(range_selector) < 2:
                    range_selector.append(event.xdata)
                    ax.axvline(event.xdata, color='r')
                    canvas.draw()
                if len(range_selector) == 2:
                    dialog.accept()

        def on_motion(event):
            if event.inaxes and event.xdata is not None:
                cursor_line.set_xdata(event.xdata)
                canvas.draw_idle()

        canvas.mpl_connect('button_press_event', on_click)
        canvas.mpl_connect('motion_notify_event', on_motion)

        dialog.exec()

        if len(range_selector) < 2:
            QMessageBox.warning(main_window, "Error", "Range selection was incomplete. Please try again.")
            return None

        new_range = sorted(range_selector)
        msg_box = QMessageBox()
        msg_box.setText(f"New range selected: {new_range[0]:.2f} to {new_range[1]:.2f}")
        accept_button = msg_box.addButton(QMessageBox.StandardButton.Ok)
        cancel_button = msg_box.addButton(QMessageBox.StandardButton.Cancel)

        result = msg_box.exec()
        if msg_box.clickedButton() == accept_button:
            return new_range
        else:
            return PhotopeakDetector.prompt_for_new_range(main_window, x_values, y_values, channel_name)


class MultiISODetector(PhotopeakDetector):
    """
    Detects peaks across multiple isotopes for a selected file and updates the GUI.

    Steps:
    1. Validate that a file is selected.
    2. Read the spectral data from the file.
    3. Clear any previously detected peaks.
    4. For each channel and isotope, detect peaks based on x-values and y-values using adjust_ROI.
    5. Append detected peaks and update the GUI with peak information.
    6. Display completion message and update the plot based on user selection.
    """

    @staticmethod
    def run_multi_detection(main_window, isotopes):
        if main_window.selected_file is None:
            QMessageBox.warning(main_window, "Error", "No file selected. Please select a file first.")
            return

        file_path = os.path.join(main_window.file_path_label.text(), main_window.selected_file)
        df = pd.read_csv(file_path)
        main_window.detected_peak_list.clear()

        detected_peaks = []

        for isotope in isotopes:
            user_defined_range = None
            for index, row in df.iterrows():
                channel_name = f'Channel_{index}'
                x_values = pd.to_numeric(df.columns, errors='coerce')
                y_values = row.values
                if detected_peaks:
                    last_detected_peak_energy = detected_peaks[-1][1]
                    start_index = np.searchsorted(x_values, last_detected_peak_energy + 1000)
                    mask = np.zeros_like(x_values, dtype=bool)
                    mask[start_index:] = True
                else:
                    mask = MultiISODetector.get_initial_mask(main_window, isotope, x_values)
                # Use a specific method based on isotope
                if isotope == "60Co":
                    found_peak, peak_energy = MultiISODetector.adjust_ROI(main_window, isotope, channel_name, x_values, y_values)
                    if not found_peak:
                        found_peak, peak_energy, user_defined_range = MultiISODetector.prompt_for_new_range_until_peaks_found(
                            main_window, channel_name, x_values, y_values, user_defined_range)
                else:

                    found_peak, peak_energy = MultiISODetector.detect_peaks(main_window, channel_name, x_values, y_values, mask)
                    if not found_peak:
                        found_peak, peak_energy, user_defined_range = MultiISODetector.prompt_for_new_range_until_peaks_found(
                            main_window, channel_name, x_values, y_values, user_defined_range)

                if found_peak:
                    detected_peaks.append((channel_name, peak_energy))

        QMessageBox.information(main_window, "Peak Detection Complete", "All channels have been processed for peaks.")

        if main_window.selected_channel is None or main_window.last_plot_all_channels:
            main_window.plot_all_channels_with_peaks(df, detected_peaks)
        else:
            main_window.plot_multi_peaks()


class PeakTuningDialog(QDialog):
    """
    Initializes a dialog for interactive peak tuning with a plot.

    Parameters:
    - parent: Parent widget.
    - initial_peak_position: Initial x-coordinate of the peak.
    - x_data: X data for plotting the spectrum.
    - y_data: Y data for plotting the spectrum.

    Steps:
    1. Setup the dialog window with a plot of the spectrum and an initial peak position.
    2. Connect interactive events for moving and selecting a peak position.
    """
    def __init__(self, parent=None, initial_peak_position=0.0, x_data=None, y_data=None):
        super().__init__(parent)
        self.setWindowTitle("Select New Peak Position")
        self.layout = QVBoxLayout(self)
        self.figure = plt.Figure(figsize=(12, 9))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.plot(x_data, y_data, label='Spectrum')
        self.ax.axvline(x=initial_peak_position, color='red', label='Initial Peak', linestyle='--')
        self.ax.set_xlabel('Energy (keV)')
        self.ax.set_ylabel('Counts')
        self.ax.legend()
        self.layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)
        self.vertical_line = self.ax.axvline(x=initial_peak_position, color='r')
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_click)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)
        self.new_peak_position = initial_peak_position

    def on_mouse_move(self, event):
        """
        Handles mouse movement within the plot axes to update the vertical line position.

        Parameters:
        - event: Matplotlib event object containing event details.
        """
        if event.inaxes == self.ax:
            self.vertical_line.set_xdata(event.xdata)
            self.canvas.draw()

    def on_mouse_click(self, event):
        """
        Handles mouse button presses within the plot axes to set a new peak position.

        Parameters:
        - event: Matplotlib event object containing event details.

        Steps:
        1. Update the vertical line to the new position.
        2. Confirm the new position with the user through a dialog box.
        3. If confirmed, accept the dialog to return the new position.
        """
        if event.inaxes == self.ax:
            self.new_peak_position = event.xdata
            self.vertical_line.set_xdata(event.xdata)
            self.canvas.draw()
            reply = QMessageBox.question(self, 'Confirm Peak Position',
                                         f"Set new peak position to {self.new_peak_position:.2f} keV?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                self.accept()

    def get_peak_position(self):
        """
        Returns the selected peak position after the dialog is closed.

        Returns:
        - The new peak position as a float.
        """
        return self.new_peak_position
