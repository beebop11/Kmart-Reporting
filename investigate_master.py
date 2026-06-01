import sys
import pandas as pd
from app.sheets_client import SheetsClient

client = SheetsClient(lambda x: None)

master_id = "1Aehi27ZPHcoj8MWwsbAwzX44EiP7xOHZBsQrzBRR4lk"
try:
    master = client.client.open_by_key(master_id)
    template_ws = master.worksheet("Template")
    print("Template first 5 rows:")
    for i, row in enumerate(template_ws.get_all_values()[:5]):
        print(f"Row {i+1}: {row}")
except Exception as e:
    print(f"Error: {e}")

