# Coordinates and configuration for Realme 7 device
# --- App Coordinates & Configuration ---
class AppCoordinates:
    """
    A dedicated class to store all screen coordinates and configuration.
    This makes the script portable to different devices and screen resolutions.
    """
    def __init__(self):
        # --- App Specific Configuration ---
        # CRITICAL: You must find and set the package name for MyMoneyPro.
        # See the README for instructions on how to find this.
        self.app_package_name = "com.raha.app.mymoney.pro"

        # --- General Timings ---
        self.SHORT_DELAY = 0.1
        self.LONG_DELAY = 0.6

        # --- Navigation Coordinates ---
        self.initiate_new_entry_coords = (910, 1970)
        self.save_button_coords = (950, 150)

        self.income_entry_coords = (174, 380)
        self.transfer_entry_coords = (853, 382)

        # --- Main 'Add Expense' Screen Buttons ---
        self.account_entry_left_coords = (300, 650)
        self.account_entry_right_coords = (800, 650)
        self.category_entry_coords = (800, 650)
        self.date_picker_entry_coords = (400, 2200)
        self.time_picker_entry_coords = (750, 2200)
        self.notes_section_coords = (500, 950)

        # --- Amount Keypad ---
        self.keypad_coords = {
            '7': (450, 1450), '8': (650, 1450), '9': (950, 1450),
            '4': (450, 1650), '5': (650, 1650), '6': (950, 1650),
            '1': (450, 1850), '2': (650, 1850), '3': (950, 1850),
            '0': (450, 2069), '.': (650, 2039),
        }
        self.backspace_coords = (950, 1250)

        # --- Date Picker Dialog ---
        self.date_month_change_coords = {"next": (867, 860), "prev": (216, 860)}
        self.date_grid_x_coords = [230, 330, 430, 530, 630, 730, 830]
        self.date_grid_y_coords = [1100, 1220, 1340, 1460, 1580, 1700]
        self.date_ok_coords = (810, 1885)

        # --- Time Picker Dialog ---
        self.time_keypad_mode_coords = (209, 1731)
        self.time_hour_coords = (256, 1026)
        self.time_minute_coords = (426, 1026)
        self.time_ampm_selector_coords = (838, 1299)
        self.time_ampm_coords = {'AM': (705, 1333), 'PM': (700, 1457)}
        self.time_ok_coords = (852, 1542)

        # --- Scrolling / Swiping ---
        self.swipe_coords = (500, 1800, 500, 800, 300)
        
        # --- OCR Configuration ---
        self.account_list_crop_pixels = 240
        self.category_name_crop = 10  # Crop length for category names that are too long
