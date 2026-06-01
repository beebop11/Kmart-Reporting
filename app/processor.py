import re
import pandas as pd
from app.sheets_client import SheetsClient

def extract_sheet_id(url):
    """Extracts the unique ID from a Google Sheet URL."""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        return match.group(1)
    raise ValueError("Invalid Google Sheet URL provided.")

def normalize_key(text):
    """Normalize text for matching (lowercase, strip whitespace)."""
    if pd.isna(text):
        return ""
    return str(text).strip().lower()

def process_training_data(sheet_url, csv_filepath, target_tab_name, log_callback):
    client = SheetsClient(log_callback)
    
    # 1. Extract Sheet ID
    log_callback("Extracting target ID from Google Sheet URL...")
    sheet_id = extract_sheet_id(sheet_url)
    
    # 2. Fetch Session Data
    session_data = client.get_sheet_data(sheet_id)
    if not session_data:
        raise ValueError("The provided Google Sheet is empty or could not be read.")
    
    session_df = pd.DataFrame(session_data)
    log_callback(f"Successfully read {len(session_df)} rows from Session Sheet.")
    
    # 3. Read Calendly CSV
    log_callback("Parsing uploaded Calendly CSV file...")
    try:
        calendly_df = pd.read_csv(csv_filepath)
        log_callback(f"Read {len(calendly_df)} rows from Calendly CSV.")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")
        
    # Standardize column names if needed, we assume 'Email Address' and 'Full Name', 'Store Number', 'Employee ID'
    # Calendly might have 'Email', 'Name' instead of 'Email Address' and 'Full Name'. We'll try to find the best match.
    email_col = next((col for col in calendly_df.columns if 'email' in col.lower()), None)
    name_col = next((col for col in calendly_df.columns if 'name' in col.lower() and 'event' not in col.lower()), None)
    store_col = next((col for col in calendly_df.columns if 'store number' in col.lower()), None)
    emp_col = next((col for col in calendly_df.columns if 'employee' in col.lower() or 'id' in col.lower()), None)
    
    if not email_col or not name_col:
        log_callback("⚠️ Warning: Could not find strict 'Email' or 'Name' columns in Calendly CSV. Matching might fail.")

    # Convert Calendly to a lookup dictionary
    calendly_lookup = {}
    for _, row in calendly_df.iterrows():
        email_key = normalize_key(row.get(email_col, '')) if email_col else ''
        name_key = normalize_key(row.get(name_col, '')) if name_col else ''
        
        data = {
            'Store Number': row.get(store_col, 'N/A') if store_col else 'N/A',
            'Employee ID': row.get(emp_col, 'N/A') if emp_col else 'N/A'
        }
        
        if email_key:
            calendly_lookup[email_key] = data
        if name_key:
            calendly_lookup[name_key] = data

    active_rows = []
    absent_rows = []
    
    # Check session sheet headers
    s_email_col = next((col for col in session_df.columns if 'email' in col.lower()), None)
    
    # Try exact match first, fallback to containing 'name' but not 'session'
    s_name_col = next((col for col in session_df.columns if col.strip().lower() == 'full name'), None)
    if not s_name_col:
        s_name_col = next((col for col in session_df.columns if 'name' in col.lower() and 'session' not in col.lower()), None)
        
    s_status_col = next((col for col in session_df.columns if 'status' in col.lower()), None)
    s_date_col = next((col for col in session_df.columns if 'date' in col.lower()), None)
    s_usi_col = next((col for col in session_df.columns if 'usi verified' in col.lower()), None)
    
    # We will use Session Instance Name for course detection as it always contains "CPR" or "First Aid"
    s_course_col = next((col for col in session_df.columns if 'session instance name' in col.lower()), None)

    log_callback("Stitching matching records and applying strict formatting...")
    match_count = 0
    cpr_only_count = 0
    combo_count = 0
    
    # Use a dictionary to deduplicate absent rows
    absent_dict = {}

    for _, row in session_df.iterrows():
        name_val = str(row.get(s_name_col, '')) if s_name_col else ''
        course_val = normalize_key(row.get(s_course_col, '')) if s_course_col else ''
        date_val = str(row.get(s_date_col, '')) if s_date_col else ''
        status_val = normalize_key(row.get(s_status_col, '')) if s_status_col else ''
        usi_val = normalize_key(row.get(s_usi_col, '')) if s_usi_col else ''
        
        # Match with Calendly
        email_key = normalize_key(row.get(s_email_col, '')) if s_email_col else ''
        name_key = normalize_key(name_val)
        
        match_data = calendly_lookup.get(email_key) or calendly_lookup.get(name_key)
        
        store_num = match_data['Store Number'] if match_data else 'Not Found'
        emp_id = match_data['Employee ID'] if match_data else 'Not Found'
        
        if match_data:
            match_count += 1
            
        attended_val = normalize_key(row.get('Attended', ''))
        
        # Business Logic: Determine Course Type
        is_first_aid = 'first aid' in course_val or 'combo' in course_val
        
        if attended_val == 'absent':
            # Format strictly for Absent Staff sheet
            cert_val = 'First Aid' if is_first_aid else 'CPR'
            
            # Deduplicate by Employee ID (or Full Name if ID is missing)
            dedup_key = emp_id if emp_id != 'Not Found' else name_val
            
            if dedup_key not in absent_dict:
                absent_dict[dedup_key] = {
                    'Store': store_num,
                    'Employee ID': emp_id,
                    'Full Name': name_val,
                    'Certification ': cert_val,
                    'Course Date': date_val,
                    'Notes': 'Absent'
                }
            continue

        # Calculate Certificate Issued Logic
        # Complete + Verified = Yes
        # Complete + Not Verified = No - Missing USI
        # Not Complete = No - Incomplete Learning
        cert_issued = "No"
        if 'complete' in status_val and usi_val == 'yes':
            cert_issued = "Yes"
        elif 'complete' in status_val and usi_val != 'yes':
            cert_issued = "No - Missing USI"
        else:
            cert_issued = "No - Incomplete Learning"
            
        def create_formatted_row(cert, c_id, c_name):
            return {
                'Store Number': store_num,
                'Employee ID': emp_id,
                'Name ': name_val,
                'Certification ': cert,
                'Course ID': c_id,
                'Course Name': c_name,
                'Completion Date': date_val,
                'Certificate Issued': cert_issued
            }

        # Emit Active Rows based on Course Type
        if is_first_aid:
            combo_count += 1
            # Emit CPR
            active_rows.append(create_formatted_row('CPR', 'CPRY124022021', 'CPRY124022021'))
            # Emit First Aid
            active_rows.append(create_formatted_row('First Aid', 'First Aid AUS 16032021', 'FAAUS16032021'))
        else:
            cpr_only_count += 1
            # Assume it's just CPR
            active_rows.append(create_formatted_row('CPR', 'CPRY124022021', 'CPRY124022021'))
            
    absent_rows.extend(list(absent_dict.values()))

    log_callback(f"Stitching completed. {match_count} records matched with Calendly data.")
    log_callback(f"Generated {len(active_rows)} active training rows and identified {len(absent_rows)} absent staff.")

    summary_stats = {
        'Course': target_tab_name or f"Session {pd.Timestamp.now().strftime('%d/%m/%Y')}",
        'HLTAID009': cpr_only_count,
        'HLTAID011': combo_count,
        'ABSENT': len(absent_rows),
        'Trainer Feedback': 'All positive'
    }

    # 4. Push to Master Sheet
    client.append_to_master(active_rows, absent_rows, target_tab_name, summary_stats)
