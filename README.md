
# Screen Mirroring with OCR

## Overview

**Screen Mirroring with OCR** is a Flask-based web application that captures your screen, performs Optical Character Recognition (OCR) to extract text, and allows you to interact with the captured data. The application supports live screen mirroring, capturing screenshots, and extending pages for full-text extraction.


![Screenshot (68)](https://github.com/user-attachments/assets/8a0d0ffa-413a-4d03-9023-77f136f5aca5)
![image](https://github.com/user-attachments/assets/1f67bb4a-adab-4ae9-a5ef-61d7154ab3d8)

## Features

- **Live Screen Mirroring**: Stream your screen in real-time.
- **OCR Integration**: Extract text from screenshots using OCR.
- **Capture Frames**: Capture specific frames for later processing.
- **Extend Page**: Combine multiple screenshots for comprehensive OCR.
- **Copy Text**: Easily copy extracted text to the clipboard.

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/screen-mirroring-ocr.git
   cd screen-mirroring-ocr
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**

   - **On Windows:**

     ```bash
     venv\Scripts\activate
     ```

   - **On macOS/Linux:**

     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Install Additional Dependencies**

   Make sure you have Tesseract-OCR installed on your system. Follow the instructions [here](https://github.com/tesseract-ocr/tesseract) for installation.

6. **Run the Application**

   ```bash
   python app.py
   ```

   Navigate to `http://127.0.0.1:5000` in your web browser to access the application.

## Usage

1. **Start the Application**: Run the Flask app using the command above.
2. **Interact with the Application**:
   - **Screen Mirroring**: View the live screen feed.
   - **OCR Text**: See the extracted text in real-time.
   - **Capture Frame**: Click "Capture Frame" to take a screenshot.
   - **Extend Page**: Click "Extend Page" to perform OCR on a combined view of captured frames.
   - **Copy Text**: Use the "Copy Text" button to copy extracted text to the clipboard.

## Contributing

Feel free to contribute to this project by opening issues or submitting pull requests. Please follow the guidelines below:

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Commit your changes.
4. Push your branch to GitHub.
5. Open a pull request and describe your changes.



## Acknowledgements

- **Flask**: A lightweight WSGI web application framework.
- **Tesseract-OCR**: Open-source OCR engine.
- **mss**: A cross-platform screenshot capture library.
- **Pillow**: Python Imaging Library (PIL) fork.
