import sys
import threading
from flask import Flask, Response, render_template_string, jsonify, request
import mss
from PIL import Image
import io
import pytesseract
import webview
import os
import signal
from waitress import serve
import requests
import socket

app = Flask(__name__)
flask_thread = None
server_running = False


# Store captured images
captured_images = []

# Define the OCR function
def perform_ocr(image):
    text = pytesseract.image_to_string(image)
    return text

def generate_frames():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Use the primary monitor; adjust as needed
        while True:
            img = sct.grab(monitor)
            img = Image.frombytes('RGB', img.size, img.bgra, 'raw', 'BGRX')
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            text = perform_ocr(img)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.read() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_frame', methods=['POST'])
def capture_frame():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        img = Image.frombytes('RGB', img.size, img.bgra, 'raw', 'BGRX')
        captured_images.append(img)
    return jsonify({"status": "Frame captured successfully"}), 200

@app.route('/extend_page', methods=['POST'])
def extend_page():
    if not captured_images:
        return jsonify({"error": "No images captured"}), 400
    
    total_height = sum(img.size[1] for img in captured_images)
    max_width = max(img.size[0] for img in captured_images)
    stitched_image = Image.new('RGB', (max_width, total_height))
    
    y_offset = 0
    for img in captured_images:
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.size[1]
    
    full_text = perform_ocr(stitched_image)
    captured_images.clear()
    
    return jsonify({"full_text": full_text}), 200

@app.route('/')
def index():
    return render_template_string('''
        <html>
            <head>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #e0f7fa;
                        color: #37474f;
                    }
                    h1 {
                        text-align: center;
                        padding: 20px 0;
                        color: #00796b;
                        font-size: 2.5em;
                    }
                    .container {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        flex-direction: column;
                        width: 80%;
                        margin: auto;
                        padding: 20px;
                        background-color: #ffffff;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                        border-radius: 10px;
                    }
                    .left {
                        width: 100%;
                        text-align: center;
                    }
                    .left img {
                        width: 100%;
                        border-radius: 10px;
                        margin-bottom: 20px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    }
                    .left #ocr_text {
                        padding: 10px;
                        font-size: 1.2em;
                        color: #00796b;
                        background-color: #e0f2f1;
                        border-radius: 5px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        margin-bottom: 20px;
                        white-space: pre-wrap; /* Preserve formatting for multiline text */
                    }
                    .button-container {
                        display: flex;
                        justify-content: space-around;
                        width: 100%;
                    }
                    .button-container button {
                        padding: 10px 20px;
                        font-size: 1em;
                        background-color: #00796b;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        transition: background-color 0.3s;
                        margin: 10px 5px;
                    }
                    .button-container button:hover {
                        background-color: #004d40;
                    }
                    .button-container button.copy {
                        background-color: #ffa726;
                    }
                    .button-container button.copy:hover {
                        background-color: #f57c00;
                    }
                </style>
            </head>
            <body>
                <h1>Screen Mirroring with OCR</h1>
                <div class="container">
                    <div class="left">
                        <img src="/video_feed">
                        <div id="ocr_text">Text from screen will appear here...</div>
                        <div class="button-container">
                            <button class="copy" onclick="copyText()">Copy Text</button>
                            <button onclick="captureFrame()">Capture Frame</button>
                            <button onclick="extendPage()">Extend Page</button>
                        </div>
                    </div>
                </div>
                <script>
                    // Update OCR text periodically
                    setInterval(function() {
                        fetch('/ocr_text')
                            .then(response => response.text())
                            .then(text => document.getElementById('ocr_text').innerText = text);
                    }, 1000); // Update every second

                    // Capture frame for extending page
                    function captureFrame() {
                        fetch('/capture_frame', { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                alert(data.status);
                            })
                            .catch(err => {
                                console.error('Failed to capture frame: ', err);
                            });
                    }

                    // Extend page and perform OCR on full content
                    function extendPage() {
                        fetch('/extend_page', { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                if (data.error) {
                                    alert(data.error);
                                } else {
                                    document.getElementById('ocr_text').innerText = data.full_text;
                                }
                            })
                            .catch(err => {
                                console.error('Failed to extend page: ', err);
                            });
                    }

                    // Copy OCR text to clipboard
                    function copyText() {
                        const text = document.getElementById('ocr_text').innerText;
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        document.body.appendChild(textArea);
                        textArea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textArea);
                        alert('Text copied to clipboard');
                    }
                </script>
            </body>
        </html>
    ''')

@app.route('/ocr_text')
def ocr_text():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        img = Image.frombytes('RGB', img.size, img.bgra, 'raw', 'BGRX')
        text = perform_ocr(img)
        return text


# Function to start Flask
def start_flask():
    global server_running
    server_running = True
    serve(app, host='0.0.0.0', port=8080, threads=8)  # Increase the number of threads


# WebView API handlers
class API:
    def start(self):
        global flask_thread
        if server_running:
            return  # If Flask is already running, do nothing

        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()

        # Get the local IP address of the device
        local_ip = socket.gethostbyname(socket.gethostname())

        # Update status text to show the running URLs dynamically
        webview.windows[0].evaluate_js(f"""
            document.getElementById('status').innerText = 'Status: ON - http://localhost:8080\\n'
            + 'Running on all addresses (0.0.0.0)\\n'
            + 'Running on http://127.0.0.1:8080\\n'
            + 'Running on http://{local_ip}:8080';
        """)

    def stop(self):
        global server_running
        if not server_running:
            return  # Already stopped

        server_running = False  # Mark as stopped

        # Kill the process running on port 8080
        try:
            if os.name == 'nt':  # Windows
                os.system("netstat -ano | findstr :8080 | findstr LISTENING | for /F \"tokens=5\" %P in ('more') do TaskKill /PID %P /F")
            else:  # Linux/Mac
                os.system("fuser -k 8080/tcp")
        except Exception as e:
            print("Error stopping Flask:", e)

        # Update UI
        webview.windows[0].evaluate_js("""
            document.getElementById('status').innerText = 'Status: OFF';
        """)

# Flask route to allow stopping the server
@app.route('/shutdown', methods=['GET'])
def shutdown():
    global server_running
    server_running = False
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func:
        shutdown_func()
    return "Server shutting down..."

# Function to create GUI
def create_gui():
    html = """
    <html>
    <head>
        <style>
            body { text-align: center; font-family: Arial, sans-serif; padding: 20px; }
            button { padding: 10px 20px; font-size: 16px; margin: 10px; }
        </style>
    </head>
    <body>
        <h2>Screen Sharing with OCR</h2>
        <button onclick="pywebview.api.start()">Start Screen Sharing</button>
        <button onclick="pywebview.api.stop()">Stop</button>
        <p id="status">Status: OFF</p>
    </body>
    </html>
    """
    webview.create_window("Screen Sharing App", html=html, js_api=API())
    webview.start()

if __name__ == '__main__':
    create_gui()