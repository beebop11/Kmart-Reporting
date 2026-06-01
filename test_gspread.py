import sys
from app.sheets_client import SheetsClient
import traceback

try:
    print("Initializing client...")
    client = SheetsClient(lambda x: print(x))
    
    sheet_id = "1shZajESm_R3kYzBtMDhvT3RHRd-McNICdBFRLQanlrE"
    print(f"Testing access to {sheet_id}...")
    
    data = client.get_sheet_data(sheet_id)
    print(f"Success! Retrieved {len(data)} rows.")
except Exception as e:
    print("FAILED!")
    print(repr(e))
    traceback.print_exc()
