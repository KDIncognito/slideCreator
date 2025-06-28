import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pathlib import Path
from typing import List, Dict, Tuple
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_conversion.log'),
        logging.StreamHandler()
    ]
)

class ReadDoc:
    def __init__(self, output_dir: str = "images"):
        """
        Initialize the PDF converter.
        Args:
            output_dir: Directory to save the output images
        """
        self.output_dir = Path(output_dir)
        logging.info(f"Output directory: {self.output_dir}")
        
        # Create output directory if it doesn't exist
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
            logging.info(f"Created output directory: {self.output_dir}")
        else:
            logging.info(f"Using existing output directory: {self.output_dir}")

    def analyze_page_content(self, page) -> Dict:
        """
        Analyze page content to determine if it contains text or images.
        Args:
            page: fitz Page object
        Returns:
            Dictionary containing content analysis results
        """
        try:
            text = page.get_text("blocks")
            images = page.get_images()
            
            logging.debug(f"Page analysis results - Text blocks: {len(text)}, Images: {len(images)}")
            return {
                'has_text': len(text) > 0,
                'has_images': len(images) > 0,
                'text_blocks': len(text) if len(text) > 0 else 0,
                'image_count': len(images)
            }
        except Exception as e:
            logging.error(f"Error analyzing page content: {str(e)}")
            return {'has_text': False, 'has_images': False, 'text_blocks': 0, 'image_count': 0}

    def group_related_pages(self, doc, max_group_size: int = 3) -> List[List[int]]:
        """
        Group related pages together based on content analysis.
        Args:
            doc: fitz Document object
            max_group_size: Maximum number of pages per group
        Returns:
            List of page number groups
        """
        try:
            groups = []
            current_group = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                content = self.analyze_page_content(page)
                
                # Start new group if current group is full
                if len(current_group) >= max_group_size:
                    if current_group:
                        groups.append(current_group)
                    current_group = []
                
                current_group.append(page_num)
                
                # If we found an image, check if previous page has text
                if content['has_images'] and current_group:
                    # Only check previous page if it exists in current group
                    prev_page_num = current_group[-1]
                    if prev_page_num != page_num:  # Ensure we're not comparing page to itself
                        prev_content = self.analyze_page_content(doc[prev_page_num])
                        if prev_content['has_text']:
                            # Add previous page to current group if it has text
                            if prev_page_num not in current_group:
                                current_group.append(prev_page_num)
                
                # Start new group if we find an image and current group is empty
                if content['has_images'] and not current_group:
                    if current_group:
                        groups.append(current_group)
                    current_group = [page_num]
            
            # Add any remaining pages to a final group
            if current_group:
                groups.append(current_group)
            
            logging.debug(f"Created {len(groups)} page groups")
            logging.debug(f"Group sizes: {[len(group) for group in groups]}")
            return groups
        except Exception as e:
            logging.error(f"Error grouping pages: {str(e)}")
            return []

    def combine_pages(self, doc, page_numbers: List[int], dpi: int = 300) -> Tuple[fitz.Pixmap, Dict]:
        """
        Combine multiple pages into a single image using PIL.
        Args:
            doc: fitz Document object
            page_numbers: List of page numbers to combine
            dpi: Resolution in dots per inch
        Returns:
            Tuple of (combined pixmap, metadata)
        """
        try:
            logging.debug(f"Starting to combine {len(page_numbers)} pages: {page_numbers}")
            
            # Calculate total height needed
            total_height = 0
            page_width = 0
            for pnum in page_numbers:
                page = doc[pnum]
                # Get page as PIL image
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
                img = Image.frombytes("RGB", [pix.w, pix.h], pix.samples)
                
                total_height += img.height
                page_width = max(page_width, img.width)
                logging.debug(f"Page {pnum + 1}: width={img.width}, height={img.height}")
            
            # Create combined image
            combined_img = Image.new('RGB', (page_width, total_height), 'white')
            logging.debug(f"Created combined image: width={page_width}, height={total_height}")
            
            # Combine pages
            y_pos = 0
            for idx, pnum in enumerate(page_numbers):
                page = doc[pnum]
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
                img = Image.frombytes("RGB", [pix.w, pix.h], pix.samples)
                
                # Paste page onto combined image
                try:
                    combined_img.paste(img, (0, y_pos))
                    logging.debug(f"Pasted page {pnum + 1} to position y={y_pos}")
                except Exception as e:
                    logging.error(f"Failed to paste page {pnum + 1}: {str(e)}")
                    raise
                
                # Add reference marker
                marker_text = f"Page {pnum + 1}"
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(combined_img)
                try:
                    font = ImageFont.load_default()
                    draw.text((10, y_pos + 10), marker_text, fill='gray')
                    logging.debug(f"Added marker for page {pnum + 1}")
                except Exception as e:
                    logging.warning(f"Failed to add marker for page {pnum + 1}: {str(e)}")
                
                y_pos += img.height
            
            # Convert PIL image back to PyMuPDF pixmap
            buffer = io.BytesIO()
            combined_img.save(buffer, format='PNG')
            buffer.seek(0)
            combined_pix = fitz.Pixmap(buffer.read())
            
            metadata = {
                'page_numbers': [num + 1 for num in page_numbers],
                'combined_height': total_height,
                'width': page_width,
                'dpi': dpi,
                'group_size': len(page_numbers)
            }
            
            logging.debug(f"Successfully combined pages. Metadata: {metadata}")
            return combined_pix, metadata
        except Exception as e:
            logging.error(f"Error combining pages: {str(e)}")
            raise


    def convert_pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[Dict]:
        """
        Convert PDF to high-quality images, grouping related pages together.
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution in dots per inch (default: 300)
        Returns:
            List of dictionaries containing image metadata
        """
        try:
            logging.info(f"Starting conversion of PDF: {pdf_path}")
            doc = fitz.open(pdf_path)
            image_metadata = []
            
            # Group related pages
            page_groups = self.group_related_pages(doc)
            
            # Process each group
            for group_idx, page_numbers in enumerate(page_groups):
                logging.info(f"Processing group {group_idx + 1} with pages {page_numbers}")
                
                # Combine pages in group
                combined_pix, metadata = self.combine_pages(doc, page_numbers, dpi)
                
                if combined_pix is None:
                    logging.error(f"Failed to combine pages for group {group_idx + 1}")
                    continue
                
                # Create unique filename
                image_path = self.output_dir / f"group_{group_idx + 1}.png"
                logging.info(f"Saving image to: {image_path}")
                
                # Save combined image
                try:
                    combined_pix.save(str(image_path))
                    logging.info(f"Successfully saved image: {image_path}")
                except Exception as e:
                    logging.error(f"Failed to save image {image_path}: {str(e)}")
                    continue
                
                # Store metadata
                image_metadata.append({
                    'group_number': group_idx + 1,
                    'page_numbers': metadata['page_numbers'],
                    'path': str(image_path),
                    'resolution': dpi,
                    'dimensions': {
                        'width': metadata['width'],
                        'height': metadata['combined_height']
                    },
                    'group_size': metadata['group_size']
                })
            
            doc.close()
            logging.info(f"Conversion completed. Generated {len(image_metadata)} images")
            return image_metadata
        except Exception as e:
            logging.error(f"Error during PDF conversion: {str(e)}")
            return []