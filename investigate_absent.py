import sys
import pandas as pd
from app.sheets_client import SheetsClient

client = SheetsClient(lambda x: None)
session_id = "1shZajESm_R3kYzBtMDhvT3RHRd-McNICdBFRLQanlrE"
session = client.client.open_by_key(session_id)
print(f"Session Sheet Title: {session.title}")
ws = session.get_worksheet(0)
df = pd.DataFrame(ws.get_all_records())
print("Columns:", df.columns.tolist())
if 'Attended' in df.columns:
    print("Unique values in 'Attended':", df['Attended'].unique())
if 'Enrolment Status' in df.columns:
    print("Unique values in 'Enrolment Status':", df['Enrolment Status'].unique())

for idx, row in df.iterrows():
    if row.get('Attended', '').lower() != 'attended' or 'absent' in str(row.get('Enrolment Status', '')).lower():
        print(f"Potential Absent Row: {row.get('Full Name')} - Attended: {row.get('Attended')} - Status: {row.get('Enrolment Status')}")
