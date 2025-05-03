"""
Main entry point for the grant parsing application.
Handles command-line arguments and orchestrates the parsing process.
"""

import argparse
import os
import mimetypes # For determining file type
import json # For JSON output
import csv # For CSV output
import io # For CSV output

# Import functions and config from other modules
from doc_ai_client import process_document_local
from parser import parse_doc_ai_response
# from output_formatter import format_output # Keep commented if not using
from config import GCP_PROJECT_ID, DOC_AI_LOCATION, DOC_AI_PROCESSOR_ID, ALLOWED_EXTENSIONS

def get_mime_type(file_path):
    """Determines the MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type

def main():
    parser = argparse.ArgumentParser(description='Parse grant documents using Google Document AI.')
    parser.add_argument('file_path', help='Path to the grant document file (PDF, PNG, JPG, TIFF).')
    parser.add_argument('-o', '--output', help='Path to the output file (JSON or CSV). Default: output.json', default='output.json')

    args = parser.parse_args()

    file_path = args.file_path
    output_path = args.output

    # --- Input Validation ---
    if not os.path.exists(file_path):
        print(f"Error: Input file not found at {file_path}")
        return

    # Check file extension
    file_extension = os.path.splitext(file_path)[1].lower().strip('.')
    if file_extension not in ALLOWED_EXTENSIONS:
        print(f"Error: File type '.{file_extension}' is not allowed. Allowed types: {ALLOWED_EXTENSIONS}")
        return

    # Determine MIME type
    mime_type = get_mime_type(file_path)
    if not mime_type:
        print(f"Error: Could not determine MIME type for file: {file_path}")
        # Optionally attempt a default or raise an error
        # mime_type = 'application/pdf' # Example fallback
        return

    print(f"Processing document: {file_path} (MIME Type: {mime_type})")

    # --- Configuration Check ---
    if not all([GCP_PROJECT_ID, DOC_AI_LOCATION, DOC_AI_PROCESSOR_ID]):
        print("Error: Missing Google Cloud configuration (Project ID, Location, or Processor ID).")
        print("Please ensure GCP_PROJECT_ID, DOC_AI_LOCATION, and DOC_AI_PROCESSOR_ID are set in your .env file or environment variables.")
        return

    try:
        # 1. Send document to Document AI for processing
        print(f"Sending {file_path} to Document AI processor: {DOC_AI_PROCESSOR_ID} in {DOC_AI_LOCATION}...")
        doc_ai_document = process_document_local(
            project_id=GCP_PROJECT_ID,
            location=DOC_AI_LOCATION,
            processor_id=DOC_AI_PROCESSOR_ID,
            file_path=file_path,
            mime_type=mime_type
        )

        # 2. Parse the Document AI response
        print("Parsing Document AI response...")
        parsed_data = parse_doc_ai_response(doc_ai_document)

        # 3. Format and Write Output
        print(f"Formatting output for: {output_path}")
        output_format = os.path.splitext(output_path)[1].lower()

        if output_format == ".json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=4, ensure_ascii=False)
        elif output_format == ".csv":
            # Improved basic CSV conversion
            output = io.StringIO()
            # Headers: Entity Type, Text, Normalized Text, Confidence
            headers = ['entity_type', 'text', 'normalized_text', 'confidence']
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()

            for entity_type, entities in parsed_data.items():
                for entity_info in entities:
                    writer.writerow({
                        'entity_type': entity_type,
                        'text': entity_info.get('text', ''),
                        'normalized_text': entity_info.get('normalized_text', ''),
                        'confidence': entity_info.get('confidence', '')
                    })

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                f.write(output.getvalue())
        else:
            # Default to text or raise error for unsupported formats
            print(f"Warning: Unsupported output format '{output_format}'. Writing raw data as text.")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(parsed_data))

        print(f"Successfully processed document. Output saved to: {output_path}")

    except Exception as e:
        print(f"An error occurred during processing: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback for debugging

if __name__ == "__main__":
    main() 