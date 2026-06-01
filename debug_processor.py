import sys
import pandas as pd
from app.sheets_client import SheetsClient
from app.processor import normalize_key

client = SheetsClient(lambda x: None)
session_id = "1shZajESm_R3kYzBtMDhvT3RHRd-McNICdBFRLQanlrE"
session_data = client.get_sheet_data(session_id)
session_df = pd.DataFrame(session_data)

s_course_col = next((col for col in session_df.columns if 'session instance name' in col.lower()), None)
print(f"s_course_col: {s_course_col}")

row = session_df.iloc[0]
course_val = normalize_key(row.get(s_course_col, '')) if s_course_col else ''
print(f"course_val: {course_val}")
is_first_aid = 'first aid' in course_val or 'combo' in course_val
print(f"is_first_aid: {is_first_aid}")

