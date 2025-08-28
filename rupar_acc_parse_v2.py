import pandas as pd
from datetime import datetime
from loguru import logger
import sys
import os
import math

def find_header_row(df):
    """
    Scans the initial rows of a DataFrame to find the actual header row.
    It looks for the row that contains the 'Date' and 'Transaction Details' columns.
    
    Args:
        df (pd.DataFrame): The raw DataFrame read from Excel.

    Returns:
        int: The index of the header row, or None if not found.
    """
    for i, row in df.head(20).iterrows():
        # Check if key columns are present in the row's values
        if 'Date' in row.values and 'Transaction Details' in row.values:
            return i
    return None

def apply_categorization_rules(data, row):
    """
    Applies a set of predefined rules to automatically categorize transactions
    and populate the Notes field.

    Args:
        data (dict): The transaction data dictionary to be modified.
        row (pd.Series): The original row from the DataFrame to access all columns.
    
    Returns:
        dict: The modified data dictionary.
    """
    # --- Define Your Custom Rules Here ---
    # The script will check each rule in order. The FIRST rule that matches will be applied.
    CATEGORIZATION_RULES = [
        {
            "keywords": ["Elior India", "GMS Salad Counter",],
            "category": "Food",
            "notes_from_remarks": True 
        },
        {
            "keywords": ["Bmtc Bus"],
            "category": "Transportation",
            "notes_from_remarks": True 
        },
        # --- Add more rules below ---
        # Example:
        # {
        #     "keywords": ["Flight", "Indigo", "Air India"],
        #     "category": "Travel",
        #     "notes_from_remarks": True
        # },
        # {
        #     "keywords": ["Amazon", "Myntra", "Flipkart"],
        #     "category": "Shopping",
        #     "notes_from_remarks": False # Notes will remain empty
        # },
    ]

    transaction_details = str(row.get('Transaction Details', '')).lower()
    remarks = str(row.get('Remarks', ''))

    if not pd.isna(remarks) and remarks.lower() != 'nan':
        data['Notes'] = remarks[:1].upper() + remarks[1:] if remarks else remarks

    for rule in CATEGORIZATION_RULES:
        for keyword in rule['keywords']:
            if keyword.lower() in transaction_details:
                logger.debug(f"Rule matched for keyword '{keyword}'. Applying category '{rule['category']}'.")
                data['Category'] = rule['category']
                # if rule['notes_from_remarks'] and remarks and not pd.isna(remarks) and remarks.lower() != 'nan':
                #     data['Notes'] = remarks
                # Once a rule is matched for a transaction, we stop checking other rules.
                return data
    
    return data


def parse_tata_neu_excel(file_path):
    """
    Parses an Infinity Tata Neu CC statement from an Excel file and extracts transaction details.

    The script reads the specific "Passbook Payment History" sheet, finds the header,
    and processes each transaction row to create a clean, normalized output.

    Args:
        file_path (str): The full path to the .xlsx file.

    Returns:
        pandas.DataFrame: A DataFrame containing the parsed transactions with
                          columns ready for the automation script, or None if
                          the file cannot be processed.
    """
    try:
        # Read the specific sheet without assuming a header initially
        raw_df = pd.read_excel(file_path, sheet_name="Passbook Payment History", header=None)
    except FileNotFoundError:
        logger.error(f"Error: The file '{file_path}' was not found.")
        return None
    except ValueError as e:
        logger.error(f"Error: Sheet 'Passbook Payment History' not found in the Excel file. Details: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred while reading the Excel file: {e}")
        return None

    header_row_index = find_header_row(raw_df)
    if header_row_index is None:
        logger.error("Could not find the header row in the 'Passbook Payment History' sheet.")
        return None

    # Re-read the sheet, this time with the correct header row
    df = pd.read_excel(file_path, sheet_name="Passbook Payment History", header=header_row_index)
    
    transactions = []
    logger.info(f"Found {len(df)} potential transactions in the sheet.")

    expenses = 0
    income = 0
    net_amount = 0

    for index, row in df.iterrows():
        try:
            # --- NEW: Filter rows based on the 'Your Account' column ---
            your_account_value = str(row.get('Your Account', '')).strip()
            if your_account_value != "HDFC Bank Rupay Credit Card - 00":
                logger.debug(f"Skipping row {index + header_row_index + 2} because 'Your Account' is '{your_account_value}'.")
                continue

            # Extract data, converting to string to handle potential non-string types
            date_str = str(row['Date'])
            time_str = str(row['Time'])
            amount_str = str(row['Amount']).replace(',', '') # Remove commas
            details = str(row['Transaction Details'])
            remarks = str(row['Remarks'])

            # Skip rows that are likely empty or malformed
            if pd.isna(row['Date']) or pd.isna(row['Amount']):
                continue

            data = {}
            
            # Combine date and time. The source format can vary, so we handle both.
            full_datetime = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
            data['Datetime'] = full_datetime.strftime('%Y-%m-%d %I:%M %p')

            original_amount = float(amount_str)

            if original_amount < 0:
                expenses += abs(original_amount)
                net_amount -= abs(original_amount)
            else:
                income += original_amount
                net_amount += original_amount
            
            data['Type'] = 'Income' if original_amount >= 0 else 'Expense'
            data['Amount'] = abs(original_amount)

            # Create a clean description, only adding remarks if they exist and are not 'nan'
            description = details
            if remarks and not pd.isna(remarks) and remarks.lower() != 'nan':
                description += f" | {remarks}"
            data['Description'] = description
            
            data['Account'] = 'Infinity Tata Neu CC' # Set the account name
            data['Category'] = '' # To be filled manually
            data['Notes'] = '' # To be filled manually
            data['Status'] = 'Pending' # Default status
            
            # --- NEW: Apply categorization rules ---
            data = apply_categorization_rules(data, row)

            transactions.append(data)

        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping row {index + header_row_index + 2} due to a parsing error: {e}. Row data: {row.to_dict()}")
            continue
    logger.info(f"Total Income: {income:.2f}")
    logger.info(f"Total Expenses: {expenses:.2f}")
    logger.info(f"Net Amount: {net_amount:.2f}")
    logger.info(f"Processed {len(transactions)} transactions successfully.")

    if not transactions:
        logger.warning("No valid transactions were processed from the file.")
        return None

    # Create the final DataFrame
    final_df = pd.DataFrame(transactions)
    
    # Reorder columns to the desired format
    output_columns = ['Type', 'Account', 'Category', 'Amount', 'Notes', 'Datetime', 'Status', 'Description']
    final_df = final_df[output_columns]
    
    return final_df

def main():
    """
    Main function to execute the script.
    Prompts the user for a file path and generates a new, normalized Excel file.
    """
    logger.remove()
    logger.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    logger.info("--- Infinity Tata Neu CC Excel Statement to Excel Converter ---")
    logger.warning("Close the file that will be processed, otherwise it may cause an error.")
    
    input_excel_file = input("Please enter the full path to your statement .xlsx file: ")
    # input_excel_file = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Statements\\Paytm_UPI_Statement_03_Jul'25_-_28_Jul'25.xlsx"
    # --- NEW: Automatically clean the path copied from Windows Explorer ---
    input_excel_file = input_excel_file.strip()
    input_excel_file = input_excel_file.strip('"')

    if not os.path.exists(input_excel_file):
        logger.error("The provided file path does not exist. Please check the path and try again.")
        return

    transactions_df = parse_tata_neu_excel(input_excel_file)
    pd.set_option('display.max_colwidth', None)
    logger.debug(f"Parsed DataFrame:\n{transactions_df.head(100) if transactions_df is not None else 'No transactions found.'}")

    if transactions_df is not None and not transactions_df.empty:
        base_name = os.path.basename(input_excel_file).replace('.xlsx', '').replace('.xls', '')
        input_dir = os.path.dirname(input_excel_file)
        output_excel_file = os.path.join(input_dir, f"{base_name}_processed.xlsx")
        
        try:
            transactions_df.to_excel(output_excel_file, index=False)
            logger.success(f"Successfully processed {len(transactions_df)} transactions.")
            logger.success(f"Output saved to: {os.path.abspath(output_excel_file)}")
        except Exception as e:
            logger.error(f"Failed to save the Excel file. Error: {e}")

if __name__ == '__main__':
    main()
