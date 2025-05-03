"""
doc_ai_client.py

Handles interaction with Google Document AI to process uploaded documents.
"""

import os
# Use the v1 version of the Document AI library
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions

def process_document_local(project_id, location, processor_id, file_path, mime_type):
    """
    Processes a document locally and returns the Document AI response object.

    Args:
        project_id (str): GCP project ID.
        location (str): Location (e.g., "us").
        processor_id (str): ID of the Document AI processor.
        file_path (str): Local path to the file.
        mime_type (str): MIME type of the file.

    Returns:
        documentai.Document: Parsed document (using v1 structure).
    """
    # Initialize client with optional endpoint override for non-global locations
    # The endpoint format is the same for v1 and v1beta3
    client_options = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    # Use the v1 client
    client = documentai.DocumentProcessorServiceClient(client_options=client_options)

    # Construct processor resource name (same format for v1)
    name = client.processor_path(project=project_id, location=location, processor=processor_id)
    print(f"[INFO] Using processor: {name}")

    # Read the file
    file_content = None
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()
        if not file_content:
            print(f"[ERROR] Read 0 bytes from file: {file_path}. Check if the file is empty or corrupted.")
            return None # Return None to indicate failure
        print(f"[INFO] Read {len(file_content)} bytes from file: {file_path} (MIME type: {mime_type})")
    except FileNotFoundError:
        print(f"[ERROR] Input file not found at: {file_path}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read file {file_path}: {e}")
        return None

    # Prepare the raw document payload (structure is compatible)
    raw_document = documentai.RawDocument(
        content=file_content,
        mime_type=mime_type
    )

    # Build the request (structure is compatible)
    # NOTE: If using specific v1beta3 features like ProcessOptions, they would need adjustment.
    # For basic processing, this should work.
    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document
        # skip_human_review=True # Optional: v1 field, set if needed
    )

    print("[INFO] Sending document to Google Document AI (using v1 client)...")

    # Send the request
    result = None
    try:
        result = client.process_document(request=request)
    except Exception as e:
        print(f"[ERROR] Exception during Document AI API call: {e}")
        import traceback
        traceback.print_exc()
        return None # Return None on API call failure

    # --- Added Debugging: Inspect the raw result --- 
    if not result:
        print("[ERROR] Document AI API call returned None or failed.")
        return None
        
    print("--- Raw Document AI Result (Debug) ---")
    print(f"Result type: {type(result)}")
    # Convert the protobuf result to a dict for easier inspection (optional, requires protobuf library)
    try:
        from google.protobuf.json_format import MessageToDict
        # Be cautious with large results, maybe limit depth or size if needed
        result_dict = MessageToDict(result._pb)
        # Print a limited representation, avoid overwhelming logs
        import json
        print(json.dumps(result_dict, indent=2, default=str)[:2000] + ("... (truncated)" if len(json.dumps(result_dict, indent=2, default=str)) > 2000 else ""))
    except ImportError:
        print("(Install protobuf library for detailed dict view) Raw result object:")
        print(str(result)[:2000] + ("... (truncated)" if len(str(result)) > 2000 else ""))
    except Exception as e:
        print(f"Error converting result to dict for logging: {e}")
        print(f"Raw result object: \n{str(result)[:2000]}...")
    print("-----------------------------------------")

    document = result.document

    # --- Added Debugging: Check if document object itself seems valid --- 
    if not document:
        print("[ERROR] Document object in the API response is None.")
        return None
    if not document.text and not document.entities:
        print("[WARNING] Document object in the API response has no text and no entities. The processor might have failed or returned an empty result.")
        # Don't return None here, let the parser handle the empty document if needed

    # Log basic response info (document structure is largely compatible for text/entities)
    text_length = len(document.text or '')
    print(f"[DEBUG] Received document text length: {text_length} characters")
    print(f"[DEBUG] First 300 characters of extracted text:\n{document.text[:300]}")

    return document
