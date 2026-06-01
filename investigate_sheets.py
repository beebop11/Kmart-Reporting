import sys
import pandas as pd
from app.sheets_client import SheetsClient

client = SheetsClient(lambda x: None)

print("--- Master Sheet ---")
master_id = "1Aehi27ZPHcoj8MWwsbAwzX44EiP7xOHZBsQrzBRR4lk"
try:
    master = client.client.open_by_key(master_id)
    print(f"Worksheets: {[ws.title for ws in master.worksheets()]}")
    template_ws = None
    for ws in master.worksheets():
        if "template" in ws.title.lower():
            template_ws = ws
            break
    if template_ws:
        print(f"Template Headers: {template_ws.row_values(1)}")
    else:
        print("No template tab found.")
except Exception as e:
    print(f"Error accessing Master Sheet: {e}")

print("\n--- Session Sheet ---")
session_id = "1shZajESm_R3kYzBtMDhvT3RHRd-McNICdBFRLQanlrE"
try:
    session = client.client.open_by_key(session_id)
    ws = session.get_worksheet(0)
    print(f"Session Headers: {ws.row_values(1)}")
    print(f"Row 2: {ws.row_values(2)}")
    print(f"Row 3: {ws.row_values(3)}")
except Exception as e:
    print(f"Error accessing Session Sheet: {e}")

