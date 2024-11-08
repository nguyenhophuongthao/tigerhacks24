from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import cv2
from pyzbar.pyzbar import decode
import numpy as np

app = Flask(__name__)
app.secret_key = "supersecretkey"
DB_PATH = "food_expiration.db"

# Database setup function
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS food_items (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       expiration_date TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Home page - list all items
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, expiration_date FROM food_items")
    items = cursor.fetchall()
    conn.close()
    
    # Check for items expiring within 3 days and add notifications
    notifications = []
    today = datetime.today()
    for item_id, name, exp_date in items:
        days_left = (datetime.strptime(exp_date, "%Y-%m-%d") - today).days
        if 0 <= days_left <= 3:
            notifications.append(f"{name} expires in {days_left} day(s).")
    
    return render_template('index.html', items=items, notifications=notifications)

# Route to add new food items
@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    expiration_date = request.form['expiration_date']
    
    try:
        # Validate date format
        datetime.strptime(expiration_date, "%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO food_items (name, expiration_date) VALUES (?, ?)", (name, expiration_date))
        conn.commit()
        conn.close()
        flash(f"{name} added with expiration date {expiration_date}.", "success")
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
    
    return redirect(url_for('index'))

# Route to delete an item by ID
@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item removed successfully.", "success")
    return redirect(url_for('index'))

# Route to upload a barcode image
@app.route('/upload_barcode', methods=['POST'])
def upload_barcode():
    if 'barcode_image' not in request.files:
        flash("No file selected for uploading", "danger")
        return redirect(url_for('index'))
    
    file = request.files['barcode_image']
    if file.filename == '':
        flash("No file selected", "danger")
        return redirect(url_for('index'))
    
    # Read the image file and decode it
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    barcodes = decode(img)

    if barcodes:
        barcode_data = barcodes[0].data.decode('utf-8')
        flash(f"Scanned item: {barcode_data}. Please enter expiration date manually.", "info")
    else:
        flash("No barcode detected in uploaded image.", "danger")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    setup_database()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))         # app.run(host="0.0.0.0", port=5001)
