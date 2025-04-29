import re
import nltk
from nltk.tokenize import sent_tokenize
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

def identify_potential_grants(text):
    """
    Identify potential grant names in a text block.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        list: List of potential grant names with confidence scores
    """
    if not text or not isinstance(text, str):
        return []
    
    # Common grant name patterns
    grant_patterns = [
        r'(?i)grant\s+(?:for|to|in|of|program|award|opportunity|funding|project|initiative|scheme)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
        r'(?i)(?:federal|state|local|private|public|research|academic|scientific|educational|community)\s+grant\s+(?:for|to|in|of|program|award|opportunity|funding|project|initiative|scheme)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
        r'(?i)(?:funding|award|support)\s+(?:for|to|in|of|program|project|initiative|scheme)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
        r'(?i)(?:program|project|initiative|scheme)\s+(?:for|to|in|of|funding|support|award)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
        r'(?i)(?:RFA|RFP|NOFA|NOFO|FOA|FOA|BAA|RFI)\s+[A-Z0-9-]+(?:\s*[-:]\s*[A-Z][a-zA-Z\s,&\'-]+)?',
        r'(?i)(?:NIH|NSF|DOE|DOD|HHS|USDA|ED|HUD|DOJ|DOT|EPA|NASA|NSF|USGS|USPTO|VA|Treasury)\s+(?:Grant|Award|Program|Initiative|Project|Scheme)\s+(?:for|to|in|of)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
        r'(?i)(?:Foundation|Institute|Center|Society|Association|Council|Commission|Agency|Department|Bureau|Office|Division|Unit|Group|Team|Committee|Board|Panel|Task Force|Working Group)\s+(?:Grant|Award|Program|Initiative|Project|Scheme)\s+(?:for|to|in|of)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
        r'(?i)(?:Research|Development|Innovation|Education|Training|Outreach|Extension|Implementation|Evaluation|Assessment|Analysis|Study|Investigation|Exploration|Discovery|Creation|Production|Distribution|Dissemination|Application|Utilization|Adoption|Integration|Incorporation|Inclusion|Participation|Engagement|Involvement|Collaboration|Cooperation|Coordination|Partnership|Alliance|Consortium|Network|Community|Society|Population|Group|Cohort|Sample|Set|Collection|Database|Repository|Archive|Library|Museum|Gallery|Exhibition|Display|Show|Presentation|Demonstration|Performance|Event|Activity|Initiative|Program|Project|Scheme|Plan|Strategy|Approach|Method|Technique|Procedure|Process|System|Framework|Model|Paradigm|Theory|Hypothesis|Question|Problem|Issue|Challenge|Opportunity|Need|Gap|Barrier|Constraint|Limitation|Boundary|Scope|Scale|Size|Extent|Degree|Level|Depth|Breadth|Width|Height|Length|Distance|Duration|Period|Time|Date|Year|Month|Day|Hour|Minute|Second|Millisecond|Microsecond|Nanosecond|Picosecond|Femtosecond|Attosecond|Zeptosecond|Yoctosecond|Planck time)\s+(?:Grant|Award|Program|Initiative|Project|Scheme)\s+(?:for|to|in|of)\s+[A-Z][a-zA-Z\s,&\'-]+(?:\([^)]+\))?',
    ]
    
    # Compile patterns
    compiled_patterns = [re.compile(pattern) for pattern in grant_patterns]
    
    # Find matches
    potential_grants = []
    
    # Split text into sentences for better context
    sentences = sent_tokenize(text)
    
    for sentence in sentences:
        for pattern in compiled_patterns:
            matches = pattern.finditer(sentence)
            for match in matches:
                grant_name = match.group(0).strip()
                
                # Calculate confidence score based on various factors
                confidence = calculate_confidence_score(grant_name, sentence)
                
                # Only include if confidence is above threshold
                if confidence > 0.3:
                    potential_grants.append({
                        'name': grant_name,
                        'confidence': confidence,
                        'context': sentence.strip()
                    })
    
    # Remove duplicates while keeping the highest confidence score
    unique_grants = {}
    for grant in potential_grants:
        name = grant['name'].lower()
        if name not in unique_grants or grant['confidence'] > unique_grants[name]['confidence']:
            unique_grants[name] = grant
    
    # Sort by confidence score (highest first)
    sorted_grants = sorted(unique_grants.values(), key=lambda x: x['confidence'], reverse=True)
    
    return sorted_grants

def calculate_confidence_score(grant_name, context):
    """
    Calculate a confidence score for a potential grant name.
    
    Args:
        grant_name (str): The potential grant name
        context (str): The sentence containing the grant name
        
    Returns:
        float: Confidence score between 0 and 1
    """
    score = 0.0
    
    # Length factor (longer names are more likely to be grants)
    length_factor = min(len(grant_name.split()) / 10, 1.0)
    score += length_factor * 0.2
    
    # Keyword presence
    keywords = ['grant', 'award', 'funding', 'program', 'project', 'initiative', 'scheme', 
                'RFA', 'RFP', 'NOFA', 'NOFO', 'FOA', 'BAA', 'RFI']
    keyword_count = sum(1 for keyword in keywords if keyword.lower() in grant_name.lower())
    score += (keyword_count / len(keywords)) * 0.3
    
    # Proper noun detection (grants often contain proper nouns)
    words = word_tokenize(grant_name)
    tagged = pos_tag(words)
    proper_noun_count = sum(1 for word, tag in tagged if tag.startswith('NNP'))
    proper_noun_factor = min(proper_noun_count / max(len(words), 1), 1.0)
    score += proper_noun_factor * 0.2
    
    # Capitalization (grants often have capitalized words)
    capitalized_words = sum(1 for word in words if word and word[0].isupper())
    capitalization_factor = capitalized_words / max(len(words), 1)
    score += capitalization_factor * 0.15
    
    # Context analysis
    context_keywords = ['apply', 'application', 'submit', 'submission', 'deadline', 'due date', 
                       'eligibility', 'requirements', 'criteria', 'budget', 'funding', 'amount',
                       'period', 'duration', 'term', 'conditions', 'restrictions', 'limitations']
    context_keyword_count = sum(1 for keyword in context_keywords if keyword.lower() in context.lower())
    context_factor = min(context_keyword_count / 5, 1.0)
    score += context_factor * 0.15
    
    return min(score, 1.0) 