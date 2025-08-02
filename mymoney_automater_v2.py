import os
import sys
import time
import subprocess
from datetime import datetime
import calendar
import re
from PIL import Image
import pytesseract
from loguru import logger

# --- Configuration Section ---
# If Tesseract is not in your system's PATH, uncomment and set the path below.
# This tells the script where to find the Tesseract OCR engine.
# Example for Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- App Coordinates & Configuration ---
class AppCoordinates:
    """
    A dedicated class to store all screen coordinates and configuration.
    This makes the script portable to different devices and screen resolutions.
    """
    def __init__(self):
        # --- General Timings ---
        self.SHORT_DELAY = 0.2
        self.LONG_DELAY = 2.0

        # --- Navigation Coordinates ---
        self.initiate_new_entry_coords = (910, 1970)
        self.save_button_coords = (950, 150)

        # --- Main 'Add Expense' Screen Buttons ---
        self.account_entry_coords = (300, 650)
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


class MyMoneyProAutomator:
    """
    A class to automate expense entry in the MyMoneyPro app using ADB and OCR.
    """
    def __init__(self, coords: AppCoordinates):
        self.coords = coords
        self._current_picker_date = datetime.now()
        self.calendar = calendar.Calendar(firstweekday=calendar.SUNDAY)

    def _execute_adb(self, command, check=True):
        """Executes a given ADB command."""
        return subprocess.run(f"adb shell {command}", shell=True, check=check, capture_output=True)

    def _tap(self, x, y):
        logger.debug(f"Tapping at ({x}, {y})")
        self._execute_adb(f"input tap {x} {y}")
        time.sleep(self.coords.SHORT_DELAY)

    def _type_text(self, text):
        formatted_text = text.replace(" ", "%s")
        logger.debug(f"Typing text: '{text}'")
        self._execute_adb(f"input text '{formatted_text}'")
        time.sleep(self.coords.SHORT_DELAY)

    def _press_key(self, keycode):
        logger.debug(f"Pressing keycode: {keycode}")
        self._execute_adb(f"input keyevent {keycode}")
        time.sleep(0.1)

    def _swipe(self, x1, y1, x2, y2, duration):
        logger.info("Swiping screen to scroll...")
        self._execute_adb(f"input swipe {x1} {y1} {x2} {y2} {duration}")
        time.sleep(self.coords.LONG_DELAY)

    def _find_and_tap_text(self, target_text, max_swipes=5):
        """
        Finds an item by its text, scrolling if necessary. This version filters out
        numerical noise and searches for a sequence of words, making it robust
        against multi-line names and irrelevant text like account balances.
        """
        screenshot_path_phone = "/sdcard/screen.png"
        screenshot_path_local = "screen.png"

        for i in range(max_swipes):
            try:
                logger.debug(f"Scan attempt {i+1}/{max_swipes} for '{target_text}'")
                self._execute_adb(f"screencap -p {screenshot_path_phone}")
                subprocess.run(f"adb pull {screenshot_path_phone} {screenshot_path_local}", shell=True, check=True, capture_output=True)
                
                img = Image.open(screenshot_path_local)
                ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                # --- Advanced "Bag of Words" Logic with Improved Filtering ---
                clean_words_data = []
                # logger.debug("--- Raw OCR Word Detection & Filtering ---")
                for j in range(len(ocr_data['text'])):
                    if int(ocr_data['conf'][j]) > 40:
                        word = ocr_data['text'][j].strip()
                        if not word:
                            continue

                        # --- Improved Filtering Logic ---
                        if re.search(r'\d', word):
                            # logger.debug(f"Discarding word (contains digit): '{word}'")
                            continue
                        if word in ['©', '—', '₹', '%', '|']:
                            # logger.debug(f"Discarding word (noise symbol): '{word}'")
                            continue

                        # logger.debug(f"Keeping word: '{word}'")
                        clean_words_data.append({
                            'text': word,
                            'left': ocr_data['left'][j],
                            'top': ocr_data['top'][j],
                            'width': ocr_data['width'][j],
                            'height': ocr_data['height'][j]
                        })
                
                searchable_text = " ".join([d['text'] for d in clean_words_data])
                logger.debug(f"Searchable Text Block: '{searchable_text}'")

                if target_text.lower() in searchable_text.lower():
                    target_words = target_text.split()
                    for k in range(len(clean_words_data) - len(target_words) + 1):
                        phrase_to_check = " ".join([clean_words_data[k+l]['text'] for l in range(len(target_words))])
                        if target_text.lower() == phrase_to_check.lower():
                            first_word_data = clean_words_data[k]
                            x, y, w, h = first_word_data['left'], first_word_data['top'], first_word_data['width'], first_word_data['height']
                            center_x = x + w // 2
                            center_y = y + h // 2
                            logger.success(f"Found match '{phrase_to_check}'. Tapping first word at ({center_x}, {center_y}).")
                            self._tap(center_x, center_y)
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

    def select_account(self, account_name):
        logger.info(f"--- Selecting Account: {account_name} ---")
        self._tap(self.coords.account_entry_coords[0], self.coords.account_entry_coords[1])
        return self._find_and_tap_text(account_name)

    def select_category(self, category_name):
        logger.info(f"--- Selecting Category: {category_name} ---")
        self._tap(self.coords.category_entry_coords[0], self.coords.category_entry_coords[1])
        return self._find_and_tap_text(category_name)

    def enter_amount(self, amount_str):
        logger.info(f"--- Entering Amount: {amount_str} ---")
        # for _ in range(5): self._tap(self.coords.backspace_coords[0], self.coords.backspace_coords[1])
        for char in str(amount_str):
            if char in self.coords.keypad_coords:
                self._tap(self.coords.keypad_coords[char][0], self.coords.keypad_coords[char][1])

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
        self._tap(self.coords.date_picker_entry_coords[0], self.coords.date_picker_entry_coords[1])
        
        # 2. Navigate to the correct month and year by tapping the '<' or '>' arrows.
        # It calculates how many months to move forward or backward from the current view.
        month_diff = (target_date.year - self._current_picker_date.year) * 12 + (target_date.month - self._current_picker_date.month)
        if month_diff > 0:
            for _ in range(month_diff): self._tap(self.coords.date_month_change_coords['next'][0], self.coords.date_month_change_coords['next'][1])
        elif month_diff < 0:
            for _ in range(abs(month_diff)): self._tap(self.coords.date_month_change_coords['prev'][0], self.coords.date_month_change_coords['prev'][1])
        
        # 3. Update the internal state to prevent re-navigating next time.
        self._current_picker_date = target_date
        
        # 4. Dynamically find the position of the target day.
        # It builds a virtual calendar for the target month and finds the row/column of the target day.
        month_calendar = self.calendar.monthdayscalendar(target_date.year, target_date.month)
        for week_index, week in enumerate(month_calendar):
            if target_date.day in week:
                # 5. Map the row/column to the actual screen coordinates and tap.
                day_index = week.index(target_date.day)
                self._tap(self.coords.date_grid_x_coords[day_index], self.coords.date_grid_y_coords[week_index])
                break
        
        # 6. Finalize by tapping the 'OK' button.
        self._tap(self.coords.date_ok_coords[0], self.coords.date_ok_coords[1])

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
        self._tap(self.coords.time_picker_entry_coords[0], self.coords.time_picker_entry_coords[1])
        
        # 2. Switch to the more reliable keyboard input mode.
        self._tap(self.coords.time_keypad_mode_coords[0], self.coords.time_keypad_mode_coords[1])

        # 3. Select AM or PM.
        target_ampm = target_time.strftime('%p')
        logger.debug(f"Attempting to select {target_ampm}")
        self._tap(self.coords.time_ampm_selector_coords[0], self.coords.time_ampm_selector_coords[1])
        # --- FIX: Added a delay to allow the AM/PM dropdown to animate and appear ---
        self._tap(self.coords.time_ampm_coords[target_ampm][0], self.coords.time_ampm_coords[target_ampm][1])
        
        # 4. Enter the hour.
        self._tap(self.coords.time_hour_coords[0], self.coords.time_hour_coords[1])
        self._press_key(67); self._press_key(67) # Press backspace twice to clear
        self._type_text(target_time.strftime('%I')) # %I is for 12-hour format
        
        # 5. Enter the minute.
        self._tap(self.coords.time_minute_coords[0], self.coords.time_minute_coords[1])
        self._press_key(67); self._press_key(67)
        self._type_text(target_time.strftime('%M'))
        
        # 6. Finalize by tapping the 'OK' button.
        self._tap(self.coords.time_ok_coords[0], self.coords.time_ok_coords[1])

    def enter_notes(self, notes_text):
        logger.info(f"--- Entering Notes: {notes_text} ---")
        self._tap(self.coords.notes_section_coords[0], self.coords.notes_section_coords[1])
        self._type_text(notes_text)

    def add_expense(self, expense_data):
        """
        Orchestrates the entire process of adding a single expense.

        This is the main workflow method that calls all other helper methods in
        the correct sequence to perform a complete expense entry, from navigating
        to the page to filling all fields and saving.

        Args:
            expense_data (dict): A dictionary containing all necessary details
                                 for a single transaction.

        Returns:
            bool: True if the expense was added successfully, False otherwise.
        """
        logger.info(f"\n>>> PROCESSING EXPENSE: {expense_data['notes']} <<<")
        try:
            # 1. Start from the main screen and tap the button to add a new entry.
            logger.info("--- Navigating to Add Expense screen ---")
            self._tap(self.coords.initiate_new_entry_coords[0], self.coords.initiate_new_entry_coords[1])
            time.sleep(self.coords.LONG_DELAY)

            # 2. Fill in all the details in the specified order.
            # If any step fails, it will return False and stop this transaction.
            if not self.select_account(expense_data['account']): return False
            if not self.select_category(expense_data['category']): return False
            self.enter_amount(expense_data['amount'])
            self.set_date(expense_data['datetime'])
            self.set_time(expense_data['datetime'])
            self.enter_notes(expense_data['notes'])
            
            # 3. Save the expense and wait for the app to return to the main screen.
            logger.info("--- Saving Expense ---")
            self._tap(self.coords.save_button_coords[0], self.coords.save_button_coords[1])
            time.sleep(self.coords.LONG_DELAY)
            
            logger.success(">>> SUCCESSFULLY ADDED EXPENSE! <<<")
            return True
        except Exception as e:
            logger.exception("!!! An unrecoverable error occurred during expense entry !!!")
            logger.error("You may need to manually press CANCEL on the phone to reset the app state.")
            return False

if __name__ == '__main__':
    # Configure Loguru for real-time, debug-level logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    my_phone_coords = AppCoordinates()
    transactions_to_add = [
        {
            'account': 'Cash',
            'category': 'Tax',
            'amount': '1800.65',
            'notes': 'Trial - Flight',
            'datetime': datetime(2025, 8, 2, 18, 30),
        },
        {
            'account': 'Infinity Tata Neu CC',
            'category': 'Vacation',
            'amount': '1200',
            'notes': 'Trial 1',
            'datetime': datetime(2025, 8, 1, 8, 30),
        },
        {
            'account': 'Splitwise',
            'category': 'Sports',
            'amount': '1200',
            'notes': 'Trial 1',
            'datetime': datetime.strptime("2025-07-25 08:45 AM", "%Y-%m-%d %I:%M %p"),
        },
        {
            'account': 'Infinity Tata Neu CC',
            'category': 'Vacation',
            'amount': '1200',
            'notes': 'Trial 3',
            'datetime': datetime(2025, 8, 3, 1, 45),
        },
        {
            'account': 'HSBC CC',
            'category': 'Vacation',
            'amount': '654.78',
            'notes': 'Trial 4',
            'datetime': datetime.strptime("2025-08-25 04:45 AM", "%Y-%m-%d %I:%M %p"),
        },
        {
            'account': 'SBI Elite CC',
            'category': 'Vacation',
            'amount': '123879.23',
            'notes': 'Trial - Flight',
            'datetime': datetime(2025, 8, 1, 8, 30),
        },
    ]

    automator = MyMoneyProAutomator(coords=my_phone_coords)

    logger.info("="*50)
    logger.info("Starting MyMoneyPro Automation in 5 seconds...")
    logger.info("Please ensure your phone is connected, unlocked, and on its MAIN screen.")
    logger.info("="*50)
    time.sleep(5)

    for transaction in transactions_to_add:
        success = automator.add_expense(transaction)
        if success:
            logger.success(f"MARKING '{transaction['notes']}' as Done.")
        else:
            logger.error(f"STOPPING SCRIPT due to failure on '{transaction['notes']}'.")
            break
        time.sleep(my_phone_coords.SHORT_DELAY)

    logger.info("\nAutomation script finished.")
