import pdfplumber
import json
import re
import datetime
from dateutil.parser import parse
from email_validator import validate_email, EmailNotValidError
import pandas as pd

class GrantDocumentParser:
    def __init__(self):
        pass  # TextBlob does not require model loading

    def parse_pdf(self, file_path):
        """Parse PDF grant document and extract key information"""
        # Initialize extracted information dictionary
        extracted_info = {
            'file_path': file_path,
            'grant_provider': None,
            'grant_amount': None,
            'deadlines': [],
            'start_date': None,
            'end_date': None,
            'contact_info': {},
            'grant_status': None,
            'additional_details': {}
        }

        # Extract PDF text
        with pdfplumber.open(file_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() or ''

        # Comprehensive regex patterns for information extraction
        PROVIDER_PATTERNS = [
            r'RECIPIENT:\s*([\w\s]+(?:Brd|Board|Agency|Corporation))',
            r'PAYEE:\s*([\w\s]+(?:Brd|Board|Agency|Corporation))'
        ]

        AMOUNT_PATTERNS = [
            r'This grant provides full federal funding in the amount of \$([0-9,]+(?:\.[0-9]{2})?)',
            r'EPA Amount This Action \$\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'TOTAL BUDGET PERIOD COST \$([0-9,]+(?:\.[0-9]{2})?)',
            r'Allowable Project Cost \$\s*([0-9,]+(?:\.[0-9]{2}?))'
        ]

        DATE_PATTERNS = {
            'grant_date': [
                r'DATE OF AWARD\s*(\d{2}/\d{2}/\d{4})',
                r'MAILING DATE\s*(\d{2}/\d{2}/\d{4})'
            ]
        }

        DEADLINE_PATTERNS = [
            r'deadline:\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'submission\s*deadline:\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'application\s*due\s*date:\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'due\s*date:\s*(\d{1,2}/\d{1,2}/\d{2,4})'
        ]

        CONTACT_PATTERNS = {
            'email': r'E-Mail:\s*([\w\.-]+@[\w\.-]+)',
            'phone': r'Phone:\s*(\d{3}-\d{3}-\d{4})',
            'name': [
                r'PROJECT\s*MANAGER\s*([\w\s]+)\s*EPA',
                r'([\w\s]+)\s*EPA PROJECT OFFICER'
            ]
        }

        # Date Parsing
        date_pattern = r'BUDGET\s*PERIOD.*?(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
        budget_periods = re.findall(date_pattern, full_text, re.DOTALL)
        if budget_periods:
            start_date_str, end_date_str = budget_periods[0]
            start_date = parse(start_date_str)
            end_date = parse(end_date_str)
            extracted_info['start_date'] = start_date.strftime("%Y-%m-%d")
            extracted_info['end_date'] = end_date.strftime("%Y-%m-%d")

        # Extract Grant Provider
        for pattern in PROVIDER_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted_info["grant_provider"] = match.group(1).strip()
                break

        # Extract Grant Amount
        for pattern in AMOUNT_PATTERNS:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace('$', '').replace(',', '')
                    extracted_info['grant_amount'] = float(amount_str)
                    break
                except (ValueError, TypeError):
                    pass

        # Extract Deadlines
        for pattern in DEADLINE_PATTERNS:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                extracted_info['deadlines'] = [match.strip() for match in matches]
                break

        # Contact Information
        contact_info = {
            'email': 'N/A',
            'phone': 'N/A',
            'name': 'N/A'
        }

        # Email extraction
        email_matches = re.findall(r'E-Mail:\s*([\w\.-]+@[\w\.-]+)', full_text, re.IGNORECASE)
        contact_info['email'] = email_matches[0] if email_matches else 'N/A'

        # Phone extraction
        phone_matches = re.findall(r'Phone:\s*(\d{3}-\d{3}-\d{4})', full_text)
        contact_info['phone'] = phone_matches[0] if phone_matches else 'N/A'
        
        # Name extraction
        name_patterns = [
            r'PROJECT\s*MANAGER\s*([\w\s]+)\s*EPA',
            r'([\w\s]+)\s*EPA PROJECT OFFICER'
        ]
        name_matches = []
        for pattern in name_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else None
                if match and isinstance(match, str):
                    name_matches.append(match.strip())
        
        contact_info['name'] = name_matches[0] if name_matches else 'N/A'
        
        extracted_info["contact_info"] = contact_info

        return extracted_info

    def parse_json(self, file_path):
        """
        Parse JSON grant document
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Implement JSON parsing logic here
        # This is a placeholder and should be customized based on specific JSON structures
        return data

    def process_documents(self, document_paths):
        """
        Process multiple documents and return a DataFrame
        """
        results = []
        for path in document_paths:
            if path.lower().endswith('.pdf'):
                result = self.parse_pdf(path)
            elif path.lower().endswith('.json'):
                result = self.parse_json(path)
            else:
                print(f"Unsupported file type: {path}")
                continue
            results.append(result)

        return pd.DataFrame(results)

def main():
    parser = GrantDocumentParser()
    # Replace with your actual PDF path
    sample_pdf_path = '/Users/hysonk/CascadeProjects/grant_parser/test_grant.pdf'
    try:
        result = parser.parse_pdf(sample_pdf_path)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"Error parsing PDF: {e}")

if __name__ == "__main__":
    main()
