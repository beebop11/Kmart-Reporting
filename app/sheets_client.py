import os
import time
import gspread
from google.oauth2.service_account import Credentials
import logging

logger = logging.getLogger(__name__)

# Master Kmart Reporting Summary Sheet
MASTER_SHEET_ID = "1Aehi27ZPHcoj8MWwsbAwzX44EiP7xOHZBsQrzBRR4lk"

def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credentials file not found at {creds_path}. Please ensure it exists.")
        
    credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(credentials)
    return client

def with_retry(max_retries=5, initial_backoff=1):
    """Decorator to apply exponential backoff retries for Google Sheets API calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            backoff = initial_backoff
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except gspread.exceptions.APIError as e:
                    if e.response.status_code == 429: # Rate limit
                        logger.warning(f"Rate limited. Retrying in {backoff} seconds... (Attempt {retries + 1}/{max_retries})")
                        time.sleep(backoff)
                        retries += 1
                        backoff *= 2
                    else:
                        raise e
            raise Exception(f"Max retries exceeded for {func.__name__}")
        return wrapper
    return decorator

class SheetsClient:
    def __init__(self, log_callback=None):
        self.client = get_client()
        self.log_callback = log_callback or (lambda x: logger.info(x))

    def log(self, message):
        self.log_callback(message)

    @with_retry()
    def get_sheet_data(self, sheet_id, worksheet_name=None):
        """Fetches all records from a given sheet."""
        self.log(f"Connecting to Google Sheet ID: {sheet_id}...")
        sheet = self.client.open_by_key(sheet_id)
        if worksheet_name:
            worksheet = sheet.worksheet(worksheet_name)
        else:
            worksheet = sheet.get_worksheet(0)
            
        self.log(f"Reading data from '{worksheet.title}'...")
        return worksheet.get_all_records()

    @with_retry()
    def append_to_master(self, active_rows, absent_rows, target_tab_name, summary_stats=None):
        """Appends active rows to new tab and absent rows to Absent Staff Summary tab."""
        if not active_rows and not absent_rows:
            self.log("No data to append to Master Sheet.")
            return

        master_sheet = self.client.open_by_key(MASTER_SHEET_ID)

        if active_rows:
            if not target_tab_name:
                target_tab_name = f"Session {int(time.time())}"
                
            self.log(f"Preparing tab '{target_tab_name}' in Master Sheet...")
            
            try:
                # Check if it already exists
                main_ws = master_sheet.worksheet(target_tab_name)
                self.log(f"Tab '{target_tab_name}' already exists. Appending to it.")
            except gspread.exceptions.WorksheetNotFound:
                # Duplicate the TEMPLATE
                try:
                    template_ws = master_sheet.worksheet("TEMPLATE")
                    main_ws = template_ws.duplicate(new_sheet_name=target_tab_name)
                    # Update A1 with the tab name
                    main_ws.update(range_name='A1', values=[[target_tab_name]])
                    self.log(f"Successfully duplicated TEMPLATE into '{target_tab_name}'.")
                except Exception as e:
                    self.log(f"⚠️ Failed to duplicate TEMPLATE: {e}. Creating blank tab.")
                    main_ws = master_sheet.add_worksheet(title=target_tab_name, rows="1000", cols="20")
                    headers = list(active_rows[0].keys())
                    main_ws.append_row(headers)
            
            # Format rows as lists of values in the correct order
            headers = ['Store Number', 'Employee ID', 'Name ', 'Certification ', 'Course ID', 'Course Name', 'Completion Date', 'Certificate Issued']
            values = []
            for row in active_rows:
                values.append([row.get(h, '') for h in headers])
                
            main_ws.append_rows(values)
            self.log(f"✅ Success! Loaded {len(active_rows)} strict-formatted rows into '{target_tab_name}'.")

        if absent_rows:
            self.log(f"Appending {len(absent_rows)} rows to Absent staff...")
            try:
                absent_ws = master_sheet.worksheet("Absent staff")
            except gspread.exceptions.WorksheetNotFound:
                try:
                    absent_ws = master_sheet.worksheet("Absent Staff Summary")
                except gspread.exceptions.WorksheetNotFound:
                    self.log("⚠️ 'Absent staff' tab not found. Creating it...")
                    absent_ws = master_sheet.add_worksheet(title="Absent staff", rows="1000", cols="20")
                    headers = list(absent_rows[0].keys())
                    absent_ws.append_row(headers)
                
            # For absent rows, we just dump whatever columns we got from the dict
            values = [list(row.values()) for row in absent_rows]
            absent_ws.append_rows(values)
            self.log(f"✅ Success! Routed {len(absent_rows)} absent rows into Absent staff tab.")

        if summary_stats:
            self.log(f"Appending session summary to 'summary' tab...")
            try:
                summary_ws = master_sheet.worksheet("summary")
            except gspread.exceptions.WorksheetNotFound:
                try:
                    summary_ws = master_sheet.worksheet("Summary")
                except gspread.exceptions.WorksheetNotFound:
                    self.log("⚠️ 'summary' tab not found. Creating it...")
                    summary_ws = master_sheet.add_worksheet(title="Summary", rows="1000", cols="10")
                    summary_ws.append_row(['Course', 'HLTAID009', 'HLTAID011', 'ABSENT', 'Trainer Feedback'])
            
            summary_ws.append_row([
                summary_stats.get('Course', ''),
                summary_stats.get('HLTAID009', 0),
                summary_stats.get('HLTAID011', 0),
                summary_stats.get('ABSENT', 0),
                summary_stats.get('Trainer Feedback', 'All positive')
            ])
            self.log("✅ Success! Appended session summary.")
