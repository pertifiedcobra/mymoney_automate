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

from src.mymoneypro_automator import MyMoneyProAutomator
from src.data_loader import load_transactions_from_excel, load_sample_transactions
from src.utils.validate_transactions import validate_transactions
from src.utils.misc import serialize_datetimes, calculate_and_print_net_diffs

# --- Configuration Section ---
# If Tesseract is not in your system's PATH, uncomment and set the path below.
# This tells the script where to find the Tesseract OCR engine.
# Example for Windows:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def run_automation_workflow(transactions_to_add, input_excel_file=None, main_df=None):
    # --- 2. Pre-run Verification ---
    if not validate_transactions(transactions_to_add):
        logger.error("Validation failed for one or more transactions. Please check the logs for details.")
        sys.exit(1)
    
    calculate_and_print_net_diffs(transactions_to_add)
    
    # --- Debug: Print loaded transactions ---
    # logger.debug(f"Type: {transactions_to_add.type()}")
    # logger.debug(f"{[transaction for transaction in transactions_to_add]}")  # Log the loaded transactions for debugging
    # transactions_to_add_datetime_serialized = serialize_datetimes(transactions_to_add)
    # pprint.pprint(transactions_to_add_datetime_serialized)

    if not transactions_to_add:
        logger.warning("No pending transactions found in the Excel file. Exiting.")
        sys.exit(0)

    # --- 3. User Confirmation and Countdown ---
    logger.info("="*50)
    logger.info("Starting MyMoneyPro Automation...")
    logger.info("Please ensure your phone is connected, unlocked, and on its MAIN screen.")
    # --- User confirmation before starting ---
    input("Press Enter to begin...")
    for i in range (3, 0, -1):
        logger.info(f"Starting in {i} seconds...")
        time.sleep(1)
    logger.info("="*50)

    # --- 4. Main Automation Loop ---
    automator = MyMoneyProAutomator()
    total_transactions = len(transactions_to_add)

    try:
        for i, transaction in enumerate(transactions_to_add):
            logger.info(f"--- Processing transaction {i + 1} of {total_transactions} ---")
            success = automator.begin_entry(transaction)
            if success:
                logger.success(f"MARKING '{transaction['notes']}' as Done.")
                if main_df:
                    original_index = transaction['original_index']
                    main_df.loc[original_index, 'status'] = 'Added'
            else:
                logger.error(f"STOPPING SCRIPT due to failure on '{transaction['notes']}'.")
                break
            time.sleep(automator.coords.SHORT_DELAY)
    finally:
        # --- 5. Save Progress ---
        # This block runs whether the loop finishes, breaks, or is interrupted (Ctrl+C)
        if input_excel_file and main_df:
            logger.info("="*50)
            logger.info("Saving updated statuses back to the Excel file...")
            try:
                main_df.to_excel(input_excel_file, index=False)
                logger.success("Successfully saved the updated Excel file.")
            except Exception as e:
                logger.exception("Failed to save the updated Excel file.")

if __name__ == '__main__':
    # Configure Loguru for real-time, debug-level logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    input_excel_file = None
    main_df = None

    # --- Load transactions from Excel ---
    # input_excel_file = input("Please enter the full path to your statement .xlsx file: ")
    # Below is sample path for testing
    # # --- Automatically clean the path copied from Windows Explorer ---
    # input_excel_file = input_excel_file.strip()
    # input_excel_file = input_excel_file.strip('"')

    # --- 1. Load Data ---
    # --- NEW: Read the main DataFrame once ---
    # try:
    #     main_df = pd.read_excel(input_excel_file)
    #     main_df.columns = [col.lower() for col in main_df.columns]
    # except FileNotFoundError:
    #     logger.error(f"Input Excel file not found at: {input_excel_file}")
    #     sys.exit(1)
    # except Exception as e:
    #     logger.exception("Failed to read the main Excel file.")
    #     sys.exit(1)

    transactions_to_add = load_sample_transactions()  # For testing purposes, you can use this instead
    # transactions_to_add = load_transactions_from_excel(input_excel_file)

    run_automation_workflow(transactions_to_add, input_excel_file, main_df)

    logger.info("\nAutomation script finished.")
