import PyPDF2
import sys
import os

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        # Check if file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} does not exist.")
            
        # Check if file is a PDF
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("The file must be a PDF.")
            
        # Open the PDF file
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            text = ""
            for page_num in range(num_pages):
                # Get the page
                page = pdf_reader.pages[page_num]
                # Extract text from the page
                text += page.extract_text() + "\n\n"
                
            return text.strip()
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def main():
    # Check if PDF path is provided as command line argument
    if len(sys.argv) != 2:
        print("Usage: python pdf_extractor.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    
    # Extract text from PDF
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if extracted_text:
        print("\nExtracted Text:")
        print("-" * 50)
        print(extracted_text)
        print("-" * 50)
        
        # Save the extracted text to a file
        output_file = os.path.splitext(pdf_path)[0] + "_extracted.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        print(f"\nExtracted text has been saved to: {output_file}")

if __name__ == "__main__":
    main() 