import pandas as pd
from datetime import datetime
from loguru import logger
import sys
import os
from bs4 import BeautifulSoup


def apply_splitwise_categorization_rules(description):
    """
    Applies a set of predefined rules to automatically categorize a transaction
    based on its full description string.

    Args:
        description (str): The full description of the transaction 
                           (e.g., "Groceries | Boiled eggs | Gaurav V. | 91.0").
    
    Returns:
        str: The determined category, or an empty string if no rule matches.
    """
    # --- Define Your Custom Rules Here ---
    # The script will check each rule in order. The FIRST rule that matches will be applied.
    # The keyword is case-insensitive and is checked against the full description.
    CATEGORIZATION_RULES = [
        {"keywords": ["Groceries"], "category": "Groceries"},
        # {"keywords": ["Home"], "category": "Home"},
        # {"keywords": ["trip", "vacation"], "category": "Vacation"},
        {"keywords": ["sports", "cricket", "badminton"], "category": "Sports"},
        # --- Add more rules as needed ---
    ]

    for rule in CATEGORIZATION_RULES:
        for keyword in rule['keywords']:
            if keyword.lower() in description.lower():
                logger.debug(f"Rule matched for description '{description}' with keyword '{keyword}'. Applying category '{rule['category']}'.")
                return rule['category']
    
    logger.warning(f"No category rule found for description: '{description}'. It will be left blank.")
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
    # --- FIX: Use the direct child selector '>' to prevent duplicate processing ---
    expense_blocks = soup.select('#expenses_list > .expense:not(:has(.payment))')
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
        datetime_str = date_element['title'] if date_element and 'title' in date_element.attrs else None
        if not datetime_str:
            continue

        # --- NEW: More reliable date parsing ---
        # Extract time from the full timestamp
        time_part = datetime.fromisoformat(datetime_str.replace('Z', '+00:00')).strftime('%H:%M:%S')
        # Extract visible date parts
        month_text = date_element.get_text(strip=True, separator=' ').split(' ')[0]
        day_text = date_element.find("div", class_="number").get_text(strip=True)
        year_text = datetime.fromisoformat(datetime_str.replace('Z', '+00:00')).strftime('%Y')
        # Combine into a reliable date string and parse
        reliable_date_str = f"{day_text} {month_text} {year_text} {time_part}"
        full_datetime = datetime.strptime(reliable_date_str, "%d %b %Y %H:%M:%S")


        # --- Determine who paid and what the user's share is ---
        cost_div = expense.select_one('.cost')
        you_div = expense.select_one('.you')
        
        user_share = 0.0
        you_text = you_div.get_text(strip=True, separator=' ').lower()
        
        if 'you borrowed' in you_text and 'nothing' in you_text:
            user_share = 0.0
        else:
            amount_element = you_div.select_one('.amount, .positive, .negative')
            if amount_element:
                amount_text = amount_element.get_text(strip=True).replace('₹', '').replace(',', '')
                user_share = float(amount_text)
            else:
                logger.warning(f"Could not find amount for transaction '{title}'. Assuming share is 0.")

        cost_text = cost_div.get_text(strip=True, separator=' ').lower()
        paid_by_you = 'you paid' in cost_text
        multiple_payers = 'people paid' in cost_text
        
        total_paid_text = cost_div.select_one('.number').get_text(strip=True).replace('₹', '').replace(',', '')
        total_paid = float(total_paid_text)
        
        payer_info = cost_div.get_text(" ", strip=True).split(" paid")[0]
        payer = "You" if paid_by_you else payer_info

        # --- Generate Transaction Records Based on Logic ---
        base_data = {
            'Datetime': full_datetime.strftime('%Y-%m-%d %I:%M %p'),
            'Notes': title,
            'Status': 'Pending',
            'Description': f"{group} | {title} | {payer} | {total_paid}"
        }

        if multiple_payers:
            # Case 1: Multiple people paid. Create a single net expense entry.
            if user_share > 0.01:
                expense_entry = base_data.copy()
                expense_entry.update({
                    'Type': 'Expense',
                    'Account': 'Splitwise',
                    'Category': apply_splitwise_categorization_rules(expense_entry['Description']),
                    'Amount': user_share,
                })
                transactions.append(expense_entry)
        elif paid_by_you:
            # Case 2: You paid. This creates two entries.
            your_expense_amount = total_paid - user_share
            
            if your_expense_amount > 0.01:
                expense_entry = base_data.copy()
                expense_entry.update({
                    'Type': 'Expense',
                    'Account': 'Splitwise',
                    'Category': apply_splitwise_categorization_rules(expense_entry['Description']),
                    'Amount': your_expense_amount,
                })
                transactions.append(expense_entry)

            if user_share > 0.01:
                transfer_entry = base_data.copy()
                transfer_entry.update({
                    'Type': 'Transfer',
                    'Account': 'X',
                    'Category': 'Splitwise',
                    'Amount': user_share,
                })
                transactions.append(transfer_entry)

        else:
            # Case 3: Someone else paid. This is a simple expense for you.
            if user_share > 0.01:
                expense_entry = base_data.copy()
                expense_entry.update({
                    'Type': 'Expense',
                    'Account': 'Splitwise',
                    'Category': apply_splitwise_categorization_rules(expense_entry['Description']),
                    'Amount': user_share,
                })
                transactions.append(expense_entry)
            
    # --- Process settlement payments ---
    payment_blocks = soup.select('#expenses_list > .expense.summary.payment.involved')
    logger.info(f"Found {len(payment_blocks)} potential settlement entries.")
    for payment in payment_blocks:
        datetime_str = payment['data-date']
        full_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        description_element = payment.select_one('.description a')
        full_description = description_element.get_text(" ", strip=True) if description_element else "Unknown Payment"
        
        cleaned_description = full_description.split(' in “')[0].strip()
        
        amount_element = payment.select_one('.you .positive, .you .negative')
        amount = float(amount_element.get_text(strip=True).replace('₹', '').replace(',', ''))

        cost_text = payment.select_one('.cost').get_text(strip=True).lower()
        
        payment_data = {
            'Type': 'Transfer',
            'Amount': amount,
            'Notes': cleaned_description,
            'Datetime': full_datetime.strftime('%Y-%m-%d %I:%M %p'),
            'Status': 'Pending',
            'Description': f"Settlement | {cleaned_description}"
        }

        if 'you paid' in cost_text:
            payment_data['Account'] = 'X'
            payment_data['Category'] = 'Splitwise'
        elif 'you received' in cost_text:
            payment_data['Account'] = 'Splitwise'
            payment_data['Category'] = 'X'
        else:
            continue

        transactions.append(payment_data)


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
        base_name = input_html_file.replace('.html', '').replace('.htm', '')
        output_excel_file = f"{base_name}_processed.xlsx"

        logger.debug(f"Input HTML file: {input_html_file}")
        logger.debug(f"Base name for output: {base_name}")
        logger.debug(f"Output Excel file will be: {output_excel_file}")
        
        try:
            transactions_df.to_excel(output_excel_file, index=False)
            logger.success(f"Successfully processed and generated {len(transactions_df)} transaction records.")
            logger.success(f"Output saved to: {os.path.abspath(output_excel_file)}")
        except Exception as e:
            logger.error(f"Failed to save the Excel file. Error: {e}")

if __name__ == '__main__':
    main()
