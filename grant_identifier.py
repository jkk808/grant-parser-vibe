import re
import json
import os
from collections import defaultdict
from datetime import datetime

# Grant-related keywords and patterns for context analysis
GRANT_KEYWORDS = [
    "grant", "award", "funding", "program", "project", "initiative", "scheme",
    "RFA", "RFP", "NOFA", "NOFO", "FOA", "BAA", "RFI", "opportunity",
    "federal", "state", "local", "private", "public", "research", "academic",
    "scientific", "educational", "community", "foundation", "institute", "center",
    "society", "association", "council", "commission", "agency", "department",
    "bureau", "office", "division", "unit", "group", "team", "committee", "board",
    "panel", "task force", "working group"
]

# Common grant-giving organizations
GRANT_ORGANIZATIONS = [
    "NIH", "NSF", "DOE", "DOD", "HHS", "USDA", "ED", "HUD", "DOJ", "DOT", "EPA", 
    "NASA", "USGS", "USPTO", "VA", "Treasury", "CDC", "FDA", "FEMA", "FBI", "ICE", 
    "IRS", "NIST", "NOAA", "NRC", "OSHA", "Peace Corps", "SBA", "SSA", "USDA", "USPS"
]

# Financial field patterns
FINANCIAL_PATTERNS = {
    'salary': [
        r'(?i)salary\s*(?:and\s*wages)?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)personnel\s*costs?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)wages\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)'
    ],
    'indirect': [
        r'(?i)indirect\s*costs?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)overhead\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)F&A\s*costs?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)'
    ],
    'travel': [
        r'(?i)travel\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)transportation\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)'
    ],
    'supplies': [
        r'(?i)supplies?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)materials\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)'
    ],
    'fringe': [
        r'(?i)fringe\s*benefits?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)benefits?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)'
    ],
    'equipment': [
        r'(?i)equipment\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)capital\s*expenses?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)'
    ],
    'other': [
        r'(?i)other\s*costs?\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)',
        r'(?i)miscellaneous\s*:?\s*\$?\s*([\d,]+(?:\.\d{2})?)'
    ]
}

# Date patterns
DATE_PATTERNS = [
    r'(?i)(?:start|beginning|project)\s*date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    r'(?i)(?:end|completion|project)\s*date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    r'(?i)period\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    r'(?i)budget\s*period\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
]

# Project/Program patterns
PROJECT_PATTERNS = [
    r'(?i)project\s*title\s*:?\s*([^\n]+)',
    r'(?i)program\s*title\s*:?\s*([^\n]+)',
    r'(?i)project\s*description\s*:?\s*([^\n]+)',
    r'(?i)program\s*description\s*:?\s*([^\n]+)'
]

# Load or create grant name database
GRANT_DB_PATH = "grant_database.json"
grant_database = defaultdict(list)

def load_grant_database():
    """Load the grant database if it exists, otherwise create an empty one."""
    global grant_database
    if os.path.exists(GRANT_DB_PATH):
        try:
            with open(GRANT_DB_PATH, 'r') as f:
                grant_database = defaultdict(list, json.load(f))
        except Exception as e:
            print(f"Error loading grant database: {e}")
            grant_database = defaultdict(list)

def save_grant_database():
    """Save the grant database to disk."""
    try:
        with open(GRANT_DB_PATH, 'w') as f:
            json.dump(dict(grant_database), f)
    except Exception as e:
        print(f"Error saving grant database: {e}")

# Load the database on module import
load_grant_database()

def extract_dates(text):
    """
    Extract start and end dates from text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing start_date, end_date, and yearly_dates
    """
    dates = {
        'start_date': None,
        'end_date': None,
        'yearly_dates': []
    }
    
    # Try to find dates using patterns
    for pattern in DATE_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                if len(match.groups()) == 2:  # Period or budget period pattern
                    start = parse_date(match.group(1))
                    end = parse_date(match.group(2))
                    if start and end:
                        dates['start_date'] = start
                        dates['end_date'] = end
                        # Calculate yearly dates
                        dates['yearly_dates'] = calculate_yearly_dates(start, end)
                        return dates
                else:  # Single date pattern
                    date_str = match.group(1)
                    parsed_date = parse_date(date_str)
                    if parsed_date:
                        if 'start' in pattern.lower() or 'beginning' in pattern.lower():
                            dates['start_date'] = parsed_date
                        elif 'end' in pattern.lower() or 'completion' in pattern.lower():
                            dates['end_date'] = parsed_date
            except Exception:
                continue
    
    return dates

def parse_date(date_str):
    """Parse date string into datetime object."""
    try:
        # Try different date formats
        formats = [
            '%m/%d/%Y', '%m-%d-%Y',
            '%m/%d/%y', '%m-%d-%y',
            '%Y/%m/%d', '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        return None
    except Exception:
        return None

def calculate_yearly_dates(start_date, end_date):
    """Calculate yearly date ranges between start and end dates."""
    yearly_dates = []
    current_date = start_date
    
    while current_date < end_date:
        next_year = datetime(current_date.year + 1, 1, 1)
        if next_year > end_date:
            yearly_dates.append({
                'start': current_date,
                'end': end_date
            })
        else:
            yearly_dates.append({
                'start': current_date,
                'end': datetime(next_year.year - 1, 12, 31)
            })
            current_date = next_year
    
    return yearly_dates

def extract_financial_fields(text):
    """
    Extract financial information from text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing financial fields and their values
    """
    financial_data = {}
    
    for field, patterns in FINANCIAL_PATTERNS.items():
        values = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    value = float(match.group(1).replace(',', ''))
                    values.append({
                        'value': value,
                        'context': text[max(0, match.start() - 50):min(len(text), match.end() + 50)]
                    })
                except (ValueError, IndexError):
                    continue
        
        if values:
            # Sort by value and take the highest
            values.sort(key=lambda x: x['value'], reverse=True)
            financial_data[field] = values[0]
    
    return financial_data

def extract_project_info(text):
    """
    Extract project/program information from text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing project information
    """
    project_info = {
        'title': None,
        'description': None
    }
    
    for pattern in PROJECT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            info = match.group(1).strip()
            if 'title' in pattern.lower():
                project_info['title'] = info
            elif 'description' in pattern.lower():
                project_info['description'] = info
    
    return project_info

def identify_potential_grants(text):
    """
    Identify potential grant names and extract additional information from text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Dictionary containing grant information and extracted fields
    """
    if not text or not isinstance(text, str):
        return {
            'grants': [],
            'dates': {},
            'financial': {},
            'project': {}
        }
    
    # Extract basic grant information
    grants = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        if len(sentence.split()) < 3:
            continue
        
        keyword_count = sum(1 for keyword in GRANT_KEYWORDS if keyword.lower() in sentence.lower())
        org_count = sum(1 for org in GRANT_ORGANIZATIONS if org.lower() in sentence.lower())
        
        if keyword_count > 0 or org_count > 0:
            confidence = min((keyword_count * 0.2) + (org_count * 0.3), 1.0)
            grant_name = extract_grant_name_from_sentence(sentence)
            
            if grant_name:
                grants.append({
                    'name': grant_name,
                    'confidence': confidence,
                    'context': sentence
                })
    
    # Remove duplicates and sort by confidence
    unique_grants = {}
    for grant in grants:
        name = grant['name'].lower()
        if name not in unique_grants or grant['confidence'] > unique_grants[name]['confidence']:
            unique_grants[name] = grant
    
    sorted_grants = sorted(unique_grants.values(), key=lambda x: x['confidence'], reverse=True)
    
    # Extract additional information
    dates = extract_dates(text)
    financial = extract_financial_fields(text)
    project = extract_project_info(text)
    
    return {
        'grants': sorted_grants,
        'dates': dates,
        'financial': financial,
        'project': project
    }

def extract_grant_name_from_sentence(sentence):
    """Extract a potential grant name from a sentence using heuristics."""
    # Look for patterns like "X Grant for Y" or "X Program for Y"
    patterns = [
        r'(?i)([A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?)\s+(?:grant|award|program|project|initiative|scheme)\s+(?:for|to|in|of)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
        r'(?i)(?:grant|award|program|project|initiative|scheme)\s+(?:for|to|in|of)\s+([A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?)',
        r'(?i)([A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?)\s+(?:RFA|RFP|NOFA|NOFO|FOA|BAA|RFI)\s+[A-Z0-9-]+(?:\s*[-:]\s*[A-Z][a-zA-Z\s,&\'-]+)?',
        r'(?i)(?:RFA|RFP|NOFA|NOFO|FOA|BAA|RFI)\s+[A-Z0-9-]+(?:\s*[-:]\s*)([A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sentence)
        if match:
            return match.group(1).strip()
    
    # If no pattern matches, look for capitalized phrases
    words = sentence.split()
    capitalized_phrases = []
    current_phrase = []
    
    for word in words:
        if word and word[0].isupper():
            current_phrase.append(word)
        else:
            if len(current_phrase) > 1:  # Only keep phrases with at least 2 words
                capitalized_phrases.append(' '.join(current_phrase))
            current_phrase = []
    
    if len(current_phrase) > 1:
        capitalized_phrases.append(' '.join(current_phrase))
    
    # Return the longest capitalized phrase
    if capitalized_phrases:
        return max(capitalized_phrases, key=len)
    
    # If all else fails, return the sentence itself
    return sentence.strip()

def add_to_database(grant_name, context):
    """
    Add a grant name and its context to the database for future reference.
    
    Args:
        grant_name (str): The grant name
        context (str): The context in which the grant was found
    """
    if not grant_name or not context:
        return
    
    grant_name = grant_name.strip()
    grant_database[grant_name].append(context)
    
    # Limit the number of contexts per grant to avoid database bloat
    if len(grant_database[grant_name]) > 10:
        grant_database[grant_name] = grant_database[grant_name][-10:]
    
    # Save the updated database
    save_grant_database() 