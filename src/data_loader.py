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
            # --- Expenses (3) ---
            {
                'type': 'Expense',
                'account': 'HSBC CC',
                'category': 'Food',
                'amount': 150.75,
                'notes': 'Lunch at "The Grand" (with tip)',
                'datetime': datetime(2025, 10, 5, 13, 30), # 01:30 PM
            },
            {
                'type': 'Expense',
                'account': 'SBI Elite CC',
                'category': 'Entertainment',
                'amount': 800,
                'notes': 'Movie tickets: "The Sequel" & popcorn',
                'datetime': datetime.strptime("2025-10-12 08:00 PM", "%Y-%m-%d %I:%M %p"),
            },
            {
                'type': 'Expense',
                'account': 'Cash',
                'category': 'Transportation',
                'amount': 120,
                'notes': 'Auto ride; cost > expected | Final price: $2',
                'datetime': datetime(2025, 10, 18, 9, 15), # 09:15 AM
            },
            {
                'type': 'Expense',
                'account': 'HDFC - Special Gold',
                'category': 'House-Rent',
                'amount': 13000,
                'notes': 'August Rent - cost > expected | Final price: $2',
                'datetime': datetime(2025, 10, 18, 9, 15), # 09:15 AM
            },
            
            # --- Incomes (2) ---
            {
                'type': 'Income',
                'account': 'Fixed Deposit',
                'category': 'Salary',
                'amount': 50000,
                'notes': 'Monthly Salary (Oct \'25)',
                'datetime': datetime(2025, 10, 1, 10, 0), # 10:00 AM
            },
            {
                'type': 'Income',
                'account': 'SBI Bank Account',
                'category': 'Refunds',
                'amount': 255.50,
                'notes': 'Amazon return for item #1234; refund processed',
                'datetime': datetime.strptime("2025-10-20 03:20 PM", "%Y-%m-%d %I:%M %p"),
            },

            # --- Transfers (5) ---
            {
                'type': 'Transfer',
                'account': 'HDFC - UPI',
                'category': 'Splitwise',  # Destination Account
                'amount': 350,
                'notes': 'Settle up with friends (Splitwise)',
                'datetime': datetime(2025, 10, 8, 11, 0), # 11:00 AM
            },
            {
                'type': 'Transfer',
                'account': 'SBI Bank Account',
                'category': 'Mutual Funds', # Destination Account
                'amount': 5000,
                'notes': 'Monthly SIP investment <ELSS>',
                'datetime': datetime(2025, 10, 10, 9, 0), # 09:00 AM
            },
            {
                'type': 'Transfer',
                'account': 'HDFC - UPI',
                'category': 'Parents', # Destination Account
                'amount': 2000.0,
                'notes': 'Money sent home for expenses',
                'datetime': datetime.strptime("2025-10-15 06:00 PM", "%Y-%m-%d %I:%M %p"),
            },
            {
                'type': 'Transfer',
                'account': 'ICICI Sapphiro CC',
                'category': 'HDFC - Special Gold', # Destination Account
                'amount': 10000,
                'notes': 'Credit Card Bill Payment (cleared)',
                'datetime': datetime(2025, 10, 22, 12, 0), # 12:00 PM
            },
            {
                'type': 'Transfer',
                'account': 'Cash',
                'category': 'Other Pending', # Destination Account
                'amount': 50.25,
                'notes': 'Lent to friend~ will get back later',
                'datetime': datetime.strptime("2025-10-28 01:00 PM", "%Y-%m-%d %I:%M %p"),
            },
        ]
        return transactions_to_add
