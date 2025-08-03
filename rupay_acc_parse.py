import pandas as pd
import os # Import os module to check file existence

# --- Configuration ---
# <<< Replace with the actual path to your Excel file >>>
excel_file_path = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Paytm_UPI_Statement_01_Apr'25_-_13_Apr'25.xlsx"
# <<< Replace with the desired path for your output CSV file >>>
csv_file_path = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Paytm_UPI_Statement_01_Apr'25_-_13_Apr'25.csv"
# Specify the sheet name to read from
sheet_name = 'Passbook Payment History'
# Specify the account name to filter by
account_filter_value = 'HDFC Bank Rupay Credit Card - 00'
# Specify columns to remove (Added 'Comment')
columns_to_drop = ['UPI Ref No.', 'Order ID', 'Comment']
# Specify the column to modify (Tags)
remarks_column_to_modify = 'Tags'
# Specify the column to format (Time)
time_column_to_format = 'Time'
# --- End Configuration ---

print(f"Starting Excel processing...")
print(f"Input Excel file: {excel_file_path}")
print(f"Sheet name: '{sheet_name}'")
print(f"Filtering for Account: '{account_filter_value}'")
print(f"Modifying column: '{remarks_column_to_modify}' (removing first 2 chars)")
print(f"Formatting column: '{time_column_to_format}' (from HH:MM:SS to HH:MM AM/PM)") # Updated log for time formatting
print(f"Removing columns: {columns_to_drop}")
print(f"Output CSV file: {csv_file_path}")

# Check if input file exists
if not os.path.exists(excel_file_path):
    print(f"Error: Input Excel file not found at '{excel_file_path}'")
    exit() # Exit the script if the file doesn't exist

try:
    # Read the specific sheet from the Excel file into a pandas DataFrame
    print(f"\nAttempting to read sheet '{sheet_name}' from '{excel_file_path}'...")
    # Use engine='openpyxl' for .xlsx files
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name, engine='openpyxl')
    print(f"Successfully read sheet. Initial rows: {len(df)}")

    # --- Step 1: Filter rows based on 'Your Account' column ---
    print(f"\nFiltering rows where 'Your Account' is '{account_filter_value}'...")
    # Check if the 'Your Account' column exists before filtering
    if 'Your Account' in df.columns:
        original_rows = len(df)
        # Create a boolean mask for filtering
        mask = df['Your Account'] == account_filter_value
        # Apply the mask to filter the DataFrame
        df_filtered = df[mask].copy() # Use .copy() to avoid SettingWithCopyWarning
        rows_after_filter = len(df_filtered)
        print(f"Filtering complete. Kept {rows_after_filter} rows out of {original_rows}.")
    else:
        print(f"Error: Column 'Your Account' not found in sheet '{sheet_name}'. Skipping filtering.")
        df_filtered = df.copy() # Continue with the original data if column not found

    # --- Step 2: Modify the 'Remarks' column ---
    print(f"\nModifying column '{remarks_column_to_modify}'...")
    if remarks_column_to_modify in df_filtered.columns:
        # Ensure the column is treated as string, then slice
        # Using .astype(str) handles potential numbers or NaNs gracefully before slicing
        df_filtered[remarks_column_to_modify] = df_filtered[remarks_column_to_modify].astype(str).str[2:]
        print(f"Successfully removed first 2 characters from '{remarks_column_to_modify}'.")
    else:
        print(f"Warning: Column '{remarks_column_to_modify}' not found. Skipping modification.")

    # --- Step 3: Format the 'Time' column ---
    print(f"\nFormatting column '{time_column_to_format}'...")
    if time_column_to_format in df_filtered.columns:
        # Store original times for comparison or fallback
        original_times = df_filtered[time_column_to_format].copy()

        # Attempt to convert to datetime objects using the specific HH:MM:SS format
        # Coercing errors to NaT (Not a Time) for entries that don't match the format
        # Note: If times are already datetime.time objects from Excel, convert to string first
        # If the column might contain actual datetime objects already, this might need adjustment
        df_filtered[time_column_to_format] = pd.to_datetime(
            df_filtered[time_column_to_format].astype(str), # Convert to string first just in case
            format='%H:%M:%S', # Explicitly specify the input format
            errors='coerce'
        )

        # Format the valid datetime objects to HH:MM AM/PM
        # NaT values will result in NaN after formatting, which we can handle
        formatted_times = df_filtered[time_column_to_format].dt.strftime('%I:%M %p')

        # Fill any NaNs (resulting from NaT or original NaNs) with a placeholder or original value
        # Here, we'll fill with an empty string, adjust if needed
        df_filtered[time_column_to_format] = formatted_times.fillna('') # Or use original_times[formatted_times.isna()] to keep original invalid values

        print(f"Successfully formatted '{time_column_to_format}' to HH:MM AM/PM (invalid entries set to empty string).")
    else:
        print(f"Warning: Column '{time_column_to_format}' not found. Skipping formatting.")

    # --- Step 4: Remove specified columns ---
    print(f"\nAttempting to remove columns: {columns_to_drop}...")
    # Check which columns actually exist in the DataFrame before trying to drop
    existing_columns_to_drop = [col for col in columns_to_drop if col in df_filtered.columns]
    missing_columns = [col for col in columns_to_drop if col not in df_filtered.columns]

    if existing_columns_to_drop:
        # Use the DataFrame that has potentially modified 'Remarks' and 'Time'
        df_dropped = df_filtered.drop(columns=existing_columns_to_drop)
        print(f"Successfully removed columns: {existing_columns_to_drop}")
    else:
        print("No columns to remove were found in the data.")
        df_dropped = df_filtered # Continue with the potentially modified data

    if missing_columns:
        print(f"Warning: The following columns specified for removal were not found: {missing_columns}")

    # --- Step 5: Write the result to a CSV file ---
    if not df_dropped.empty:
        print(f"\nAttempting to write {len(df_dropped)} rows to CSV file: {csv_file_path}...")
        # Use index=False to prevent pandas from writing the DataFrame index as a column
        df_dropped.to_csv(csv_file_path, index=False, encoding='utf-8')
        print(f"Successfully wrote filtered data to '{csv_file_path}'")
    else:
        print("\nNo data remaining after filtering and modification. CSV file will not be created or will be empty.")

except FileNotFoundError:
    print(f"Error: Input Excel file not found at '{excel_file_path}'")
except ValueError as ve:
    # Specific check if the sheet name was not found
    if f"Worksheet named '{sheet_name}' not found" in str(ve):
         print(f"Error: Sheet named '{sheet_name}' not found in the Excel file '{excel_file_path}'.")
         print("Please check the sheet name in the configuration.")
    # Check for time parsing errors if format is specified
    elif "time data" in str(ve) and "does not match format" in str(ve):
        print(f"Error parsing time in column '{time_column_to_format}'. Ensure all entries match 'HH:MM:SS' format or adjust the script.")
        print(f"Specific error: {ve}")
    else:
         print(f"An error occurred during processing: {ve}")
except ImportError:
    print("Error: The 'openpyxl' library is required to read .xlsx files.")
    print("Please install it using: pip install openpyxl")
except Exception as e:
    # Catch any other unexpected errors during processing
    print(f"An unexpected error occurred: {e}")

print("\nProcessing finished.")
