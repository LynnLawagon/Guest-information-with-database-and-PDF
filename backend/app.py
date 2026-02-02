from flask import Flask, request, jsonify, render_template, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import cv2
import base64
import easyocr
import re
import numpy as np
import io
import os
from datetime import datetime
import mysql.connector

app = Flask(__name__, template_folder="templates")
PDF_FOLDER = os.path.join(app.root_path, "static", "PDFs")
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OCR
reader = easyocr.Reader(["en"], gpu=False)

# Database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="db_ocr_results"
)

#Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    img_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(img_path)
    img_path_db = f"uploads/{file.filename}"

    # Read image with OpenCV for OCR
    in_memory = io.BytesIO()
    file.seek(0)
    file.save(in_memory)
    data = np.frombuffer(in_memory.getvalue(), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)

    results = reader.readtext(img)
    texts = [t.strip() for _, t, s in results if s > 0.4]
    full_text = " ".join(texts).upper()

    # Regex
    dob_match = re.search(r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2}\s+\d{4}", full_text)
    dob_mysql = None
    if dob_match:
        try:
            dob_mysql = datetime.strptime(dob_match.group(0), "%B %d %Y").date()
        except:
            pass

    last_name = re.search(r"APELYIDO/ LAST NAME\s+([A-Z\s]+?)(?=\sMGA PANGALAN/)", full_text)
    first_name = re.search(r"MGA PANGALAN/ GIVEN NAMES\s+([A-Z\s]+?)(?=\sGITNANG APELYIDO/)", full_text)
    middle_name = re.search(r"GITNANG APELYIDO/.*?MIDDLE NAME\s*([A-Z\s]+?)(?=\sPETSA NG)", full_text)
    address = re.search(r"TIRAHAN/ADDRESS\s+(.+)", full_text)
    contact = re.search(r"CONTACT\s+(.+)", full_text)
    gender = re.search(r"SEX\s+([A-Z])", full_text)

    return jsonify({
        "ID_type": "",
        "First_name": first_name.group(1).strip() if first_name else "",
        "Middle_name": middle_name.group(1).strip() if middle_name else "",
        "Last_name": last_name.group(1).strip() if last_name else "",
        "Date_of_birth": dob_mysql.strftime("%Y-%m-%d") if dob_mysql else "",
        "Gender": gender.group(1).strip() if gender else "",
        "Contact": contact.group(1).strip() if contact else "",
        "Address": address.group(1).strip() if address else "",
        "Img_path": img_path_db
    })

# Camera OCR
@app.route("/scan", methods=["POST"])
def scan():
    data = request.json
    img_data = data["image"].split(",")[1]
    img_bytes = base64.b64decode(img_data)
    img_array = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # Save camera image
    filename = f"scan_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    img_path = os.path.join(UPLOAD_FOLDER, filename)
    cv2.imwrite(img_path, img)
    img_path_db = f"uploads/{filename}"

    results = reader.readtext(img)
    texts = [t.strip() for _, t, s in results if s > 0.4]
    full_text = " ".join(texts).upper()

    # Regex
    dob_match = re.search(r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+\d{1,2}\s+\d{4}", full_text)
    dob_mysql = None
    if dob_match:
        try:
            dob_mysql = datetime.strptime(dob_match.group(0), "%B %d %Y").date()
        except:
            pass

    last_name = re.search(r"APELYIDO/ LAST NAME\s+([A-Z\s]+?)(?=\sMGA PANGALAN/)", full_text)
    first_name = re.search(r"MGA PANGALAN/ GIVEN NAMES\s+([A-Z\s]+?)(?=\sGITNANG APELYIDO/)", full_text)
    middle_name = re.search(r"GITNANG APELYIDO/.*?MIDDLE NAME\s*([A-Z\s]+?)(?=\sPETSA NG)", full_text)
    address = re.search(r"TIRAHAN/ADDRESS\s+(.+)", full_text)
    gender = re.search(r"SEX\s+([A-Z])", full_text)
    contact = re.search(r"CONTACT\s+(.+)", full_text)

    return jsonify({
        "ID_type": "",
        "First_name": first_name.group(1).strip() if first_name else "",
        "Middle_name": middle_name.group(1).strip() if middle_name else "",
        "Last_name": last_name.group(1).strip() if last_name else "",
        "Date_of_birth": dob_mysql.strftime("%Y-%m-%d") if dob_mysql else "",
        "Address": address.group(1).strip() if address else "",
        "Gender": gender.group(1).strip() if gender else "",
        "Contact": contact.group(1).strip() if contact else "",
        "Img_path": img_path_db 
    })

# Save guest
@app.route("/save_guest", methods=["POST"])
def save_guest():
    data = request.json
    dob = data.get("Date_of_birth") or None
    cursor = db.cursor()

    gender_map = {
        "Male": 1,
        "Female": 2,
        "Other": 3
    }

    gender_id = gender_map.get(data.get("Gender",""), None)

    cursor.execute("""
        INSERT INTO tbl_guests (ID_type, First_name, Middle_name, Last_name, Date_of_birth, Gender_id, Contact, Address, Img_path)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data.get("ID_type",""),
        data.get("First_name",""),
        data.get("Middle_name",""),
        data.get("Last_name",""),
        dob,
        gender_id,
        data.get("Contact"),
        data.get("Address",""),
        data.get("Img_path","")
    ))
    db.commit()
    return jsonify({"status":"success"})

# Export PDF
@app.route("/export-latest-pdf")
def export_latest_pdf():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tbl_guests ORDER BY ID_num DESC LIMIT 1")
    data = cursor.fetchone()
    if not data:
        return "No records found", 404

    filename = f"guest_{data['ID_num']}.pdf"
    pdf_path = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    margin = 50
    image_width = 150
    image_height = 100

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - margin, "GUEST INFORMATION")
    c.setFont("Helvetica", 10)
    c.drawString(margin, height - margin - 20, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Image
    img_path = os.path.join(app.root_path, "static", data["Img_path"].replace("\\", "/"))
    if os.path.exists(img_path):
        try:
            img = ImageReader(img_path)
            c.drawImage(img, margin, height - margin - image_height - 40, width=image_width, height=image_height, preserveAspectRatio=True)
        except Exception as e:
            print("Image error:", e)

    # Text 
    text_x = margin + image_width + 20
    text_y = height - margin - 40
    c.setFont("Helvetica", 12)
    c.drawString(text_x, text_y, f"First Name: {data['First_name']}")
    text_y -= 18
    c.drawString(text_x, text_y, f"Middle Name: {data['Middle_name']}")
    text_y -= 18
    c.drawString(text_x, text_y, f"Last Name: {data['Last_name']}")
    text_y -= 18
    c.drawString(text_x, text_y, f"DOB: {data['Date_of_birth'] or 'N/A'}")
    text_y -= 18
    
    gender_map_rev = {
        1: "Male",      
        2: "Female",
        3: "Other"
    }
    gender_text = gender_map_rev.get(data['Gender_id'], "N/A")
    c.drawString(text_x, text_y, f"Gender: {gender_text}")
    
    text_y -= 18
    c.drawString(text_x, text_y, f"Contact: {data['Contact']}")
    text_y -= 18
    c.drawString(text_x, text_y, f"ID Type: {data['ID_type']}")

    # Address 
    addr_y = height - margin - image_height - 60 - 18 * 5
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, addr_y, "Address:")
    c.setFont("Helvetica", 10)
    addr_text = c.beginText(margin, addr_y - 18)
    addr_text.setLeading(14)

    #long addresses
    address = (data["Address"] or "").replace("\n", " ")
    max_chars_per_line = 90 
    while address:
        line = address[:max_chars_per_line]
        addr_text.textLine(line)
        address = address[max_chars_per_line:]
    c.drawText(addr_text)

    c.showPage()
    c.save()
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
