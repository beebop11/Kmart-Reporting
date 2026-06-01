import sys
from app.sheets_client import SheetsClient

client = SheetsClient(lambda x: None)
master_id = "1Aehi27ZPHcoj8MWwsbAwzX44EiP7xOHZBsQrzBRR4lk"
master = client.client.open_by_key(master_id)
ws = master.worksheet(" Kmart Keysborough 13/05/2026")
for row in ws.get_all_values()[:5]:
    print(row)
