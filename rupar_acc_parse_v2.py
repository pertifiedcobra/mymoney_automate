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
            
            transactions.append(data)

        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping row {index + header_row_index + 2} due to a parsing error: {e}. Row data: {row.to_dict()}")
            continue
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
    logger.info("Close the file that will be processed, otherwise it may cause an error.")
    
    # input_excel_file = input("Please enter the full path to your statement .xlsx file: ")
    input_excel_file = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Statements\\Paytm_UPI_Statement_03_Jul'25_-_28_Jul'25.xlsx"
    # --- NEW: Automatically clean the path copied from Windows Explorer ---
    input_excel_file = input_excel_file.strip()
    input_excel_file = input_excel_file.strip('"')

    if not os.path.exists(input_excel_file):
        logger.error("The provided file path does not exist. Please check the path and try again.")
        return

    transactions_df = parse_tata_neu_excel(input_excel_file)
    logger.debug(f"Parsed DataFrame:\n{transactions_df.head(100) if transactions_df is not None else 'No transactions found.'}")

    # if transactions_df is not None and not transactions_df.empty:
    #     base_name = os.path.basename(input_excel_file).replace('.xlsx', '').replace('.xls', '')
    #     output_excel_file = f"{base_name}_processed.xlsx"
        
    #     try:
    #         transactions_df.to_excel(output_excel_file, index=False)
    #         logger.success(f"Successfully processed {len(transactions_df)} transactions.")
    #         logger.success(f"Output saved to: {os.path.abspath(output_excel_file)}")
    #     except Exception as e:
    #         logger.error(f"Failed to save the Excel file. Error: {e}")

if __name__ == '__main__':
    main()
