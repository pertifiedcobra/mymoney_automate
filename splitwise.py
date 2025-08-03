from bs4 import BeautifulSoup
import csv
import io
import os
import sys

# Load the HTML file
html_file = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Statements\\Splitwise\\Splitwise-22-06.html"
file_name = html_file.split("/")[-1].replace(".html","")
print(f"FileName: {file_name}")
with open(html_file, "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Find all expense entries
expenses = []
for expense in soup.find_all("div", class_="expense summary involved"):
    date = expense.find("div", class_="date").get_text(strip=True) if expense.find("div", class_="date") else "Unknown Date"
    title = expense.find("span", class_="description").get_text(strip=True) if expense.find("span", class_="description") else "Unknown Title"
    group = expense.find("span", class_="label group").get_text(strip=True) if expense.find("span", class_="label group") else "Unknown Group"
    title = title.replace(group, "")
    # print(f"{title} - {group}")
    amount_element = expense.find("div", class_="cost").find("span", class_="number") if expense.find("div", class_="cost") else None
    amount = float(amount_element.get_text(strip=True).replace("₹", "").replace(",", "")) if amount_element else 0.0
    
    # Find who made the payment
    cost_div = expense.find("div", class_="cost")
    payer_info = cost_div.get_text(" ", strip=True).split(" paid ") if cost_div else []
    payer = payer_info[0] if len(payer_info) > 1 else "You"
    
    # Find lending/borrowing info and adjust sign accordingly
    transaction_div = expense.find("div", class_="you simplified")
    transaction_info = transaction_div.get_text(" ", strip=True) if transaction_div else ""
    transaction_amount = 0  # Default case
    my_share = amount  # Default to full amount unless modified
    
    if "lent you" in transaction_info:
        transaction_amount = -float(transaction_info.split("₹")[-1].replace(",", "")) if "₹" in transaction_info else 0.0
        my_share = 0  # No share if I didn't pay
    elif "you lent" in transaction_info:
        transaction_amount = float(transaction_info.split("₹")[-1].replace(",", "")) if "₹" in transaction_info else 0.0
        my_share = amount - transaction_amount  # My share of the expense
    
    expenses.append([date, group, title, amount, payer, transaction_amount, my_share])

# Include direct payment transactions with "you received"
for expense in soup.find_all("div", class_="expense summary payment involved"):
    transaction_text = expense.get_text(" ", strip=True)
    title = expense.find("span", class_="description").get_text(strip=True) if expense.find("span", class_="description") else "Unknown Title"
    title = title.replace("\u20b9", "Rs").replace("\n", "").replace("\r", "")
    title = " ".join(title.split())
    amount_element = expense.find("span", class_="negative")
    amount = -float(amount_element.get_text(strip=True).replace("₹", "").replace(",", "")) if amount_element else 0.0
    
    # Extract payer and payee
    payment_info = title.split(" paid ")
    if len(payment_info) == 2:
        payer, payee_info = payment_info
        payee = payee_info.split(" ₹")[0]
    else:
        payer, payee = "Unknown", "Unknown"
    
    expenses.append(["", "", title, amount, payer, amount, 0])  # Include received payments

csv_directory = "C:/Users/thaku/Downloads/Statements/Splitwise/"
csv_directory = "C:\\Users\\thaku\\OneDrive - Indian Institute of Technology (BHU), Varanasi\\Attachments\\Downloads\\Statements\\Splitwise\\"
os.makedirs(csv_directory, exist_ok=True)

# Save to CSV
csv_file = os.path.join(csv_directory, f"{file_name}.csv")
print(f"CSV File: {csv_file}")
with open(csv_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "Group", "Expense Title", "Expense Amount", "Payer", "Lent/Borrowed Amount", "My Share"])
    writer.writerows(expenses)

print(f"CSV file saved: {csv_file}")