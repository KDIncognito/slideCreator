import sys

from documentHandling import ReadDoc, pptHandling
from gpt import gptHandler, gptContext

def creation_of_slides():
    context = gptContext()
    gp = gptHandler()
    ## Check for malicious content
    
    is_malicious = gp.llm_handler(
        system=context.malicious.system,
        user=context.malicious.user,
        material = "images/group_1.png"
    )
    print(is_malicious)
    # Breakdown the given document into individual concepts

    # Convert the concepts into a slide format

    # Put it all together.

    # Save the file as a pptx file.

    # Upload a copy to AWS

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

    creation_of_slides()
    exit(1)

    # Initialize the ReadDoc instance
    rd = ReadDoc(1)
    try:
        rd.convert_pdf_to_images(pdf_path, dpi=300)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        sys.exit(1)

if __name__ == "__main__":
    execute_all()