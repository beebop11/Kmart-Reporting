document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('csv_file');
    const fileInfo = document.getElementById('fileInfo');
    const dropContent = dropZone.querySelector('.drop-zone-content');
    const removeBtn = document.getElementById('removeFile');
    const form = document.getElementById('uploadForm');
    const runBtn = document.getElementById('runEngineBtn');
    const logSection = document.getElementById('logSection');
    const logOutput = document.getElementById('logOutput');
    const statusText = document.querySelector('.status-text');
    const pulseDot = document.querySelector('.pulse-dot');

    // Drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0 && files[0].name.endsWith('.csv')) {
            fileInput.files = files;
            updateFileInfo(files[0].name);
        } else {
            alert('Please upload a valid .csv file');
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            updateFileInfo(e.target.files[0].name);
        }
    });

    removeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileInput.value = '';
        dropContent.classList.remove('hidden');
        fileInfo.classList.add('hidden');
    });

    function updateFileInfo(fileName) {
        fileInfo.querySelector('.file-name').textContent = fileName;
        dropContent.classList.add('hidden');
        fileInfo.classList.remove('hidden');
    }

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!fileInput.files.length) {
            alert('Please select a CSV file first.');
            return;
        }

        const formData = new FormData(form);
        runBtn.disabled = true;
        runBtn.textContent = 'Processing...';
        
        // Show log section, clear old logs
        logSection.classList.remove('hidden');
        logOutput.innerHTML = '';
        statusText.textContent = 'Uploading...';
        pulseDot.style.backgroundColor = 'var(--primary)';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (response.ok) {
                startLogStream(data.task_id);
            } else {
                appendLog(`❌ Error: ${data.error}`, 'error');
                resetUI();
            }
        } catch (error) {
            appendLog(`❌ Upload failed: ${error}`, 'error');
            resetUI();
        }
    });

    function startLogStream(taskId) {
        statusText.textContent = 'Processing...';
        
        const eventSource = new EventSource(`/stream/${taskId}`);
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const msg = data.message;
            
            if (msg === "DONE") {
                eventSource.close();
                statusText.textContent = 'Completed';
                pulseDot.style.backgroundColor = 'var(--success)';
                pulseDot.style.animation = 'none';
                resetUI();
                return;
            }
            
            let type = 'normal';
            if (msg.includes('❌ Error')) type = 'error';
            if (msg.includes('✅ Success')) type = 'success';
            
            appendLog(msg, type);
        };
        
        eventSource.onerror = function() {
            eventSource.close();
            appendLog('Connection to server lost.', 'error');
            resetUI();
        };
    }

    function appendLog(message, type = 'normal') {
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        
        const time = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });
        line.textContent = `[${time}] ${message}`;
        
        logOutput.appendChild(line);
        logOutput.scrollTop = logOutput.scrollHeight; // Auto scroll
    }

    function resetUI() {
        runBtn.disabled = false;
        runBtn.textContent = 'Run Zero-Touch Processing Engine';
    }
});
