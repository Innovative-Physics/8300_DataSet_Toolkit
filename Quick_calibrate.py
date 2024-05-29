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
    scaling_factor = known_energy / detected_peak

    # Apply the scaling factor to the columns (assumed to be energy channels)
    original_data = pd.to_numeric(data, errors='coerce')
    scaled_data = original_data * scaling_factor
    
    # Create a new DataFrame with scaled columns
    calibrated_data = data

    return calibrated_data