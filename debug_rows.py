import sys
import pandas as pd
from app.sheets_client import SheetsClient
from app.processor import process_training_data

def log(msg):
    print(msg)

class DummyClient(SheetsClient):
    def append_to_master(self, active_rows, absent_rows, target_tab_name):
        print(f"Active rows: {len(active_rows)}")
        cpr_count = sum(1 for r in active_rows if r['Certification '] == 'CPR')
        fa_count = sum(1 for r in active_rows if r['Certification '] == 'First Aid')
        print(f"CPR count: {cpr_count}")
        print(f"First Aid count: {fa_count}")
        
        print(f"Absent rows: {len(absent_rows)}")
        for i, row in enumerate(absent_rows):
            print(f"Absent {i}: {row}")

import app.processor
app.processor.SheetsClient = DummyClient

sheet_url = "https://docs.google.com/spreadsheets/d/1shZajESm_R3kYzBtMDhvT3RHRd-McNICdBFRLQanlrE/edit"
csv_file = "/Users/bronwynriddiford/Downloads/caveman-main/Kmart_Keysborough_Calendly.csv" # Wait, do I have the CSV?
