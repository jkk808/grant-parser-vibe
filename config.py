"""
Configuration settings for the Grant Parser application.
"""

import os
import secrets # Use secrets for cryptographically strong random numbers
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
# Useful for keeping sensitive information like API keys out of the code
load_dotenv()

# --- Google Cloud Document AI Configuration ---

import os
from dotenv import load_dotenv

# Your Google Cloud Project ID
# Set this as an environment variable (e.g., GOOGLE_CLOUD_PROJECT) or replace the string below
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# The location of your Document AI processor (e.g., "us", "eu")
# Set this as an environment variable (e.g., DOC_AI_LOCATION) or replace the string below
DOC_AI_LOCATION = os.getenv("DOC_AI_LOCATION") # e.g., 'us' or 'eu'

# The ID of your trained Custom Document Extractor processor
# Set this as an environment variable (e.g., DOC_AI_PROCESSOR_ID) or replace the string below
DOC_AI_PROCESSOR_ID = os.getenv("DOC_AI_PROCESSOR_ID")

# Optional: Path to your Google Cloud Service Account Key JSON file.
# If not set, the application will rely on Application Default Credentials (ADC).
# Set this as an environment variable (e.g., GOOGLE_APPLICATION_CREDENTIALS)
# SERVICE_ACCOUNT_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)

# --- Flask Configuration ---

# Secret key for Flask sessions (important for security)
# Try to load from .env, generate if missing, and instruct user to add it.
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

if not SECRET_KEY:
    print("Flask SECRET_KEY not found in environment variables or .env file.")
    SECRET_KEY = secrets.token_hex(24) # Generate a 24-byte (48 hex chars) secure key
    print("Generated a new Flask SECRET_KEY.")
    print("Please add the following line to your .env file:")
    print(f"FLASK_SECRET_KEY='{SECRET_KEY}'")
    # Optionally, you could raise an error here to force the user to set it:
    # raise ValueError("FLASK_SECRET_KEY is not set. Please add the generated key to your .env file and restart.")
    # For now, we'll proceed with the generated key for this run, but it won't persist without adding to .env

# Directory to temporarily store uploaded files
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Input/Output Configuration ---
# (Potentially add default output paths or formats if needed for web interface) 