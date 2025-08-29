import os
import json
from loguru import logger

# --- Caching Class (with Swipe Support) ---
class UICache:
    """Handles loading and saving UI element coordinates and swipe counts to a JSON file."""
    def __init__(self, cache_file='ui_cache.json'):
        self.cache_file = cache_file
        self.locations = {}

    def load(self):
        """Loads coordinates from the JSON cache file if it exists."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.locations = json.load(f)
                logger.success(f"Successfully loaded UI cache from {self.cache_file}")
        except Exception as e:
            logger.error(f"Could not load cache file: {e}")

    def save(self):
        """Saves the current coordinates to the JSON cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.locations, f, indent=4)
            logger.debug(f"Saved UI cache to {self.cache_file}")
        except Exception as e:
            logger.error(f"Could not save cache file: {e}")

    def get(self, name):
        """Gets location data (swipes and coords) for a given name from the cache."""
        return self.locations.get(name)

    def set(self, name, swipe_count, coords):
        """Sets the location data for a given name in the cache."""
        self.locations[name] = {"swipes": swipe_count, "coords": coords}
