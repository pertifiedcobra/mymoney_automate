# Coordinates and configuration for Realme 7 device
from src.app_coordinates.base_coordinates import BaseAppCoordinates

# --- App Coordinates & Configuration ---
class Realme7Coordinates(BaseAppCoordinates):
    """
    A dedicated class to store all screen coordinates and configuration.
    This makes the script portable to different devices and screen resolutions.
    """
    def __init__(self):
        # --- App Specific Configuration ---
        # CRITICAL: You must find and set the package name for MyMoneyPro.
        # See the README for instructions on how to find this.
        self.phone_name = "Realme 7"
        self.model_name = "VKCYBQKFBUGEH6CI"
        self.app_package_name = "com.raha.app.mymoney.pro"

        # --- General Timings ---
        self.SHORT_DELAY = 0.1
        self.LONG_DELAY = 0.6

        # --- Navigation Coordinates ---
        # The main '+' floating action button on the app's home screen to start a new entry.
        self.initiate_new_entry_coords = (910, 1970)
        # The '✓' checkmark icon at the top right to save an entry.
        self.save_button_coords = (950, 150)

        # The 'INCOME' tab at the top of the 'Add Transaction' screen.
        self.income_entry_coords = (174, 380)
        # The 'TRANSFER' tab at the top of the 'Add Transaction' screen.
        self.transfer_entry_coords = (853, 382)

        # --- Main 'Add Expense/Income/Transfer' Screen Buttons ---
        # For Expenses/Incomes, this is the main 'Account' dropdown.
        # For Transfers, this is the 'From Account' dropdown on the left.
        self.account_entry_left_coords = (300, 650)
        # For Transfers, this is the 'To Account' dropdown on the right.
        self.account_entry_right_coords = (800, 650)
        # The 'Category' dropdown on the right (used for Expenses and Incomes).
        self.category_entry_coords = (800, 650)
        # The button that shows the date and opens the date picker.
        self.date_picker_entry_coords = (400, 2200)
        # The button that shows the time and opens the time picker.
        self.time_picker_entry_coords = (750, 2200)
        # The text input field for 'Notes'.
        self.notes_section_coords = (500, 950)

        # --- Amount Keypad ---
        # The coordinates for each digit on the app's custom on-screen keypad.
        self.keypad_coords = {
            '7': (450, 1450), '8': (650, 1450), '9': (950, 1450),
            '4': (450, 1650), '5': (650, 1650), '6': (950, 1650),
            '1': (450, 1850), '2': (650, 1850), '3': (950, 1850),
            '0': (450, 2069), '.': (650, 2039),
        }
        # The backspace button '⌫' next to the amount display.
        self.backspace_coords = (950, 1250)

        # --- Date Picker Dialog ---
        # The '<' and '>' arrows to change the month.
        self.date_month_change_coords = {"next": (867, 860), "prev": (216, 860)}
        # A list of the X-coordinates for each day column (Sun, Mon, Tue, etc.).
        self.date_grid_x_coords = [230, 330, 430, 530, 630, 730, 830]
        # A list of the Y-coordinates for each week row in the calendar.
        self.date_grid_y_coords = [1100, 1220, 1340, 1460, 1580, 1700]
        # The 'OK' button to confirm the date selection.
        self.date_ok_coords = (810, 1885)

        # --- Time Picker Dialog ---
        # The keyboard icon in the bottom-left of the clock view to switch to text input.
        self.time_keypad_mode_coords = (209, 1731)
        # The hour input field in the text-based time picker.
        self.time_hour_coords = (256, 1026)
        # The minute input field in the text-based time picker.
        self.time_minute_coords = (426, 1026)
        # The dropdown selector for AM/PM in the text-based time picker.
        self.time_ampm_selector_coords = (838, 1299)
        # The coordinates for the 'AM' and 'PM' options themselves after the dropdown is open.
        self.time_ampm_coords = {'AM': (705, 1333), 'PM': (700, 1457)}
        # The 'OK' button to confirm the time selection.
        self.time_ok_coords = (852, 1542)

        # --- Scrolling / Swiping ---
        # Defines a swipe action from a start (x,y) to an end (x,y) with a duration (ms).
        self.swipe_coords = (500, 1800, 500, 800, 300)
        
        # --- OCR Configuration ---
        # Number of pixels to crop from the left of the screen on the 'Accounts' page to ignore logos.
        self.account_list_crop_pixels = 240
        # Number of characters to use when searching for long category names that get truncated with '...'.
        self.category_name_crop = 10
