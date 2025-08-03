import re
import pandas as pd
from datetime import datetime
from loguru import logger
import sys
import os

def parse_hdfc_qif(file_path):
    """
    Parses an HDFC bank statement in .qif format and extracts transaction details.

    The script reads the file line by line, identifying transaction blocks
    that start with a date ('D') and end with a caret ('^'). It intelligently
    extracts the date, amount, transaction number, and a clean description.

    Args:
        file_path (str): The full path to the .qif file.

    Returns:
        pandas.DataFrame: A DataFrame containing the parsed transactions with
                          columns ready for the automation script, or None if
                          the file cannot be processed.
    """
    account_name = ''
    if "XX2562" in file_path:
        account_name = 'HDFC - UPI'
    elif "XX6642" in file_path:
        account_name = 'HDFC - Special Gold'
    else:
        logger.error(f"Unknown account name for file: {file_path}. Defaulting to '{account_name}'.")
        raise ValueError(f"Unknown account name for file: {file_path}. Please check the file name or update the script.")

    transactions = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        logger.error(f"An error occurred while reading the file: {e}")
        return None

    # Each transaction is separated by a '^' character on its own line.
    transaction_blocks = content.strip().split('\n^\n')

    logger.info(f"Found {len(transaction_blocks)} potential transaction blocks in the file.")

    for block in transaction_blocks:
        lines = block.strip().split('\n')
        
        if not lines or not (lines[0].strip() == '!Type:Bank' or lines[0].startswith('D')):
            continue
        
        if lines[0].strip() == '!Type:Bank':
            lines = lines[1:]

        data = {}
        description_parts = []
        
        # Regex to find the transaction time, e.g., 'MTXN TIME 21:02:47' or 'TXN TIME 12:04:29'
        time_regex = re.compile(r'M?TXN TIME (\d{2}:\d{2}:\d{2})')
        
        date_str = None
        time_str = "00:00:00" # Default time if not found
        transaction_num = None

        for line in lines:
            if not line:
                continue
            
            prefix = line[0]
            value = line[1:].strip()

            if prefix == 'D':
                date_str = value
            elif prefix == 'T':
                data['Amount'] = float(value.replace(',', ''))
            elif prefix == 'N':
                transaction_num = value
            elif prefix in ['P', 'M']:
                # Check if this line contains the transaction time
                match = time_regex.search(line)
                if match:
                    time_str = match.group(1)
                    # Clean the time part from the description
                    cleaned_value = time_regex.sub('', line[1:]).strip()
                    if cleaned_value:
                        description_parts.append(cleaned_value)
                else:
                    description_parts.append(value)

        if date_str and 'Amount' in data:
            try:
                full_datetime = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%y %H:%M:%S")
                
                # --- NEW: Logic to determine Type and format Amount/Datetime ---
                original_amount = data['Amount']
                data['Type'] = 'Income' if original_amount >= 0 else 'Expense'
                data['Amount'] = abs(original_amount)
                data['Datetime'] = full_datetime.strftime('%Y-%m-%d %I:%M %p')
                
                # Construct a clean and informative description
                final_description = ""
                final_description += " ".join(description_parts)
                data['Description'] = final_description.strip()
                
                data['Account'] = account_name
                data['Category'] = '' # To be filled manually
                data['Notes'] = '' # To be filled manually
                data['Status'] = 'Pending' # Default status
                
                transactions.append(data)
            except ValueError:
                logger.warning(f"Could not parse date/time for a transaction block: Date='{date_str}', Time='{time_str}'")

    if not transactions:
        logger.warning("No valid transactions were found in the file.")
        return None

    df = pd.DataFrame(transactions)
    
    # --- NEW: Reordered and updated columns ---
    output_columns = ['Type', 'Account', 'Category', 'Amount', 'Notes', 'Datetime', 'Status', 'Description']
    df = df[output_columns]
    
    return df

def main():
    """
    Main function to execute the script.
    Prompts the user for a file path and generates an Excel file.
    """
    logger.remove()
    logger.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    logger.info("--- HDFC QIF Statement to Excel Converter ---")
    logger.warning("Close the file that will be processed, otherwise it may cause an error.")
    
    input_qif_file = input("Please enter the full path to your HDFC .qif file: ")
    # input_qif_file = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Statements\\HDFCs\\Acct Statement_XX2562_22022025.qif"
    # --- NEW: Automatically clean the path copied from Windows Explorer ---
    input_qif_file = input_qif_file.strip()
    input_qif_file = input_qif_file.strip('"')

    if not os.path.exists(input_qif_file):
        logger.error("The provided file path does not exist. Please check the path and try again.")
        return

    transactions_df = parse_hdfc_qif(input_qif_file)
    pd.set_option('display.max_colwidth', None)
    logger.debug(f"Parsed DataFrame:\n{transactions_df.head(100) if transactions_df is not None else 'No transactions found.'}")

    if transactions_df is not None and not transactions_df.empty:
        base_name = os.path.basename(input_qif_file).replace('.qif', '')
        input_dir = os.path.dirname(input_qif_file)
        output_excel_file = os.path.join(input_dir, f"{base_name}_processed.xlsx")
    
        try:
            transactions_df.to_excel(output_excel_file, index=False)
            logger.success(f"Successfully processed {len(transactions_df)} transactions.")
            logger.success(f"Output saved to: {os.path.abspath(output_excel_file)}")
        except Exception as e:
            logger.error(f"Failed to save the Excel file. Error: {e}")

if __name__ == '__main__':
    main()
