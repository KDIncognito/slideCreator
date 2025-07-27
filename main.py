#!/usr/bin/env python3
"""
SlideCreator - Convert PDF documents to PowerPoint presentations

Usage: python3 main.py <path_to_pdf_file>

This CLI interface provides a simple command-line interface for the SlideCreator system.
The core conversion logic is handled by the SlideCreator class in core/slide_creator.py
"""

import sys
import os
import argparse
from pathlib import Path

from core.slide_creator import SlideCreator
from utils.logger import get_logger, SlideCreatorLogger


def setup_logging(args):
    """Setup logging based on command line arguments."""
    logger_instance = SlideCreatorLogger()
    
    if args.verbose:
        logger_instance.set_level('DEBUG')
    
    if args.log_file:
        logger_instance.add_file_handler(args.log_file)
    
    return logger_instance.get_logger()


def validate_environment():
    """Validate environment and dependencies."""
    creator = SlideCreator()
    validation = creator.validate_environment()
    
    if not validation.success:
        logger = get_logger()
        logger.error("(XXX) Environment validation failed:")
        for error in validation.errors:
            logger.error(f"   - {error}")
        
        if validation.errors:
            logger.info("   Example: export gpt_key=your_openai_api_key")
        
        return False
    
    return True


def show_file_info(pdf_path: str):
    """Show information about the PDF file to be converted."""
    try:
        creator = SlideCreator()
        info = creator.get_conversion_info(pdf_path)
        logger = get_logger()
        
        logger.info("(###) File Information:")
        logger.info(f"   (&&&) Name: {info['file_name']}")
        logger.info(f"   (%) Size: {info['file_size_mb']:.2f} MB")
        logger.info(f"   (&&&) Output will be: {info['expected_output']}")
        
    except Exception as e:
        logger = get_logger()
        logger.warning(f"(!!!) Could not get file info: {str(e)}")


def main():
    """Main entry point for the command line interface."""
    
    parser = argparse.ArgumentParser(
        description='Convert PDF documents to PowerPoint presentations using AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py document.pdf
  python3 main.py /path/to/thesis.pdf
  python3 main.py document.pdf --output presentation.pptx
  python3 main.py document.pdf --verbose --log-file conversion.log

Environment Variables:
  gpt_key    OpenAI API key (required)

For more information, see KNOWLEDGE_README.md
        """
    )
    
    parser.add_argument(
        'pdf_file',
        help='Path to the PDF file to convert'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output path for the PowerPoint file (default: same name as PDF with .pptx extension)',
        default=None
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output (DEBUG level logging)'
    )
    
    parser.add_argument(
        '--log-file',
        help='Path to log file for detailed logging',
        default=None
    )
    
    parser.add_argument(
        '--info-only',
        action='store_true',
        help='Show file information only, do not convert'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging based on arguments
    logger = setup_logging(args)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Show file info if requested
    if args.info_only:
        show_file_info(args.pdf_file)
        return
    
    # Show file info before conversion
    show_file_info(args.pdf_file)
    
    try:
        # Create SlideCreator instance and run conversion
        logger.info("(>>>) Initializing SlideCreator...")
        creator = SlideCreator()
        
        logger.info("(>>>) Starting conversion process...")
        output_file = creator.convert_pdf_to_slides(args.pdf_file, args.output)
        
        # Show success information
        logger.info("(!!!) Success! Your presentation is ready:")
        logger.info(f"   (&&&) File: {output_file}")
        
        if os.path.exists(output_file):
            file_size_kb = os.path.getsize(output_file) / 1024
            logger.info(f"   (%) Size: {file_size_kb:.1f} KB")
        
        logger.info("(!!!) Conversion completed successfully!")
        
    except KeyboardInterrupt:
        logger.warning("(---) Conversion cancelled by user")
        sys.exit(1)
        
    except FileNotFoundError as e:
        logger.error(f"(XXX) File not found: {str(e)}")
        sys.exit(1)
        
    except ValueError as e:
        logger.error(f"(XXX) Invalid input: {str(e)}")
        sys.exit(1)
        
    except RuntimeError as e:
        logger.error(f"(XXX) Conversion failed: {str(e)}")
        if args.verbose:
            import traceback
            logger.debug(traceback.format_exc())
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"(XXX) Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
