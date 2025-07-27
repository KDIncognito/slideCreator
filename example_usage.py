#!/usr/bin/env python3
"""
Example usage of the SlideCreator class for programmatic access.

This demonstrates how to use SlideCreator in your own Python scripts
without the command-line interface.
"""

import os
from pathlib import Path
from core.slide_creator import SlideCreator
from utils.logger import get_logger, SlideCreatorLogger


def example_basic_conversion():
    """Basic example of converting a PDF to PowerPoint."""
    
    # Setup logging
    logger = get_logger()
    
    # Example PDF path (replace with your actual PDF)
    pdf_path = "example_document.pdf"
    
    if not Path(pdf_path).exists():
        logger.warning(f"Example PDF not found: {pdf_path}")
        logger.info("Please provide a valid PDF path to test the conversion.")
        return
    
    try:
        # Create SlideCreator instance
        creator = SlideCreator()
        
        # Validate environment
        validation = creator.validate_environment()
        if not validation['is_valid']:
            logger.error("Environment validation failed:")
            for error in validation['errors']:
                logger.error(f"  - {error}")
            return
        
        # Get file information
        info = creator.get_conversion_info(pdf_path)
        logger.info(f"Converting: {info['file_name']} ({info['file_size_mb']:.2f} MB)")
        
        # Convert PDF to PowerPoint
        output_path = creator.convert_pdf_to_slides(
            pdf_path=pdf_path,
            output_path="output_presentation.pptx"
        )
        
        logger.info(f"Conversion successful! Output: {output_path}")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")


def example_batch_conversion():
    """Example of converting multiple PDFs in a batch."""
    
    logger = get_logger()
    
    # Example: convert all PDFs in a directory
    pdf_directory = Path("input_pdfs")  # Replace with your directory
    output_directory = Path("output_presentations")
    
    if not pdf_directory.exists():
        logger.warning(f"Input directory not found: {pdf_directory}")
        logger.info("Create the directory and add PDF files to test batch conversion.")
        return
    
    # Create output directory
    output_directory.mkdir(exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(pdf_directory.glob("*.pdf"))
    
    if not pdf_files:
        logger.info(f"No PDF files found in {pdf_directory}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to convert")
    
    # Create SlideCreator instance
    creator = SlideCreator()
    
    # Convert each PDF
    successful_conversions = 0
    failed_conversions = 0
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"Converting: {pdf_file.name}")
            
            output_path = output_directory / f"{pdf_file.stem}.pptx"
            
            creator.convert_pdf_to_slides(
                pdf_path=str(pdf_file),
                output_path=str(output_path)
            )
            
            successful_conversions += 1
            logger.info(f"Successfully converted: {pdf_file.name}")
            
        except Exception as e:
            failed_conversions += 1
            logger.error(f"Failed to convert {pdf_file.name}: {str(e)}")
    
    logger.info(f"Batch conversion complete: {successful_conversions} successful, {failed_conversions} failed")


def example_with_custom_logging():
    """Example showing custom logging configuration."""
    
    # Setup custom logging
    logger_instance = SlideCreatorLogger()
    logger_instance.set_level('DEBUG')  # Verbose logging
    logger_instance.add_file_handler('conversion_log.txt')  # Log to file
    
    logger = logger_instance.get_logger()
    
    logger.info("Starting conversion with custom logging")
    
    # Your conversion code here
    pdf_path = "example_document.pdf"
    
    if Path(pdf_path).exists():
        try:
            creator = SlideCreator()
            output_path = creator.convert_pdf_to_slides(pdf_path)
            logger.info(f"Conversion completed: {output_path}")
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
    else:
        logger.warning(f"PDF file not found: {pdf_path}")


if __name__ == "__main__":
    # Make sure to set your OpenAI API key
    if not os.getenv('gpt_key'):
        print("Please set the 'gpt_key' environment variable with your OpenAI API key")
        print("Example: export gpt_key=your_openai_api_key")
        exit(1)
    
    print("SlideCreator Usage Examples")
    print("=" * 50)
    
    print("\n1. Basic Conversion Example:")
    example_basic_conversion()
    
    print("\n2. Batch Conversion Example:")
    example_batch_conversion()
    
    print("\n3. Custom Logging Example:")
    example_with_custom_logging()
    
    print("\nExamples completed!")
