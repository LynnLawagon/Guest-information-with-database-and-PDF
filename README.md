# Guest-information-with-database-and-PDF
This system is a Guest Information Management System that automates data capture from IDs using OCR. It stores extracted details in a database and allows generating PDF reports of guest information, including photos, personal details, and contact information. The system supports both file uploads and real-time camera scanning.

Overview
This system is a Guest Information Management System that captures guest details from IDs using OCR (Optical Character Recognition), stores the data in a MySQL database, and allows exporting PDF reports including guest photos. It supports both file upload and real-time camera scanning.

Features
-Upload ID images or use a camera to scan IDs.
-Automatically extract personal details (Name, DOB, Gender, Contact, Address, etc.).
-Save data to a MySQL database.
-Generate PDF reports of guest information.
-User-friendly web interface using Flask.

Prerequisites
-Before running the system, make sure you have the following installed:
-Python 3.10+
-Download from Python official website

MySQL Server
-Download from MySQL official website
-Make sure you have a username (e.g., root) and password set up.

Git (optional, if using repository)
-Download from Git official website

Setup Instructions
1. Clone the repository (if using Git)
git clone <repository-url>
cd <repository-folder>

2. Create a Python virtual environment (recommended)
python -m venv venv
# Activate environment
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

3. Install Python dependencies
pip install --upgrade pip
pip install flask mysql-connector-python easyocr opencv-python-headless reportlab numpy

Notes:
-easyocr requires torch automatically, but pip will install it.
-opencv-python-headless is preferred for servers without GUI.
-You can also install opencv-python if you want a full OpenCV GUI support.

Database Setup
-Create Database
CREATE DATABASE db_ocr_results;

-Create Tables
CREATE TABLE tbl_gender (
    Gender_id INT AUTO_INCREMENT PRIMARY KEY,
    Gender_name VARCHAR(50)
);

INSERT INTO tbl_gender (Gender_name) VALUES ('Male'), ('Female'), ('Other');

CREATE TABLE tbl_guests (
    ID_num INT AUTO_INCREMENT PRIMARY KEY,
    ID_type VARCHAR(100),
    First_name VARCHAR(100),
    Middle_name VARCHAR(100),
    Last_name VARCHAR(100),
    Date_of_birth DATE,
    Gender_id INT,
    Contact VARCHAR(50),
    Address TEXT,
    Img_path VARCHAR(255),
    Created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (Gender_id) REFERENCES tbl_gender(Gender_id)
);

Running the Application
-Open a terminal and activate your Python environment.
-Navigate to the project folder.

Run the Flask app:
-python app.py

Open your browser and go to:
-http://127.0.0.1:5000

How to Use
-Upload an ID
-Click the image area or “Upload your ID here”.
-Choose an ID image (e.g., School ID, National ID).
-OCR will automatically extract details.
-Use Camera
-Click Use Camera to activate your webcam.
-Point your ID to the camera.
-Click Snap to capture and extract details.
-Edit or Confirm Data
-All extracted fields will appear in the form.
-You can manually edit any details before saving.
-Save Guest
-Click Save to store the guest information into the database.
-Export PDF
-Click Export PDF to download a PDF report of the latest guest entry.
