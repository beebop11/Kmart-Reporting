import os
import time
import json
import uuid
import queue
import threading
from flask import Flask, render_template, request, jsonify, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from app.processor import process_training_data

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/kmart_uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global dictionary to hold message queues for different task sessions
task_queues = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_and_process():
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['csv_file']
    sheet_url = request.form.get('sheet_url', '')
    target_tab_name = request.form.get('target_tab_name', '')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if not sheet_url:
        return jsonify({'error': 'Sheet URL is required'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
    file.save(filepath)
    
    task_id = str(uuid.uuid4())
    task_queues[task_id] = queue.Queue()
    
    def log_callback(message):
        task_queues[task_id].put(message)
    
    # Run the processing engine in a separate thread so we can stream logs
    threading.Thread(target=run_engine, args=(task_id, sheet_url, filepath, target_tab_name, log_callback)).start()
    
    return jsonify({'task_id': task_id})

def run_engine(task_id, sheet_url, filepath, target_tab_name, log_callback):
    import traceback
    try:
        log_callback("Starting Zero-Touch Processing Engine...")
        process_training_data(sheet_url, filepath, target_tab_name, log_callback)
        log_callback("✅ Success! Processing complete.")
    except Exception as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = repr(e)
        full_traceback = traceback.format_exc()
        print(f"Exception Traceback:\n{full_traceback}") # Log to console
        log_callback(f"❌ Error: {error_msg}")
    finally:
        log_callback("DONE")

@app.route('/stream/<task_id>')
def stream(task_id):
    def event_stream():
        q = task_queues.get(task_id)
        if not q:
            yield "data: Error: Task not found\n\n"
            return
            
        while True:
            try:
                message = q.get(timeout=30)
                yield f"data: {json.dumps({'message': message})}\n\n"
                if message == "DONE":
                    break
            except queue.Empty:
                # Keep alive
                yield ":\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
