import pandas as pd
from flask import Flask, request, send_file, render_template_string
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_csv(file_path):
    df = pd.read_csv(file_path)
    
    # Define column mapping
    column_mapping = {
        "Virtual Card": "Card number",
        "Authorization": "Amount",
        "Merchant": "Description",
        "Auth Time": "Date",
        "Status": "Authorization"
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Ensure exact card number format (16 digits, numeric only)
    df["Card number"] = df["Card number"].astype(str).str.replace(r'\D', '', regex=True)
    df = df[df["Card number"].str.len() == 16]
    
    # Extract numeric values from Authorization (Amount)
    df["Amount"] = df["Amount"].astype(str).str.replace(r'[^0-9.]', '', regex=True)
    
    # Convert date format from YYYY-MM-DD to DD/MM/YYYY
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.strftime("%d/%m/%Y")
    
    # Normalize Authorization Status
    df["Authorization"] = df["Authorization"].str.lower()
    df = df[~df["Authorization"].str.contains("pending", na=False)]  # Remove Pending rows
    df.loc[df["Authorization"].str.contains("settled", na=False), "Authorization"] = "refund"
    df.loc[df["Authorization"].str.contains("declined", na=False), "Authorization"] = "declined"
    df.loc[df["Authorization"].str.contains("authorized", na=False), "Authorization"] = "authorized"
    
    # Save cleaned file
    output_file = os.path.join(UPLOAD_FOLDER, "cleaned_data.csv")
    df.to_csv(output_file, index=False)
    return output_file

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            cleaned_file = process_csv(file_path)
            return send_file(cleaned_file, as_attachment=True)
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSV Formatter</title>
        </head>
        <body>
            <h2>Upload CSV to Format</h2>
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <button type="submit">Upload & Process</button>
            </form>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
