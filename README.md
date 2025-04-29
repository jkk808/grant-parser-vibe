# Grant Document Parser

## Overview
A Python-based tool to extract key information from grant documents (PDF, JSON).

## Features
- Parse PDF and JSON grant documents
- Extract key information:
  - Grant Provider
  - Grant Amount
  - Deadlines
  - Start and End Dates
  - Contact Information
  - Grant Status

## Setup
1. Clone the repository
2. Create a virtual environment
3. Install dependencies:
   ```
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Usage
```python
from src.grant_parser import GrantDocumentParser

parser = GrantDocumentParser()
document_paths = ['path/to/grant_document.pdf']
results = parser.process_documents(document_paths)
print(results)
```

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License.
