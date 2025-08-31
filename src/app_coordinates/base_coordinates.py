class BaseAppCoordinates:
    """
    A base class defining the required structure for all device-specific coordinates.
    All device configuration classes should inherit from this class.
    """
    def __init__(self):
        # --- App Specific Configuration ---
        self.phone_name = "Generic Phone"
        self.model_name = "GenericModel"
        self.app_package_name = "com.raha.app.mymoney.pro"

        # --- General Timings ---
        self.SHORT_DELAY = 0.1
        self.LONG_DELAY = 0.6

        # --- Navigation Coordinates ---
        self.initiate_new_entry_coords = None
        self.save_button_coords = None
        self.income_entry_coords = None
        self.transfer_entry_coords = None

        # --- Main 'Add Expense' Screen Buttons ---
        self.account_entry_left_coords = None
        self.account_entry_right_coords = None
        self.category_entry_coords = None
        self.date_picker_entry_coords = None
        self.time_picker_entry_coords = None
        self.notes_section_coords = None

        # --- Amount Keypad ---
        self.keypad_coords = {}
        self.backspace_coords = None

        # --- Date Picker Dialog ---
        self.date_month_change_coords = {}
        self.date_grid_x_coords = []
        self.date_grid_y_coords = []
        self.date_ok_coords = None

        # --- Time Picker Dialog ---
        self.time_keypad_mode_coords = None
        self.time_hour_coords = None
        self.time_minute_coords = None
        self.time_ampm_selector_coords = None
        self.time_ampm_coords = {}
        self.time_ok_coords = None

        # --- Scrolling / Swiping ---
        self.swipe_coords = None
        
        # --- OCR Configuration ---
        self.account_list_crop_pixels = 0
        self.category_name_crop = 10
