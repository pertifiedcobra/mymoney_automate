import pandas as pd
from datetime import datetime
from loguru import logger
import sys
import os
from bs4 import BeautifulSoup

def apply_splitwise_categorization_rules(group_name):
    """
    Applies a set of predefined rules to automatically categorize a transaction
    based on its Splitwise group name.

    Args:
        group_name (str): The name of the group from Splitwise.
    
    Returns:
        str: The determined category, or an empty string if no rule matches.
    """
    # --- Define Your Custom Rules Here ---
    # The script will check each rule in order. The FIRST rule that matches will be applied.
    # The keyword is case-insensitive.
    CATEGORIZATION_RULES = [
        {"keywords": ["Groceries"], "category": "Groceries"},
        # {"keywords": ["Home"], "category": "Home"},
        # {"keywords": ["trip", "vacation"], "category": "Vacation"},
        {"keywords": ["sports", "cricket", "badminton"], "category": "Sports"},
        # --- Add more rules as needed ---
    ]

    for rule in CATEGORIZATION_RULES:
        for keyword in rule['keywords']:
            if keyword.lower() in group_name.lower():
                logger.debug(f"Rule matched for group '{group_name}' with keyword '{keyword}'. Applying category '{rule['category']}'.")
                return rule['category']
    
    logger.warning(f"No category rule found for group: '{group_name}'. It will be left blank.")
    return ""

def parse_splitwise_html(file_path):
    """
    Parses a saved Splitwise HTML file and extracts transaction details.

    The script uses BeautifulSoup to find all expense blocks, determines who paid
    and what the user's share is, and generates one or two transaction rows accordingly.

    Args:
        file_path (str): The full path to the .html file.

    Returns:
        pandas.DataFrame: A DataFrame containing the parsed transactions, or None.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'lxml')
    except FileNotFoundError:
        logger.error(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        logger.error(f"An error occurred while reading the file: {e}")
        return None

    transactions = []
    # Find all expense blocks, excluding payment summaries
    expense_blocks = soup.select('#expenses_list .expense:not(:has(.payment))')
    logger.info(f"Found {len(expense_blocks)} potential expense entries.")

    for expense in expense_blocks:
        # Skip entries where the user is not involved at all
        if expense.select_one('.summary.uninvolved'):
            continue

        # --- Extract Core Information ---
        title_element = expense.select_one('.description a')
        title = title_element.get_text(strip=True) if title_element else "Unknown"
        
        group_element = expense.select_one('.label.group')
        group = group_element.get_text(strip=True) if group_element else "Non-group"

        date_element = expense.select_one('.date')
        # The full datetime is in the 'title' attribute of the date div
        datetime_str = date_element['title'] if date_element and 'title' in date_element.attrs else None
        if not datetime_str:
            continue # Skip if we can't find a valid datetime
        
        # Parse the ISO 8601 format datetime string (e.g., 2025-08-28T14:48:39Z)
        full_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))

        # --- Determine who paid and what the user's share is ---
        cost_div = expense.select_one('.cost')
        you_div = expense.select_one('.you')
        
        # Clean the currency symbol and commas, then convert to float
        amount_text = you_div.select_one('.amount, .positive, .negative').get_text(strip=True).replace('₹', '').replace(',', '')
        user_share = float(amount_text)

        paid_by_you = 'you paid' in cost_div.get_text(strip=True, separator=' ').lower()
        
        # --- Generate Transaction Records Based on Logic ---
        base_data = {
            'Datetime': full_datetime.strftime('%Y-%m-%d %I:%M %p'),
            'Notes': title,
            'Status': 'Pending',
            'Description': f"{group} | {title}"
        }

        if paid_by_you:
            # Case 1: You paid. This creates two entries.
            # Entry A: The portion you personally owe is an expense from Splitwise.
            total_paid_text = cost_div.select_one('.number').get_text(strip=True).replace('₹', '').replace(',', '')
            total_paid = float(total_paid_text)
            your_expense_amount = total_paid - user_share
            
            if your_expense_amount > 0.01: # Only add if your share is meaningful
                expense_entry = base_data.copy()
                expense_entry.update({
                    'Type': 'Expense',
                    'Account': 'Splitwise',
                    'Category': apply_splitwise_categorization_rules(group),
                    'Amount': your_expense_amount,
                })
                transactions.append(expense_entry)

            # Entry B: The amount you lent to others is a transfer from your bank to Splitwise.
            if user_share > 0.01: # Only add if you lent a meaningful amount
                transfer_entry = base_data.copy()
                transfer_entry.update({
                    'Type': 'Transfer',
                    'Account': 'X', # Placeholder for the source account
                    'Category': 'Splitwise', # The destination account
                    'Amount': user_share,
                })
                transactions.append(transfer_entry)

        else:
            # Case 2: Someone else paid. This is a simple expense for you.
            expense_entry = base_data.copy()
            expense_entry.update({
                'Type': 'Expense',
                'Account': 'Splitwise',
                'Category': apply_splitwise_categorization_rules(group),
                'Amount': user_share,
            })
            transactions.append(expense_entry)

    if not transactions:
        logger.warning("No valid and involved transactions were processed from the file.")
        return None

    df = pd.DataFrame(transactions)
    output_columns = ['Type', 'Account', 'Category', 'Amount', 'Notes', 'Datetime', 'Status', 'Description']
    df = df[output_columns]
    
    return df

def main():
    """
    Main function to execute the script.
    """
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    logger.info("--- Splitwise HTML Export to Excel Converter ---")
    
    input_html_file = input("Please enter the full path to your Splitwise .html file: ").strip().strip('"')

    if not os.path.exists(input_html_file):
        logger.error("The provided file path does not exist. Please check the path and try again.")
        return

    transactions_df = parse_splitwise_html(input_html_file)

    if transactions_df is not None and not transactions_df.empty:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        logger.debug(f"\n{transactions_df}")
        # base_name = os.path.basename(input_html_file).replace('.html', '').replace('.htm', '')
        # output_excel_file = f"{base_name}_processed.xlsx"
        
        # try:
        #     transactions_df.to_excel(output_excel_file, index=False)
        #     logger.success(f"Successfully processed and generated {len(transactions_df)} transaction records.")
        #     logger.success(f"Output saved to: {os.path.abspath(output_excel_file)}")
        # except Exception as e:
        #     logger.error(f"Failed to save the Excel file. Error: {e}")

if __name__ == '__main__':
    main()
