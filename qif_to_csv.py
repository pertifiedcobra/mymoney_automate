import csv
import re
from datetime import datetime
import os # Import os module to check file existence

# --- Configuration ---
# <<< Replace with the actual path to your QIF file >>>
qif_file_path = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Acct Statement_XX2562_03052025.qif"
# <<< Replace with the desired path for your output CSV file >>>
csv_file_path = 'C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Acct Statement_XX2562_03052025.csv'
# --- End Configuration ---

print(f"Starting QIF to CSV conversion...")
print(f"Input QIF file: {qif_file_path}")
print(f"Output CSV file: {csv_file_path}")

# Check if input file exists
if not os.path.exists(qif_file_path):
    print(f"Error: Input file not found at '{qif_file_path}'")
    exit() # Exit the script if the file doesn't exist

# Define CSV header
header = ['Date', 'Amount', 'Num', 'Payee', 'Memo', 'Time']
transactions = []
current_transaction = {}
line_number = 0

# Regex to find time in the memo field (HH:MM:SS format)
time_regex = re.compile(r'(\d{2}):(\d{2}):(\d{2})')

try:
    print(f"Attempting to open and read QIF file: {qif_file_path}")
    with open(qif_file_path, 'r', encoding='utf-8', errors='replace') as infile:
        print("QIF file opened successfully. Processing lines...")
        for line in infile:
            line_number += 1
            line = line.strip() # Remove leading/trailing whitespace

            if not line: # Skip empty lines
                continue

            # Check the first character to identify the field
            field_code = line[0].upper() # Use uppercase for consistency
            field_value = line[1:].strip() # Get the value part

            try:
                if field_code == 'D':
                    # QIF dates can sometimes have ' prepended, handle this
                    current_transaction['Date'] = field_value.replace("'", "")
                elif field_code == 'T':
                    # Amount (usually total amount, handles splits)
                    # Remove commas for proper float conversion if needed later
                    current_transaction['Amount'] = field_value.replace(",", "")
                elif field_code == 'U':
                     # Amount (sometimes used instead of T for non-split)
                    current_transaction['Amount'] = field_value.replace(",", "")
                elif field_code == 'N':
                    current_transaction['Num'] = field_value
                elif field_code == 'P':
                    current_transaction['Payee'] = field_value
                elif field_code == 'M':
                    current_transaction['Memo'] = field_value
                    # Extract and format time from Memo
                    time_match = time_regex.search(field_value)
                    if time_match:
                        try:
                            # Create a datetime object just for formatting
                            time_obj = datetime.strptime(time_match.group(0), '%H:%M:%S')
                            # Format time as HH:MM AM/PM
                            current_transaction['Time'] = time_obj.strftime('%I:%M %p')
                        except ValueError:
                            print(f"Warning: Line {line_number}: Could not parse time '{time_match.group(0)}' found in Memo. Skipping time extraction for this record.")
                            current_transaction['Time'] = 'N/A' # Or set to empty string ''
                    else:
                         # Set default if no time pattern found
                         current_transaction['Time'] = '' # Or set to 'N/A'

                elif field_code == '^':
                    # End of transaction marker
                    if current_transaction: # Ensure it's not an empty marker
                        # Add the completed transaction to our list
                        transactions.append(current_transaction)
                        # print(f"Processed transaction ending near line {line_number}") # Optional: print per transaction
                    # Reset for the next transaction
                    current_transaction = {}
                # Add other QIF codes here if needed (e.g., L for Category)

            except Exception as e:
                print(f"Error processing line {line_number}: '{line}'. Error: {e}")
                # Decide if you want to skip the transaction or stop the script
                # For now, we reset the current transaction and continue
                current_transaction = {}


    print(f"Finished reading QIF file. Total lines processed: {line_number}")
    print(f"Found {len(transactions)} transactions.")

except FileNotFoundError:
    print(f"Error: Input file not found at '{qif_file_path}'")
    exit()
except IOError as e:
    print(f"Error reading file '{qif_file_path}': {e}")
    exit()
except Exception as e:
    print(f"An unexpected error occurred while reading the QIF file: {e}")
    exit()

# Write the collected data to CSV
if transactions: # Only write if we have transactions
    try:
        print(f"Attempting to open and write CSV file: {csv_file_path}")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=header)

            print("Writing CSV header...")
            writer.writeheader()

            print(f"Writing {len(transactions)} transactions to CSV...")
            record_count = 0
            for transaction in transactions:
                # Ensure all header columns exist in the transaction dict, add if missing
                row_data = {col: transaction.get(col, '') for col in header}
                writer.writerow(row_data)
                record_count += 1
            print(f"Successfully wrote {record_count} records to {csv_file_path}")

    except IOError as e:
        print(f"Error writing to file '{csv_file_path}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing the CSV file: {e}")
else:
    print("No transactions found or processed, CSV file will not be created.")

print("Conversion process finished.")