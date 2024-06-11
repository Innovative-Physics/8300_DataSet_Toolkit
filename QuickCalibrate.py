import pandas as pd 

def quick_calibrate(data, detected_peak, known_energy):
    """
    Perform quick calibration of the spectra based on a detected peak and known energy.

    Args:
        df (pd.DataFrame): The original dataframe containing the spectra data.
        detected_peak (float): The detected peak position.
        known_energy (float): The known energy corresponding to the detected peak.

    Returns:
        pd.DataFrame: The calibrated dataframe with the x-axis scaled.
    """
    # Calculate the scaling factor
    scaling_factor = detected_peak / known_energy

    # Scale the index (x-axis) values
    calibrated_data = data.copy()
    calibrated_data.index = calibrated_data.index * scaling_factor

    return calibrated_data