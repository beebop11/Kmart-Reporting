import sys
from app.sheets_client import SheetsClient

client = SheetsClient(lambda x: None)
master_id = "1Aehi27ZPHcoj8MWwsbAwzX44EiP7xOHZBsQrzBRR4lk"
master = client.client.open_by_key(master_id)
titles = [ws.title for ws in master.worksheets()]
print(f"First 10 Worksheets: {titles[:10]}")

template_name = None
for t in titles:
    if 'template' in t.lower():
        template_name = t
        break

if template_name:
    ws = master.worksheet(template_name)
    print(f"Template '{template_name}' headers:")
    print(ws.row_values(1))
    print(ws.row_values(2))
else:
    print("No template found.")
