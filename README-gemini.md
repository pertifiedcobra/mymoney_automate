# **MyMoneyPro Automator**

## **1\. Project Overview**

MyMoneyPro Automator is a Python-based automation suite designed to streamline the process of entering financial transactions into the "MyMoneyPro" mobile application. The project addresses the tedious manual task of transferring transaction data from various bank and service statements into the app.

It achieves this through a multi-stage process:

1. **Parsing:** A collection of scripts parses various statement formats (QIF, Excel, HTML) from different accounts (HDFC, Tata Neu CC, Splitwise) into a standardized format.  
2. **Normalization:** Consolidates the parsed data into a single, master Excel file that acts as the source of truth for the automation.  
3. **Automation:** Uses Android Debug Bridge (ADB) to simulate user taps and text input on an Android device, reading from the master Excel file to automatically add each transaction into the MyMoneyPro app.

The system is built to be secure, robust, and highly configurable, utilizing Optical Character Recognition (OCR) for dynamic UI element detection and a caching mechanism for improved performance over time.

## **2\. Project Structure**

The project is organized into a src directory containing the core logic, which is further divided into modules for better maintainability.

└── pertifiedcobra-mymoney\_automate/  
    ├── README.md  
    ├── requirements.txt  
    └── src/  
        ├── \_\_init\_\_.py  
        ├── data\_loader.py  
        ├── mymoney\_automater\_v2.py       \# Main entry point for the automation.  
        ├── mymoneypro\_automator.py       \# Core class that handles ADB and OCR interactions.  
        ├── account\_statement\_parsers/  
        │   ├── \_\_init\_\_.py  
        │   ├── qif\_to\_csv\_parser.py      \# Parses HDFC .qif statement files.  
        │   ├── rupar\_acc\_parse.py        \# Parses Tata Neu CC .xlsx statement files.  
        │   └── splitwise\_parse.py        \# Parses Splitwise .html export files.  
        ├── app\_coordinates/  
        │   ├── \_\_init\_\_.py  
        │   ├── realme\_coordinates.py     \# Configuration and coordinates for a Realme device.  
        │   └── s24u\_coordinates.py       \# Configuration and coordinates for a Samsung S24 Ultra.  
        └── utils/  
            ├── \_\_init\_\_.py  
            ├── account\_categories\_list.py \# Master lists of valid accounts and categories.  
            ├── misc.py                   \# Miscellaneous helper functions (net diff calculation, etc.).  
            ├── ui\_cache.py               \# Handles the OCR coordinate caching system.  
            └── validate\_transactions.py  \# Validates the data in the master Excel file.

### **File & Directory Descriptions**

* **src/mymoney\_automater\_v2.py**: The **main executable script**. This is the file you run to start the entire automation process. It orchestrates loading data, validation, and initiating the UI automation.  
* **src/mymoneypro\_automator.py**: Contains the MyMoneyProAutomator class. This is the heart of the automation, containing all the low-level methods for sending ADB commands (tapping, swiping, typing) and performing OCR to find UI elements on the screen.  
* **src/data\_loader.py**: Responsible for loading transaction data from the master Excel file or loading sample data for testing.  
* **src/account\_statement\_parsers/**: This directory holds all the individual scripts used to parse raw statement files from different sources into a standardized format.  
* **src/app\_coordinates/**: This directory contains device-specific configurations. Each file defines an AppCoordinates class for a particular phone model.  
* **src/utils/**: A package for utility modules that support the main script.  
  * account\_categories\_list.py: Centralized lists of all your valid accounts and income/expense categories. Used by the validation module.  
  * misc.py: Helper functions, most notably calculate\_and\_print\_net\_diffs for the pre-run verification summary.  
  * ui\_cache.py: Implements the UICache class, which saves and loads the coordinates of UI elements found via OCR to a .json file, speeding up subsequent runs.  
  * validate\_transactions.py: A crucial module that checks the master Excel file for errors before any automation begins, ensuring data integrity.

## **3\. Getting Started: Setup and Installation**

Follow these steps to set up your environment and run the project.

### **Step 1: System Prerequisites**

Before you begin, ensure you have the following software installed on your computer:

1. **Python**: The script is written in Python (3.7+). If you don't have it, download and install it from [python.org](https://www.python.org/). Make sure to check the box that says "Add Python to PATH" during installation.  
2. **Tesseract-OCR Engine**: This is the OCR engine used to read text from your phone's screen.  
   * **Windows**: Download the installer from the [Tesseract at UB Mannheim repository](https://www.google.com/search?q=https://github.com/UB-Mannheim/tesseract/wiki). **During installation, ensure you add Tesseract to your system's PATH.**  
   * **macOS**: Use Homebrew: brew install tesseract  
   * **Linux (Debian/Ubuntu)**: sudo apt-get install tesseract-ocr  
3. **Android Debug Bridge (ADB)**: This tool allows your computer to communicate with your phone.  
   * Download the "SDK Platform-Tools" for your operating system from the [Android Developer website](https://developer.android.com/studio/releases/platform-tools).  
   * Extract the folder and add its location to your system's PATH environment variable.

### **Step 2: Project & Virtual Environment Setup**

1. **Clone or Download the Project**: Get the project files onto your computer.  
2. **Create a Virtual Environment**: Open a terminal in the project's root directory (pertifiedcobra-mymoney\_automate) and create a virtual environment. This keeps the project's dependencies isolated.  
   python \-m venv venv

3. **Activate the Virtual Environment**:  
   * **Windows**: venv\\Scripts\\activate  
   * **macOS/Linux**: source venv/bin/activate

You will see (venv) at the beginning of your terminal prompt, indicating it's active.

4. **Install Python Libraries**: With the virtual environment active, install all required libraries from the requirements.txt file:  
   pip install \-r requirements.txt

5. **Set PYTHONPATH**: This crucial step allows Python to find the project's modules. You need to add the **src directory** to your PYTHONPATH.  
   * **Windows (Command Prompt)**: set PYTHONPATH=%PYTHONPATH%;C:\\path\\to\\your\\project\\pertifiedcobra-mymoney\_automate\\src  
   * **Windows (PowerShell)**: $env:PYTHONPATH \+= ";C:\\path\\to\\your\\project\\pertifiedcobra-mymoney\_automate\\src"  
   * **macOS/Linux**: export PYTHONPATH="${PYTHONPATH}:/path/to/your/project/pertifiedcobra-mymoney\_automate/src"

**Note:** These commands set the variable for the current terminal session only. For a permanent solution, you'll need to set it as a system environment variable.

### **Step 3: Phone Setup & Configuration**

1. **Enable Developer Options**: Go to Settings \> About Phone and tap the Build Number seven times.  
2. **Enable USB Debugging**: Go to Settings \> System \> Developer options and enable USB debugging.  
3. **Connect and Authorize**: Connect your phone to your computer via USB. On your phone, a prompt will appear to "Allow USB debugging". Check "Always allow from this computer" and tap "Allow".  
4. **Verify ADB Connection**: In your terminal, run adb devices. You should see your device's serial number.  
5. **Create a Coordinate File for Your Phone**:  
   * In the src/app\_coordinates/ directory, make a copy of an existing file (e.g., realme\_coordinates.py) and rename it to reflect your device (e.g., my\_pixel\_coordinates.py).  
   * On your phone, go to Developer options and enable **Pointer location**. This will show an overlay with the X and Y coordinates of your taps.  
   * Open your new coordinate file and the MyMoneyPro app.  
   * Methodically go through each variable in the AppCoordinates class. For each one, tap the corresponding button or area on your phone's screen and update the coordinates in the file. Be precise, especially with keypad numbers.  
   * **Disable Pointer location** when you are finished.  
6. **Find the App Package Name**:  
   * Install an app like "Package Names Viewer" from the Play Store.  
   * Find MyMoneyPro in the list and copy its package name (e.g., com.raha.app.mymoney.pro).  
   * Update the self.app\_package\_name variable in your new coordinate file.  
7. **Select Your Device in the Main Script**:  
   * Open src/mymoney\_automater\_v2.py.  
   * Change the import statement at the top to point to your new coordinate file:  
     from src.app\_coordinates.my\_pixel\_coordinates import AppCoordinates

## **4\. Security**

The script includes a critical safety feature to prevent it from performing actions in the wrong application.

* **App Focus Check**: Before every tap or text entry, the script runs the \_check\_app\_focus method. This method verifies that the app currently in the foreground on your phone is the one specified by app\_package\_name. If any other app is active, the script will immediately abort with a critical error message.  
* **It is essential that you set the correct app\_package\_name in your coordinates file for this feature to work.**

## **5\. Usage Workflow**

1. **Parse Statements**: Run the appropriate parser script from src/account\_statement\_parsers/ to convert your raw bank/service statements into processed .xlsx files.  
2. **Consolidate Data**: Copy the transactions from the processed files into your single master Excel file (e.g., transactions\_source.xlsx).  
3. **Review and Categorize**: Open the master Excel file. Fill in the Category and Notes for each transaction where needed. Ensure the Status for all new transactions is set to Pending.  
4. **Run the Automator**:  
   * Make sure the master Excel file is **closed**.  
   * Connect your phone and unlock it to the main home screen of the MyMoneyPro app.  
   * Activate your virtual environment (venv\\Scripts\\activate or source venv/bin/activate).  
   * Run the main script from the **root directory**:  
     python src/mymoney\_automater\_v2.py

   * The script will prompt you for the path to your master Excel file. Paste it in and press Enter.  
   * Review the "Net Changes" summary.  
   * Press Enter again to begin the automation. The script will add the entries and update the Excel file's status to "Added" upon completion.
