from datetime import datetime
from loguru import logger
import pandas as pd


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
                'datetime': datetime(2025, 10, 1, 8, 30),
            },
            {
                'type': 'Transfer',
                'account': 'Infinity Tata Neu CC',
                'category': 'Splitwise',  # In case of Transfer, this is the other account
                'amount': 1200,
                'notes': 'Trial 3',
                'datetime': datetime(2025, 10, 9, 19, 30),
            },
            {
                'type': 'Income',
                'account': 'Infinity Tata Neu CC',
                'category': 'Salary',
                'amount': 1200,
                'notes': 'Trial 3',
                'datetime': datetime(2025, 10, 3, 1, 30),
            },
            {
                'type': 'Expense',
                'account': 'Splitwise',
                'category': 'Transportation',
                'amount': 1200,
                'notes': 'Trial 1',
                'datetime': datetime.strptime("2025-10-25 08:45 PM", "%Y-%m-%d %I:%M %p"),
            },
            {
                'type': 'Expense',
                'account': 'HSBC CC',
                'category': 'Vacation',
                'amount': 654.78,
                'notes': 'Trial 4',
                'datetime': datetime.strptime("2025-10-25 04:45 AM", "%Y-%m-%d %I:%M %p"),
            },
            {
                'type': 'Expense',
                'account': 'Cash',
                'category': 'Tax',
                'amount': 1800.65,
                'notes': 'Trial - Flight',
                'datetime': datetime(2025, 10, 2, 18, 30),
            },
            {
                'type': 'Expense',
                'account': 'SBI Elite CC',
                'category': 'Transportation',
                'amount': 123879.23,
                'notes': 'Trial - Flight',
                'datetime': datetime(2025, 10, 1, 8, 30),
            },
        ]
        return transactions_to_add
