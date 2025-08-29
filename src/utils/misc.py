from datetime import datetime
from loguru import logger


def serialize_datetimes(transactions):
    for tx in transactions:
        for k, v in tx.items():
            if isinstance(v, datetime):
                tx[k] = v.strftime("%Y-%m-%d %I:%M %p")
    return transactions

def calculate_and_print_net_diffs(transactions):
    """
    Calculates and prints the net change for each account in the transaction list.
    This provides a summary for the user to verify before the automation starts.
    """
    net_diffs = {}
    net_credit = {}
    net_debit = {}
    for tx in transactions:
        tx_type = tx.get('type', 'expense').lower()
        amount = tx['amount']
        account = tx['account']
        
        if tx_type == 'income':
            net_diffs[account] = net_diffs.get(account, 0) + amount
            net_credit[account] = net_credit.get(account, 0) + amount
        elif tx_type == 'expense':
            net_diffs[account] = net_diffs.get(account, 0) - amount
            net_debit[account] = net_debit.get(account, 0) + amount
        elif tx_type == 'transfer':
            destination_account = tx['category']
            # Subtract from the source account
            net_diffs[account] = net_diffs.get(account, 0) - amount
            net_debit[account] = net_debit.get(account, 0) + amount
            # Add to the destination account
            net_diffs[destination_account] = net_diffs.get(destination_account, 0) + amount
            net_credit[destination_account] = net_credit.get(destination_account, 0) + amount

    logger.info("="*50)
    logger.info("PRE-RUN VERIFICATION: EXPECTED NET CHANGES")
    logger.info("="*50)
    if not net_diffs:
        logger.info("No transactions to process.")
    else:
        for account, diff in net_diffs.items():
            # Format the number with commas and two decimal places
            formatted_diff = f"{diff:,.2f}"
            logger.info(f"{account}: {formatted_diff}")
            logger.debug(f"  (Total Credit: {net_credit.get(account, 0):,.2f}, Total Debit: {net_debit.get(account, 0):,.2f})")
    logger.info("="*50)
