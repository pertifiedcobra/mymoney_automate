# Coordinates and configuration for Samsung S24 Ultra device
from src.app_coordinates.base_coordinates import BaseAppCoordinates


# --- App Coordinates & Configuration ---
class S24UCoordinates(BaseAppCoordinates):
    """
    A dedicated class to store all screen coordinates and configuration.
    This makes the script portable to different devices and screen resolutions.
    """
    def __init__(self):
        # --- App Specific Configuration ---
        # CRITICAL: You must find and set the package name for MyMoneyPro.
        # See the README for instructions on how to find this.
        self.phone_name = "Samsung S24 Ultra"
        self.model_name = "SM-S928B"
        self.app_package_name = "com.raha.app.mymoney.pro"

        # --- General Timings ---
        self.SHORT_DELAY = 0.1
        self.LONG_DELAY = 0.6

        # --- Navigation Coordinates ---
        # The main '+' floating action button on the app's home screen to start a new entry.
        self.initiate_new_entry_coords = (1251, 2693)
        # The '✓' checkmark icon at the top right to save an entry.
        self.save_button_coords = (1287, 232)

        # The 'INCOME' tab at the top of the 'Add Transaction' screen.
        self.income_entry_coords = (295, 466)
        # The 'TRANSFER' tab at the top of the 'Add Transaction' screen.
        self.transfer_entry_coords = (1172, 438)

        # --- Main 'Add Expense/Income/Transfer' Screen Buttons ---
        # For Expenses/Incomes, this is the main 'Account' dropdown.
        # For Transfers, this is the 'From Account' dropdown on the left.
        self.account_entry_left_coords = (478, 743)
        # For Transfers, this is the 'To Account' dropdown on the right.
        self.account_entry_right_coords = (1072, 734)
        # The 'Category' dropdown on the right (used for Expenses and Incomes).
        self.category_entry_coords = (1008, 715)
        # The button that shows the date and opens the date picker.
        self.date_picker_entry_coords = (362, 2984)
        # The button that shows the time and opens the time picker.
        self.time_picker_entry_coords = (1014, 2994)
        # The text input field for 'Notes'.
        self.notes_section_coords = (552, 1072)

        # --- Amount Keypad ---
        # The coordinates for each digit on the app's custom on-screen keypad.
        self.keypad_coords = {
            '7': (600, 2000), '8': (900, 2000), '9': (1200, 2000),
            '4': (600, 2250), '5': (900, 2250), '6': (1200, 2250),
            '1': (600, 2500), '2': (900, 2500), '3': (1200, 2500),
            '0': (600, 2750), '.': (900, 2750),
        }
        # The backspace button '⌫' next to the amount display.
        self.backspace_coords = (1247, 1662)

        # --- Date Picker Dialog ---
        # The '<' and '>' arrows to change the month.
        self.date_month_change_coords = {"next": (1100, 1200), "prev": (300, 1200)}
        # A list of the X-coordinates for each day column (Sun, Mon, Tue, etc.).
        self.date_grid_x_coords = [320, 450, 580, 710, 840, 970, 1100]
        # A list of the Y-coordinates for each week row in the calendar.
        self.date_grid_y_coords = [1450, 1610, 1770, 1930, 2090, 2250]
        # The 'OK' button to confirm the date selection.
        self.date_ok_coords = (1030, 2430)

        # --- Time Picker Dialog ---
        # The keyboard icon in the bottom-left of the clock view to switch to text input.
        self.time_keypad_mode_coords = (342, 2257)
        # The hour input field in the text-based time picker.
        self.time_hour_coords = (420, 1750)
        # The minute input field in the text-based time picker.
        self.time_minute_coords = (560, 1750)
        # The dropdown selector for AM/PM in the text-based time picker.
        self.time_ampm_selector_coords = (1080, 1730)
        # The coordinates for the 'AM' and 'PM' options themselves after the dropdown is open.
        self.time_ampm_coords = {'AM': (930, 1755), 'PM': (930, 1925)}
        # The 'OK' button to confirm the time selection.
        self.time_ok_coords = (1035, 2040)

        # --- Scrolling / Swiping ---
        # Defines a swipe action from a start (x,y) to an end (x,y) with a duration (ms).
        self.swipe_coords = (500, 1800, 500, 800, 300)
        
        # --- OCR Configuration ---
        # Number of pixels to crop from the left of the screen on the 'Accounts' page to ignore logos.
        self.account_list_crop_pixels = 300
        # Number of characters to use when searching for long category names that get truncated with '...'.
        self.category_name_crop = 10
