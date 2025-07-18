import sys
from logging_config import get_logger, get_calling_module_name

from documentHandling import ReadDoc
from gptHandling import handler


name = get_calling_module_name()
log = get_logger(name)
log.info("done; ")

def execute_all():
    # Check if pdf path is provided
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <pdf_path>")
        sys.exit(1)

    # Get the pdf path from command line
    pdf_path = sys.argv[1]
    
    # Check if the provided path ends with .pdf
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError("The provided file must be a PDF.")

    # Initialize the ReadDoc instance
    rd = ReadDoc()
    try:
        conv = rd.extract_all_text_simple(pdf_path)
        all_slide_content = handler(conv).get_slide_content()
        # Prepare slides from dictionary

        # Add images for the slides

        # Save the slides to a file
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        sys.exit(1)
    

if __name__ == "__main__":
    execute_all()