import os
import sys
import time
import subprocess
from datetime import datetime
import calendar
import re
import json
from PIL import Image
import pytesseract
from loguru import logger
import cv2
import pprint
import pandas as pd
import numpy as np

from account_categories_list import accounts_list, entry_type, income_categories_list, expense_categories_list

# --- Configuration Section ---
# If Tesseract is not in your system's PATH, uncomment and set the path below.
# This tells the script where to find the Tesseract OCR engine.
# Example for Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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


class MyMoneyProAutomator:
    """
    A class to automate expense entry in the MyMoneyPro app using ADB and OCR.
    """
    def __init__(self, coords: AppCoordinates):
        self.coords = coords
        self.calendar = calendar.Calendar(firstweekday=calendar.SUNDAY)
        # Initialize and load the UI cache
        self.cache = UICache()
        self.cache.load()

    def _execute_adb(self, command, check=True):
        """Executes a given ADB command."""
        return subprocess.run(f"adb shell {command}", shell=True, check=check, capture_output=True, text=True)

    def _check_app_focus(self):
        """
        SECURITY CHECK: Ensures the target app is in the foreground before performing any action.
        If the wrong app is open, it aborts the script to prevent unintended taps.
        """
        try:
            # This command gets information about the currently focused window
            # result = self._execute_adb("dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")
            result = self._execute_adb('dumpsys window | findstr "mCurrentFocus mFocusedApp"')
            focused_app_info = result.stdout.strip()
            
            if self.coords.app_package_name not in focused_app_info:
                logger.critical("!!! SAFETY ABORT !!!")
                logger.critical(f"The target app '{self.coords.app_package_name}' is NOT in the foreground.")
                logger.critical(f"Currently focused app appears to be: {focused_app_info}")
                logger.critical("Exiting to prevent unintended actions.")
                sys.exit(1) # Exit the script with an error code
            
            logger.trace("App focus check passed.")
        except Exception as e:
            logger.error(f"Could not check app focus. Aborting for safety. Error: {e}")
            sys.exit(1)

    def _tap(self, x, y, purpose="No purpose specified"):
        self._check_app_focus() # Security check before every tap
        logger.debug(f"Tapping for '{purpose}' at ({x}, {y})")
        self._execute_adb(f"input tap {x} {y}")
        time.sleep(self.coords.SHORT_DELAY)

    def _type_text(self, text):
        self._check_app_focus() # Security check
        # Ensure the input is a string
        text_to_type = str(text)

        # Escape characters that have special meaning inside double quotes for a shell
        # This makes the command more robust for a wider range of text.
        formatted_text = text_to_type.replace('"', '\\"')
        formatted_text = formatted_text.replace("'", "\\'")
        formatted_text = formatted_text.replace('$', '\\$')
        
        # Finally, replace spaces for adb compatibility
        formatted_text = formatted_text.replace(" ", "%s")
        
        logger.debug(f"Typing text: '{text_to_type}'")
        # Use double quotes to wrap the text, which handles single quotes gracefully.
        self._execute_adb(f'input text "{formatted_text}"')
        time.sleep(self.coords.SHORT_DELAY)

    def _press_key(self, keycode):
        self._check_app_focus() # Security check
        logger.debug(f"Pressing keycode: {keycode}")
        self._execute_adb(f"input keyevent {keycode}")
        time.sleep(0.1)

    def _swipe(self, x1, y1, x2, y2, duration):
        self._check_app_focus() # Security check
        logger.info("Swiping screen to scroll...")
        self._execute_adb(f"input swipe {x1} {y1} {x2} {y2} {duration}")
        time.sleep(self.coords.LONG_DELAY)

    def _find_and_tap_text(self, target_text, screen_type, max_swipes=5):
        """
        Finds an item by its text. First checks a local cache for the location.
        If not found, falls back to OCR and saves the new location to the cache.
        """
        # --- Step 1: Check Cache First (with swipe support) ---
        cached_location = self.cache.get(target_text)
        if cached_location:
            logger.success(f"Found '{target_text}' in cache.")
            swipes_needed = cached_location.get("swipes", 0)
            coords = cached_location.get("coords")
            if swipes_needed > 0:
                logger.info(f"Performing {swipes_needed} cached swipe(s)...")
                for _ in range(swipes_needed):
                    self._swipe(*self.coords.swipe_coords)
            
            logger.info(f"Tapping cached coordinates for '{target_text}'.")
            self._tap(coords[0], coords[1], purpose=f"Select cached item '{target_text}'")
            return True

        logger.warning(f"'{target_text}' not in cache. Starting OCR fallback...")
        screenshot_path_phone = "/sdcard/screen.png"
        screenshot_path_local = "screen.png"

        for i in range(max_swipes):
            try:
                self._check_app_focus() # Check focus before taking a screenshot
                logger.debug(f"Scan attempt {i+1}/{max_swipes} for '{target_text}'")
                self._execute_adb(f"screencap -p {screenshot_path_phone}")
                subprocess.run(f"adb pull {screenshot_path_phone} {screenshot_path_local}", shell=True, check=True, capture_output=True)
                
                # --- Image Pre-processing for better OCR accuracy ---
                img = cv2.imread(screenshot_path_local)

                crop_amount = 0
                if screen_type == 'account':
                    logger.debug("Cropping image for account screen to remove logos.")
                    crop_amount = self.coords.account_list_crop_pixels
                    img = img[:, crop_amount:]

                # --- Convert to grayscale for better OCR accuracy ---
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # Apply a binary threshold to get a black and white image
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
                
                # Configure Tesseract to use a specific engine mode and page segmentation
                tesseract_config = r'--oem 3 --psm 6'
                ocr_data = pytesseract.image_to_data(thresh, config=tesseract_config, output_type=pytesseract.Output.DICT)
                
                clean_words_data = []
                # logger.debug("--- Raw OCR Word Detection & Filtering ---")
                for j in range(len(ocr_data['text'])):
                    if int(ocr_data['conf'][j]) > 40:
                        word = ocr_data['text'][j].strip()
                        if (
                            not word or
                            re.search(r'\d', word) or
                            word in ['©', '—', '₹', '%', '|', '.', ','] or
                            re.search(r'\s+[.,]\s+', word)
                        ):
                            continue
                        clean_words_data.append({
                            'text': word, 'left': ocr_data['left'][j], 'top': ocr_data['top'][j],
                            'width': ocr_data['width'][j], 'height': ocr_data['height'][j]
                        })
                logger.debug(f"{[d['text'] for d in clean_words_data]}")
                searchable_text = " ".join([d['text'] for d in clean_words_data])
                logger.debug(f"Searchable Text Block: '{searchable_text}'")

                if target_text.lower() in searchable_text.lower():
                    logger.debug(f"Found '{target_text}' in the OCR text block.")
                    target_words = target_text.split()
                    for k in range(len(clean_words_data) - len(target_words) + 1):
                        phrase_to_check = " ".join([clean_words_data[k+l]['text'] for l in range(len(target_words))])
                        # logger.debug(f"Checking phrase: '{phrase_to_check}' against target '{target_text}'")
                        if target_text.lower() in phrase_to_check.lower():
                            first_word_data = clean_words_data[k]
                            x, y, w, h = first_word_data['left'], first_word_data['top'], first_word_data['width'], first_word_data['height']
                            center_x = (x + w // 2) + crop_amount
                            center_y = y + h // 2
                            
                            logger.success(f"Found match '{phrase_to_check}' via OCR after {i} swipe(s). Tapping and caching location.")
                            # --- Step 2: Cache the newly found location with swipe count ---
                            self.cache.set(target_text, i, (center_x, center_y))
                            self.cache.save()
                            
                            self._tap(center_x, center_y, purpose=f"Select item '{phrase_to_check}'")
                            return True
                
                logger.warning(f"'{target_text}' not found on screen. Swiping...")
                self._swipe(*self.coords.swipe_coords)

            except Exception as e:
                logger.exception(f"An error occurred during OCR/screenshot process")
                return False
            finally:
                if os.path.exists(screenshot_path_local):
                    os.remove(screenshot_path_local)
                self._execute_adb(f"rm {screenshot_path_phone}", check=False)
                # logger.debug("Cleaned up screenshot files.")
        
        logger.error(f"Could not find '{target_text}' after {max_swipes} swipes.")
        return False

    def select_account(self, account_name, left_or_right='left'):
        """
        Selects an account from the list.
        It first opens the account selection screen, then uses the intelligent
        find_and_tap_text method to locate and tap the correct account name.
        """
        logger.info(f"--- Selecting Account: {account_name} ---")
        if left_or_right.lower() == 'left':
            self._tap(self.coords.account_entry_left_coords[0], self.coords.account_entry_left_coords[1], purpose="Open account list(left side)")
        else:
            self._tap(self.coords.account_entry_right_coords[0], self.coords.account_entry_right_coords[1], purpose="Open account list (right side)")
        return self._find_and_tap_text(account_name, screen_type='account')

    def select_category(self, category_name):
        """
        Selects a category from the grid.
        It first opens the category selection screen, then uses the intelligent
        find_and_tap_text method to locate and tap the correct category name.
        """
        logger.info(f"--- Selecting Category: {category_name} ---")
        category_name = category_name[:self.coords.category_name_crop]  # Ensure the category name is not too long
        self._tap(self.coords.category_entry_coords[0], self.coords.category_entry_coords[1], purpose="Open category list")
        return self._find_and_tap_text(category_name, screen_type='category')

    def enter_amount(self, amount_str):
        """
        Enters the transaction amount using the on-screen custom keypad.
        It iterates through each character of the amount string and taps the
        corresponding key on the screen.
        It also removes trailing '.0' from whole numbers.
        """
        # Convert amount to string and check if it's a whole number ending in .0
        amount_to_type = str(amount_str)
        if amount_to_type.endswith(".0"):
            amount_to_type = amount_to_type[:-2] # Remove the ".0"

        logger.info(f"--- Entering Amount: {amount_to_type} (Original: {amount_str}) ---")
        for char in amount_to_type:
            if char in self.coords.keypad_coords:
                self._tap(self.coords.keypad_coords[char][0], self.coords.keypad_coords[char][1], purpose=f"Enter amount digit '{char}'")

    def set_date(self, target_date: datetime):
        """
        Sets the date using the app's date picker dialog.

        This method is designed to be robust against the changing layout of the
        calendar grid from month to month. It works by programmatically
        calculating the correct position of the target day rather than relying
        on hardcoded coordinates for each day.

        Args:
            target_date (datetime): The specific date to be selected.
        """
        logger.info(f"--- Setting Date to: {target_date.strftime('%Y-%m-%d')} ---")
        # 1. Open the date picker dialog.
        self._tap(self.coords.date_picker_entry_coords[0], self.coords.date_picker_entry_coords[1], purpose="Open date picker")
        
        # 2. Navigate to the correct month and year by tapping the '<' or '>' arrows.
        # It calculates how many months to move forward or backward from the current view.
        self._current_picker_date = datetime.now()
        month_diff = (target_date.year - self._current_picker_date.year) * 12 + (target_date.month - self._current_picker_date.month)
        logger.debug(f"Current Picker Date: {self._current_picker_date}, Target Date: {target_date}, Month Difference: {month_diff}")
        if month_diff > 0:
            for _ in range(month_diff): self._tap(self.coords.date_month_change_coords['next'][0], self.coords.date_month_change_coords['next'][1], purpose="Next month")
        elif month_diff < 0:
            for _ in range(abs(month_diff)): self._tap(self.coords.date_month_change_coords['prev'][0], self.coords.date_month_change_coords['prev'][1], purpose="Previous month")
        
        # 3. Dynamically find the position of the target day.
        # It builds a virtual calendar for the target month and finds the row/column of the target day.
        month_calendar = self.calendar.monthdayscalendar(target_date.year, target_date.month)
        for week_index, week in enumerate(month_calendar):
            if target_date.day in week:
                # 4. Map the row/column to the actual screen coordinates and tap.
                day_index = week.index(target_date.day)
                self._tap(self.coords.date_grid_x_coords[day_index], self.coords.date_grid_y_coords[week_index], purpose=f"Select day {target_date.day}")
                break
        
        # 5. Finalize by tapping the 'OK' button.
        self._tap(self.coords.date_ok_coords[0], self.coords.date_ok_coords[1], purpose="Confirm date (OK)")

    def set_time(self, target_time: datetime):
        """
        Sets the time using the app's time picker dialog.

        This method smartly switches the time picker to its keyboard input mode,
        which is more reliable to automate than the clock face. It handles
        entering the hour, minute, and selecting AM/PM.

        Args:
            target_time (datetime): The specific time to be selected.
        """
        logger.info(f"--- Setting Time to: {target_time.strftime('%I:%M %p')} ---")
        # 1. Open the time picker dialog.
        self._tap(self.coords.time_picker_entry_coords[0], self.coords.time_picker_entry_coords[1], purpose="Open time picker")
        
        # 2. Switch to the more reliable keyboard input mode.
        self._tap(self.coords.time_keypad_mode_coords[0], self.coords.time_keypad_mode_coords[1], purpose="Switch to time keypad mode")

        # 3. Select AM or PM.
        target_ampm = target_time.strftime('%p')
        logger.debug(f"Attempting to select {target_ampm}")
        self._tap(self.coords.time_ampm_selector_coords[0], self.coords.time_ampm_selector_coords[1], purpose="Open AM/PM selector")
        self._tap(self.coords.time_ampm_coords[target_ampm][0], self.coords.time_ampm_coords[target_ampm][1], purpose=f"Select {target_ampm}")
        
        # 4. Enter the hour.
        self._tap(self.coords.time_hour_coords[0], self.coords.time_hour_coords[1], purpose="Tap hour field")
        self._type_text(target_time.strftime('%I')) # %I is for 12-hour format
        
        # 5. Enter the minute.
        self._tap(self.coords.time_minute_coords[0], self.coords.time_minute_coords[1], purpose="Tap minute field")
        self._type_text(target_time.strftime('%M'))
        
        # 6. Finalize by tapping the 'OK' button.
        self._tap(self.coords.time_ok_coords[0], self.coords.time_ok_coords[1], purpose="Confirm time (OK)")

    def enter_notes(self, notes_text):
        """
        Enters the transaction notes into the appropriate text field.
        """
        logger.info(f"--- Entering Notes: {notes_text} ---")
        self._tap(self.coords.notes_section_coords[0], self.coords.notes_section_coords[1], purpose="Enter notes section")
        self._type_text(notes_text)

    def add_entry(self, expense_data, type):
        """
        Orchestrates the entire process of adding a single expense.

        This is the main workflow method that calls all other helper methods in
        the correct sequence to perform a complete expense/income entry, from navigating
        to the page to filling all fields and saving.

        Args:
            expense_data (dict): A dictionary containing all necessary details
                                 for a single transaction.

        Returns:
            bool: True if the expense was added successfully, False otherwise.
        """
        logger.info(f"--- Adding {expense_data.get('type')}: {expense_data['notes']} ---")
        try:
            # 1. Fill in all the details in the specified order.
            # If any step fails, it will return False and stop this transaction.
            if not self.select_account(expense_data['account'], left_or_right='left'): return False
            if type.lower() == 'income' or type.lower() == 'expense':
                if not self.select_category(expense_data['category']): return False
            elif type.lower() == 'transfer':
                if not self.select_account(expense_data['category'], left_or_right='right'): return False  # It's actual value will be an Account in case of Transfer

            self.enter_amount(expense_data['amount'])
            self.set_date(expense_data['datetime'])
            self.set_time(expense_data['datetime'])
            self.enter_notes(expense_data['notes'])
            
            # 2. Save the expense and wait for the app to return to the main screen.
            logger.info("--- Saving Expense ---")
            self._tap(self.coords.save_button_coords[0], self.coords.save_button_coords[1], purpose="Save expense")
            time.sleep(self.coords.LONG_DELAY)
            
            return True
        except Exception as e:
            logger.exception("!!! An unrecoverable error occurred during expense entry !!!")
            logger.error("You may need to manually press CANCEL on the phone to reset the app state.")
            return False
    
    def begin_entry(self, expense_data):
        """
        Starts the process of adding a new expense.
        This method is called to ensure the app is ready for a new entry.
        It can be used to reset the app state if needed.
        """
        self._check_app_focus() # Security check before every tap
        start_time = time.time()
        logger.info(f"\n>>> PROCESSING ENTRY: {expense_data['notes']} <<<")
        try:
            # 1. Start from the main screen and tap the button to add a new entry.
            logger.info("--- Navigating to Add Expense screen ---")
            self._tap(self.coords.initiate_new_entry_coords[0], self.coords.initiate_new_entry_coords[1], purpose="Initiate new expense entry")
            time.sleep(self.coords.LONG_DELAY)

            # 2. Check if the entry is an Income or Transfer and navigate accordingly.
            if expense_data.get('type').lower() == 'income':
                self._tap(self.coords.income_entry_coords[0], self.coords.income_entry_coords[1], purpose="Select Income Entry")
            elif expense_data.get('type').lower() == 'transfer':
                self._tap(self.coords.transfer_entry_coords[0], self.coords.transfer_entry_coords[1], purpose="Select Transfer Entry")
            
            # 3. Now we are on the appropriate Income/Expense/Transfer screen, ready to fill in details.
            success = self.add_entry(expense_data, type=expense_data.get('type', 'expense'))
            
            logger.success(">>> SUCCESSFULLY ADDED ENTRY! <<<")
            elapsed_time = time.time() - start_time
            logger.info(f"Time taken for this transaction: {elapsed_time:.2f} seconds")

            return success
        except Exception as e:
            logger.exception("An error occurred while processing the entry.")
            logger.error("You may need to manually press CANCEL on the phone to reset the app state.")
            return False
    
def load_transactions_from_excel(file_path):
    """
    Loads transactions from a processed Excel file.
    Only loads rows where the 'Status' is 'Pending'.
    """
    try:
        df = pd.read_excel(file_path)
        df.columns = [col.lower() for col in df.columns]  # Make all column names lower case
        logger.info(f"Successfully loaded '{file_path}'.")
        
        # Filter for pending transactions
        pending_df = df[df['status'].str.lower() == 'pending'].copy()
        # --- NEW: Add original index to track rows for updating ---
        pending_df['original_index'] = pending_df.index
        logger.info(f"Found {len(pending_df)} pending transactions to process.")

        # Convert 'Datetime' string back to datetime object
        pending_df['datetime'] = pd.to_datetime(pending_df['datetime'], format='%Y-%m-%d %I:%M %p')
        
        # Convert DataFrame to a list of dictionaries
        return pending_df.to_dict('records')

    except FileNotFoundError:
        logger.error(f"Input Excel file not found at: {file_path}")
        return []
    except Exception as e:
        logger.exception(f"An error occurred while loading the Excel file.")
        return []

def load_sample_transactions():
        """
        Loads a sample set of transactions for testing purposes.
        This is useful for quick testing without needing an Excel file.
        """
        transactions_to_add = [
            {
                'type': 'Expense',
                'account': 'Infinity Tata Neu CC',
                'category': 'Vacation',
                'amount': 1200,
                'notes': 'Trial 1',
                'datetime': datetime(2025, 8, 1, 8, 30),
            },
            {
                'type': 'Transfer',
                'account': 'Infinity Tata Neu CC',
                'category': 'Splitwise',  # In case of Transfer, this is the other account
                'amount': 1200,
                'notes': 'Trial 3',
                'datetime': datetime(2025, 8, 9, 19, 30),
            },
            {
                'type': 'Income',
                'account': 'Infinity Tata Neu CC',
                'category': 'Salary',
                'amount': 1200,
                'notes': 'Trial 3',
                'datetime': datetime(2025, 8, 3, 1, 30),
            },
            {
                'type': 'Expense',
                'account': 'Splitwise',
                'category': 'Transportation',
                'amount': 1200,
                'notes': 'Trial 1',
                'datetime': datetime.strptime("2025-08-25 08:45 PM", "%Y-%m-%d %I:%M %p"),
            },
            {
                'type': 'Expense',
                'account': 'HSBC CC',
                'category': 'Vacation',
                'amount': 654.78,
                'notes': 'Trial 4',
                'datetime': datetime.strptime("2025-08-25 04:45 AM", "%Y-%m-%d %I:%M %p"),
            },
            {
                'type': 'Expense',
                'account': 'Cash',
                'category': 'Tax',
                'amount': 1800.65,
                'notes': 'Trial - Flight',
                'datetime': datetime(2025, 8, 2, 18, 30),
            },
            {
                'type': 'Expense',
                'account': 'SBI Elite CC',
                'category': 'Transportation',
                'amount': 123879.23,
                'notes': 'Trial - Flight',
                'datetime': datetime(2025, 8, 1, 8, 30),
            },
        ]
        return transactions_to_add

def serialize_datetimes(transactions):
    for tx in transactions:
        for k, v in tx.items():
            if isinstance(v, datetime):
                tx[k] = v.strftime("%Y-%m-%d %I:%M %p")
    return transactions

def validate_transactions(transactions):
    """
    Validates the transactions to ensure they have all required fields.
    Returns True if all transactions are valid, otherwise returns False.
    """
    required_fields = ['account', 'category', 'amount', 'notes', 'datetime']
    for tx in transactions:
        if not all(field in tx for field in required_fields):
            logger.error(f"Transaction missing required fields: {tx} | Required fields: {required_fields}")
            return False
        if not isinstance(tx['amount'], (int, float)):
            logger.error(f"Transaction amount is not a number: {tx['amount']} | It's type is {type(tx['amount'])}")
            return False
        if not isinstance(tx['datetime'], datetime):
            logger.error(f"Transaction datetime is not a valid datetime object: {tx['datetime']} | It's type is {type(tx['datetime'])}")
            return False
        if not isinstance(tx['notes'], str):
            logger.warning(f"Transaction notes field is not a string (found {type(tx['notes'])}). Converting it. Transaction: {tx}")
            tx['notes'] = str(tx['notes']) # Attempt to convert it to a string
        if tx.get('type', 'Expense') not in entry_type:
            logger.error(f"Transaction type '{tx.get('type', 'expense')}' is not valid. Must be one of {entry_type}.")
            return False
        if tx['account'] not in accounts_list:
            logger.error(f"Transaction account '{tx['account']}' is not in the accounts list.")
            return False
        if tx['type'].lower() == 'transfer':
            if tx['category'] not in accounts_list:
                # For Transfer type, category must be in accounts_list
                logger.error(f"Transaction category '{tx['category']}' is not in the accounts list for transfer type.")
                return False
            if tx['account'] == tx['category']:
                # For Transfer type, account and category must not be the same
                logger.error(f"Transaction account '{tx['account']}' and category '{tx['category']}' cannot be the same for transfer type.")
                return False
        if tx['type'].lower() == 'income' and tx['category'] not in income_categories_list:
            # For Income types, category must be in income categories_list
            logger.error(f"Transaction category '{tx['category']}' is not in the income categories list.")
            return False
        if tx['type'].lower() == 'expense' and tx['category'] not in expense_categories_list:
            # For Expense types, category must be in expense categories_list
            logger.error(f"Transaction category '{tx['category']}' is not in the expense categories list.")
            return False
        
    logger.info("All transactions are valid.")
    return True

def calculate_and_print_net_diffs(transactions):
    """
    Calculates and prints the net change for each account in the transaction list.
    This provides a summary for the user to verify before the automation starts.
    """
    net_diffs = {}
    net_credit = {}
    net_debit = {}
    for tx in transactions:
        tx_type = tx.get('type', 'expense').lower()
        amount = tx['amount']
        account = tx['account']
        
        if tx_type == 'income':
            net_diffs[account] = net_diffs.get(account, 0) + amount
            net_credit[account] = net_credit.get(account, 0) + amount
        elif tx_type == 'expense':
            net_diffs[account] = net_diffs.get(account, 0) - amount
            net_debit[account] = net_debit.get(account, 0) + amount
        elif tx_type == 'transfer':
            destination_account = tx['category']
            # Subtract from the source account
            net_diffs[account] = net_diffs.get(account, 0) - amount
            net_debit[account] = net_debit.get(account, 0) + amount
            # Add to the destination account
            net_diffs[destination_account] = net_diffs.get(destination_account, 0) + amount
            net_credit[destination_account] = net_credit.get(destination_account, 0) + amount

    logger.info("="*50)
    logger.info("PRE-RUN VERIFICATION: EXPECTED NET CHANGES")
    logger.info("="*50)
    if not net_diffs:
        logger.info("No transactions to process.")
    else:
        for account, diff in net_diffs.items():
            # Format the number with commas and two decimal places
            formatted_diff = f"{diff:,.2f}"
            logger.info(f"{account}: {formatted_diff}")
            logger.debug(f"  (Total Credit: {net_credit.get(account, 0):,.2f}, Total Debit: {net_debit.get(account, 0):,.2f})")
    logger.info("="*50)


if __name__ == '__main__':
    # Configure Loguru for real-time, debug-level logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    my_phone_coords = AppCoordinates()

    # --- Load transactions from Excel ---
    input_excel_file = input("Please enter the full path to your statement .xlsx file: ")
    # Below is sample path for testing
    # input_excel_file = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Statements\\Automated\\04-08-2025\\sample_target_source.xlsx"  # Sample Source For Testing
    # input_excel_file = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Statements\Automated\\04-08-2025\\transactions_source.xlsx"
    # # --- Automatically clean the path copied from Windows Explorer ---
    input_excel_file = input_excel_file.strip()
    input_excel_file = input_excel_file.strip('"')

    # --- NEW: Read the main DataFrame once ---
    try:
        main_df = pd.read_excel(input_excel_file)
        main_df.columns = [col.lower() for col in main_df.columns]
    except FileNotFoundError:
        logger.error(f"Input Excel file not found at: {input_excel_file}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Failed to read the main Excel file.")
        sys.exit(1)

    # transactions_to_add = load_sample_transactions()  # For testing purposes, you can use this instead
    transactions_to_add = load_transactions_from_excel(input_excel_file)

    if not validate_transactions(transactions_to_add):
        logger.error("Validation failed for one or more transactions. Please check the logs for details.")
        sys.exit(1)
    
    calculate_and_print_net_diffs(transactions_to_add)
    
    # logger.debug(f"Type: {transactions_to_add.type()}")
    # logger.debug(f"{[transaction for transaction in transactions_to_add]}")  # Log the loaded transactions for debugging
    # transactions_to_add_datetime_serialized = serialize_datetimes(transactions_to_add)
    # pprint.pprint(transactions_to_add_datetime_serialized)

    if not transactions_to_add:
        logger.warning("No pending transactions found in the Excel file. Exiting.")
        sys.exit(0)
    
    automator = MyMoneyProAutomator(coords=my_phone_coords)
    # TODO: Remove decimal ".0" - Ex - make "1200.0" to "1200"
    # TODO: Include Mechanism to mark the transactions as 'Done' in the Excel file after successful entry

    logger.info("="*50)
    logger.info("Starting MyMoneyPro Automation...")
    logger.info("Please ensure your phone is connected, unlocked, and on its MAIN screen.")
    # --- User confirmation before starting ---
    input("Press Enter to begin...")
    for i in range (3, 0, -1):
        logger.info(f"Starting in {i} seconds...")
        time.sleep(1)
    logger.info("="*50)

    for transaction in transactions_to_add:
        success = automator.begin_entry(transaction)
        if success:
            logger.success(f"MARKING '{transaction['notes']}' as Done.")
            # --- NEW: Update the status in the main DataFrame ---
            original_index = transaction['original_index']
            main_df.loc[original_index, 'status'] = 'Added'
        else:
            logger.error(f"STOPPING SCRIPT due to failure on '{transaction['notes']}'.")
            break
        time.sleep(my_phone_coords.SHORT_DELAY)
    
    # --- NEW: Save the updated DataFrame back to the Excel file ---
    try:
        logger.info("Saving updated statuses back to the Excel file...")
        main_df.to_excel(input_excel_file, index=False)
        logger.success("Successfully saved the updated Excel file.")
    except Exception as e:
        logger.exception("Failed to save the updated Excel file.")

    logger.info("\nAutomation script finished.")
