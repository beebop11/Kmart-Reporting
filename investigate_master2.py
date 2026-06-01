import sys
from app.sheets_client import SheetsClient

client = SheetsClient(lambda x: None)

master_id = "1Aehi27ZPHcoj8MWwsbAwzX44EiP7xOHZBsQrzBRR4lk"
master = client.client.open_by_key(master_id)
print(f"Worksheets: {[ws.title for ws in master.worksheets()]}")
