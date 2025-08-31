from loguru import logger
import subprocess
import sys

from src.app_coordinates.realme_coordinates import Realme7Coordinates
from src.app_coordinates.s24u_coordinates import S24UCoordinates


def get_phone_model():
    """
    Identifies the connected Android device's model name using ADB.
    
    Returns:
        str: The model name of the device (e.g., "RMX2151"), or None if not found.
    """
    try:
        result = subprocess.run(
            "adb shell getprop ro.product.model",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        model = result.stdout.strip()
        logger.info(f"Connected device model identified as: {model}")
        return model
    except FileNotFoundError:
        logger.critical("ADB not found. Please ensure it is installed and in your system's PATH.")
        return None
    except subprocess.CalledProcessError:
        logger.critical("No ADB device found. Please ensure your phone is connected and USB debugging is enabled.")
        return None

def get_device_config(model_name):
    """
    Selects the correct AppCoordinates class based on the detected device model.
    """
    # --- Map ADB model names to your coordinate classes ---
    DEVICE_MAPPING = {
        "RMX2151": Realme7Coordinates,
        "SM-S928B": S24UCoordinates,
    }
    
    config_class = DEVICE_MAPPING.get(model_name)
    if config_class:
        logger.success(f"Found matching configuration for '{model_name}'.")
        return config_class()
    else:
        logger.error(f"No configuration found for model '{model_name}'.")
        logger.error("Please create a new coordinate file for your device and add it to the DEVICE_MAPPING.")
        return None

def get_device_coordinates():
    """
    Main function to get the device coordinates based on the connected phone model.
    
    Returns:
        An instance of the appropriate AppCoordinates subclass, or None if not found.
    """
    # --- NEW: Automatically detect phone and load config ---
    connected_model = get_phone_model()
    if not connected_model:
        logger.error("Could not detect connected phone model.")
        raise

    my_phone_coords = get_device_config(connected_model)
    if not my_phone_coords:
        logger.error(f"Failed to load device configuration for model {connected_model}.")
        raise
    return my_phone_coords
