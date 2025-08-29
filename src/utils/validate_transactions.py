from datetime import datetime
from loguru import logger

from src.utils.account_categories_list import accounts_list, entry_type, income_categories_list, expense_categories_list

def _validate_single_transaction(tx, i):
    """Helper function to validate a single transaction dictionary."""
    
    # A list of validation checks to run. Each function returns True if valid.
    validation_checks = [
        _validate_required_fields,
        _validate_data_types,
        _validate_transaction_type,
        _validate_account,
        _validate_category_logic
    ]
    
    for check_func in validation_checks:
        if not check_func(tx, i):
            return False
            
    return True

def _validate_required_fields(tx, i):
    """Checks if all required fields are present in the transaction."""
    required_fields = ['account', 'category', 'amount', 'notes', 'datetime']
    if not all(field in tx for field in required_fields):
        logger.error(f"Row: {i} | Transaction missing required fields: {tx} | Required: {required_fields}")
        return False
    return True

def _validate_data_types(tx, i):
    """Checks if the data types of key fields are correct."""
    if not isinstance(tx['amount'], (int, float)):
        logger.error(f"Row: {i} | Transaction amount is not a number: {tx['amount']} | Type: {type(tx['amount'])}")
        return False
    if not isinstance(tx['datetime'], datetime):
        logger.error(f"Row: {i} | Transaction datetime is not a valid datetime object: {tx['datetime']} | Type: {type(tx['datetime'])}")
        return False
    if not isinstance(tx['notes'], str):
        logger.warning(f"Row: {i} | Notes field is not a string (found {type(tx['notes'])}). Converting.")
        tx['notes'] = str(tx['notes'])
    return True

def _validate_transaction_type(tx, i):
    """Checks if the transaction type is valid."""
    if tx.get('type', 'Expense').lower() not in entry_type:
        logger.error(f"Row: {i} | Transaction type '{tx.get('type')}' is not valid. Must be one of {entry_type}.")
        return False
    return True

def _validate_account(tx, i):
    """Checks if the transaction account is valid."""
    if tx['account'] not in accounts_list:
        logger.error(f"Row: {i} | Transaction account '{tx['account']}' is not in the accounts list.")
        return False
    return True

def _validate_category_logic(tx, i):
    """Validates the category based on the transaction type."""
    tx_type = tx.get('type', 'expense').lower()
    category = tx['category']
    
    if tx_type == 'transfer':
        if category not in accounts_list:
            logger.error(f"Row: {i} | For a transfer, the category '{category}' must be a valid account.")
            return False
        if tx['account'] == category:
            logger.error(f"Row: {i} | For a transfer, the source account and destination account cannot be the same.")
            return False
    elif tx_type == 'income':
        if category not in income_categories_list:
            logger.error(f"Row: {i} | Category '{category}' is not in the income categories list.")
            return False
    elif tx_type == 'expense':
        if category not in expense_categories_list:
            logger.error(f"Row: {i} | Category '{category}' is not in the expense categories list.")
            return False
            
    return True

def validate_transactions(transactions):
    """
    Validates a list of transactions to ensure they have all required fields and correct values.
    Returns True if all transactions are valid, otherwise returns False.
    """
    # Use all() for a concise way to check if all transactions are valid.
    # The list comprehension will generate True/False for each transaction.
    # all() will only be True if every single item in the list is True.
    is_valid = all([_validate_single_transaction(tx, i) for i, tx in enumerate(transactions)])
    
    if is_valid:
        logger.info("All transactions are valid.")
        
    return is_valid
