from flask import Flask, Response, render_template_string, jsonify, request
import mss
from PIL import Image
import io
import pytesseract

app = Flask(__name__)

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
            # Capture the screen
            img = sct.grab(monitor)
            # Convert to PIL Image
            img = Image.frombytes('RGB', img.size, img.bgra, 'raw', 'BGRX')
            # Save to a bytes buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            # Perform OCR
            text = perform_ocr(img)
            # Yield the frame and the captured text
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
    
    # Stitch images together
    total_height = sum(img.size[1] for img in captured_images)
    max_width = max(img.size[0] for img in captured_images)
    stitched_image = Image.new('RGB', (max_width, total_height))
    
    y_offset = 0
    for img in captured_images:
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.size[1]
    
    # Perform OCR on the stitched image
    full_text = perform_ocr(stitched_image)
    
    # Clear captured images after processing
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
    # Capture a single frame for OCR
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        img = Image.frombytes('RGB', img.size, img.bgra, 'raw', 'BGRX')
        text = perform_ocr(img)
        return text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
