import sys
from logging_config import get_logger, get_calling_module_name

from documentHandling import ReadDoc
from documentHandling.writePpt import create_powerpoint_from_content  # FIX: Import the function directly
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
        print("📄 Extracting text from PDF...")
        conv = rd.extract_all_text_simple(pdf_path)
        
        # FIX: Convert list of page dictionaries to single text string
        if isinstance(conv, list):
            # Extract text from all pages and combine
            all_text = "\n\n".join([page.get('text_content', '') for page in conv])
        else:
            all_text = str(conv)
        
        print("🤖 Generating slide content...")
        all_slide_content = handler(all_text).get_slide_content()  # FIX: Pass string, not list
        
        print("📊 Creating PowerPoint presentation...")
        # Generate output filename based on input PDF
        pdf_name = pdf_path.split('/')[-1].replace('.pdf', '')
        output_filename = f"{pdf_name}_slides.pptx"
        
        # Create PowerPoint from the slide content
        success = create_powerpoint_from_content(all_slide_content, output_filename)
        
        if success:
            print(f">> Success! PowerPoint presentation created: {output_filename}")
        else:
            print("XX Failed to create PowerPoint presentation")
            
    except Exception as e:
        print(f"XX Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    execute_all()