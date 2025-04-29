import os
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
from pdf_extractor import extract_text_from_pdf
from grant_identifier import identify_potential_grants

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(filepath)
        
        if extracted_text:
            # Identify potential grants in the extracted text
            potential_grants = identify_potential_grants(extracted_text)
            
            # Save extracted text to a file
            output_filename = os.path.splitext(filename)[0] + "_extracted.txt"
            output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            return jsonify({
                'success': True,
                'text': extracted_text,
                'download_url': f'/download/{output_filename}',
                'potential_grants': potential_grants
            })
        else:
            return jsonify({'error': 'Failed to extract text from PDF'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True) 