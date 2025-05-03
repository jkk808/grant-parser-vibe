"""
Flask application for the Grant Parser.
Provides a web interface for uploading documents and viewing extracted data.
"""

import os
import mimetypes
import datetime
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Import configuration and core processing functions
import config
from doc_ai_client import process_document_local
from parser import parse_doc_ai_response

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER


def allowed_file(filename):
    """Checks if the uploaded file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Renders the main upload page."""
    # Pass current year to template for footer
    current_year = datetime.datetime.now().year
    return render_template('index.html', year=current_year)

@app.route('/process', methods=['POST'])
def process_file():
    """Handles file upload, processing via Document AI, and displays results."""
    current_year = datetime.datetime.now().year # For footer on results page

    if 'file' not in request.files:
        flash('No file part in the request', 'warning')
        return redirect(request.url)
    file = request.files['file']

    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Ensure upload folder exists (it should be created by config.py, but double-check)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
             try:
                 os.makedirs(app.config['UPLOAD_FOLDER'])
             except OSError as e:
                 flash(f'Could not create upload directory: {e}', 'danger')
                 return redirect(url_for('index')) # Redirect back to index
                 
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(file_path)
            print(f"File saved temporarily to: {file_path}")

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Make a reasonable guess if determination fails (e.g., for some TIFFs)
                ext = os.path.splitext(filename)[1].lower()
                if ext == '.pdf': mime_type = 'application/pdf'
                elif ext in ['.tif', '.tiff']: mime_type = 'image/tiff'
                elif ext in ['.jpg', '.jpeg']: mime_type = 'image/jpeg'
                elif ext == '.png': mime_type = 'image/png'
                else:
                     flash(f'Could not determine MIME type for {filename}', 'danger')
                     return render_template('results.html', filename=filename, error=f'Could not determine file type.', year=current_year)
            
            print(f"Determined MIME type: {mime_type}")

            # --- Call Document AI --- 
            # Ensure GCP configuration is set in config.py or environment variables
            if not config.GCP_PROJECT_ID or config.GCP_PROJECT_ID == "your-gcp-project-id":
                raise ValueError("GCP_PROJECT_ID is not configured in config.py or environment variables.")
            if not config.DOC_AI_LOCATION:
                 raise ValueError("DOC_AI_LOCATION is not configured.")
            if not config.DOC_AI_PROCESSOR_ID or config.DOC_AI_PROCESSOR_ID == "your-processor-id":
                raise ValueError("DOC_AI_PROCESSOR_ID is not configured.")

            print("Processing document with Google Document AI...")
            doc_ai_document = process_document_local(
                project_id=config.GCP_PROJECT_ID,
                location=config.DOC_AI_LOCATION,
                processor_id=config.DOC_AI_PROCESSOR_ID,
                file_path=file_path,
                mime_type=mime_type
            )
            print("Document AI processing finished.")

            # --- Parse the response --- 
            print("Parsing Document AI response...")

            # +++ DEBUG: Print the raw Document object from the API +++
            print("\n>>> RAW DOCUMENT AI RESPONSE OBJECT (START) <<<")
            print(doc_ai_document)
            print(">>> RAW DOCUMENT AI RESPONSE OBJECT (END) <<<")
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

            parsed_data = parse_doc_ai_response(doc_ai_document)
            print("here", parsed_data)
            print("Parsing finished.")
            
            # Clean up the uploaded file
            try:
                 os.remove(file_path)
                 print(f"Removed temporary file: {file_path}")
            except OSError as e:
                 print(f"Warning: Could not remove temporary file {file_path}: {e}")

            # --- Display results ---
            # Pass the actual parsed data to the template
            return render_template('results.html', results=parsed_data, filename=filename, year=current_year)

        except Exception as e:
            print(f"Error during processing: {e}")
            # Clean up the file even if there's an error
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as remove_err:
                    print(f"Warning: Could not remove temporary file {file_path} after error: {remove_err}")
            flash(f'An error occurred during processing: {e}', 'danger')
            # Render the results page but show the error message
            return render_template('results.html', filename=filename, error=str(e), year=current_year)

    else:
        flash('Invalid file type. Allowed types are: pdf, png, jpg, jpeg, tiff', 'warning')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Make sure authentication is set up!
    # E.g., run `gcloud auth application-default login` OR
    # Set the GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to your key file.
    print("Starting Flask development server...")
    print(f"Ensure Google Cloud credentials are set up (e.g., run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS).")
    print(f"Ensure GCP Project ID, Location, and Processor ID are set correctly in config.py or environment variables.")
    app.run(debug=True) # debug=True allows automatic reloading during development 