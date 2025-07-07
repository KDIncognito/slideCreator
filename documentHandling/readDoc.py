import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pathlib import Path
from typing import List, Dict, Tuple, Union
import string

from logging_config import get_logger, get_calling_module_name
name = get_calling_module_name()
log = get_logger(name)
log.info("done; ")


class ReadDoc:
    def __init__(self):
        """
        Initialize the PDF content extractor.
        No output directory needed as images are not saved, only their metadata.
        """
        logging.info("Initialized PDF content extractor (no image output).")

    def analyze_page_content(self, page) -> Dict:
        """
        Analyze page content to determine if it contains text, raster images, or vector drawings.
        Args:
            page: fitz Page object
        Returns:
            Dictionary containing content analysis results
        """
        try:
            text = page.get_text("blocks")
            raster_images = page.get_images()
            vector_drawings = page.get_drawings()
            
            logging.debug(f"Page analysis results - Text blocks: {len(text)}, Raster Images: {len(raster_images)}, Vector Drawings: {len(vector_drawings)}")
            return {
                'has_text': len(text) > 0,
                'has_raster_images': len(raster_images) > 0,
                'has_vector_drawings': len(vector_drawings) > 0,
                'text_blocks_count': len(text),
                'raster_image_count': len(raster_images),
                'vector_drawing_count': len(vector_drawings)
            }
        except Exception as e:
            logging.error(f"Error analyzing page content for page {page.number}: {str(e)}")
            return {
                'has_text': False, 
                'has_raster_images': False, 
                'has_vector_drawings': False,
                'text_blocks_count': 0, 
                'raster_image_count': 0, 
                'vector_drawing_count': 0
            }

    def extract_text_from_page(self, page) -> List[Dict]:
        """
        Extracts all text blocks from a given page.
        Args:
            page: fitz Page object
        Returns:
            List of dictionaries, each containing text and its bounding box.
        """
        extracted_text = []
        try:
            text_blocks = page.get_text("blocks")
            for block in text_blocks:
                x0, y0, x1, y1, text_content, block_no, block_type = block
                extracted_text.append({
                    'text': text_content.strip(),
                    'bbox': (x0, y0, x1, y1),
                    'block_type': 'text' if block_type == 0 else 'image' # 0 for text, 1 for image
                })
            logging.debug(f"Extracted {len(extracted_text)} text blocks from page {page.number + 1}")
        except Exception as e:
            logging.error(f"Error extracting text from page {page.number + 1}: {str(e)}")
        return extracted_text

    def extract_raster_images_metadata_from_page(self, doc, page) -> List[Dict]:
        """
        Extracts metadata for raster images from a given page and attempts to associate them with nearby text as titles.
        No image files are saved.
        Args:
            doc: fitz Document object (needed for extract_image)
            page: fitz Page object
        Returns:
            List of dictionaries, each containing raster image metadata (no file path).
        """
        extracted_images = []
        try:
            image_list = page.get_images(full=True)
            text_blocks = page.get_text("blocks") # Get text blocks to find potential titles

            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                bbox = img_info[7] # Bounding box of the image (x0, y0, x1, y1)

                image_ext = None
                try:
                    base_image = doc.extract_image(xref)
                    image_ext = base_image["ext"]
                except Exception as e:
                    logging.warning(f"Could not extract raster image xref {xref} from page {page.number + 1} for metadata: {str(e)}")
                    continue

                if not image_ext:
                    logging.warning(f"No image extension found for xref {xref} on page {page.number + 1}, skipping.")
                    continue

                image_title = None
                image_rect = fitz.Rect(bbox) 
                sorted_text_blocks = sorted(text_blocks, key=lambda x: x[1])

                for text_block in sorted_text_blocks:
                    text_bbox = fitz.Rect(text_block[0], text_block[1], text_block[2], text_block[3])
                    text_content = text_block[4].strip()

                    if (text_bbox.y1 < image_rect.y0 and 
                        abs(image_rect.y0 - text_bbox.y1) < 50 and 
                        text_bbox.intersects(image_rect)):
                        
                        lower_text = text_content.lower()
                        if lower_text.startswith(("fig.", "figure", "table", "chart", "graph")):
                            image_title = text_content
                            break

                extracted_images.append({
                    'type': 'raster_image',
                    'bbox': list(bbox),
                    'page_number': page.number + 1,
                    'title': image_title if image_title else f"Raster Image on Page {page.number + 1}, Image {img_index + 1}",
                    'extension': image_ext
                })
            logging.debug(f"Extracted {len(extracted_images)} raster images metadata from page {page.number + 1}")
        except Exception as e:
            logging.error(f"Error extracting raster images metadata from page {page.number + 1}: {str(e)}")
        return extracted_images

    def extract_vector_drawings_metadata_from_page(self, page) -> List[Dict]:
        """
        Extracts metadata for vector graphics (drawings) from a given page.
        These often represent charts, graphs, or complex diagrams.
        Args:
            page: fitz Page object
        Returns:
            List of dictionaries, each containing drawing elements and their bounding box.
        """
        extracted_drawings = []
        try:
            drawings = page.get_drawings()
            text_blocks = page.get_text("blocks") # Get text blocks to find potential titles

            for drawing_index, drawing_info in enumerate(drawings):
                # The 'rect' key typically gives the bounding box of the entire drawing
                bbox = drawing_info.get('rect') 
                if bbox:
                    bbox = list(bbox) # Convert fitz.Rect to list for JSON serialization
                else:
                    # If 'rect' is not present, calculate a bounding box from items if possible
                    min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
                    for item in drawing_info.get('items', []):
                        if item[0] == 're': # Rectangle
                            r = fitz.Rect(item[1])
                            min_x = min(min_x, r.x0)
                            min_y = min(min_y, r.y0)
                            max_x = max(max_x, r.x1)
                            max_y = max(max_y, r.y1)
                        elif item[0] == 'l': # Line
                            p1, p2 = fitz.Point(item[1]), fitz.Point(item[2])
                            min_x = min(min_x, p1.x, p2.x)
                            min_y = min(min_y, p1.y, p2.y)
                            max_x = max(max_x, p1.x, p2.x)
                            max_y = max(max_y, p1.y, p2.y)
                        # Add other item types as needed (e.g., 'c' for curve, 'qu' for quad)
                    if min_x != float('inf'):
                        bbox = [min_x, min_y, max_x, max_y]
                    else:
                        logging.warning(f"Could not determine bounding box for drawing {drawing_index + 1} on page {page.number + 1}. Skipping.")
                        continue


                drawing_title = None
                if bbox:
                    drawing_rect = fitz.Rect(bbox) 
                    sorted_text_blocks = sorted(text_blocks, key=lambda x: x[1])

                    for text_block in sorted_text_blocks:
                        text_bbox = fitz.Rect(text_block[0], text_block[1], text_block[2], text_block[3])
                        text_content = text_block[4].strip()

                        if (text_bbox.y1 < drawing_rect.y0 and 
                            abs(drawing_rect.y0 - text_bbox.y1) < 50 and 
                            text_bbox.intersects(drawing_rect)):
                            
                            lower_text = text_content.lower()
                            if lower_text.startswith(("fig.", "figure", "table", "chart", "graph")):
                                drawing_title = text_content
                                break
                
                extracted_drawings.append({
                    'type': 'vector_drawing',
                    'bbox': bbox,
                    'page_number': page.number + 1,
                    'title': drawing_title if drawing_title else f"Vector Drawing on Page {page.number + 1}, Drawing {drawing_index + 1}",
                    'drawing_elements': drawing_info # Includes all details like colors, lines, fills, etc.
                })
            logging.debug(f"Extracted {len(extracted_drawings)} vector drawings metadata from page {page.number + 1}")
        except Exception as e:
            logging.error(f"Error extracting vector drawings metadata from page {page.number + 1}: {str(e)}")
        return extracted_drawings

    def extract_pdf_content(self, pdf_path: str) -> Dict:
        """
        Extract all text, raster image metadata, and vector drawing metadata.
        Args:
            pdf_path: Path to the PDF file
        Returns:
            Dictionary containing extracted text, raster image metadata, and vector drawing metadata.
        """
        self.all_extracted_text = []
        self.all_extracted_raster_images = []
        self.all_extracted_vector_drawings = []
        
        try:
            logging.info(f"Starting content extraction of PDF: {pdf_path} (no image files will be saved)")
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text
                page_text_blocks = self.extract_text_from_page(page)
                self.all_extracted_text.extend([{'page_number': page.number + 1, **block} for block in page_text_blocks])

                # Extract raster images metadata
                page_raster_images_data = self.extract_raster_images_metadata_from_page(doc, page)
                self.all_extracted_raster_images.extend(page_raster_images_data)

                # Extract vector drawings metadata
                page_vector_drawings_data = self.extract_vector_drawings_metadata_from_page(page)
                self.all_extracted_vector_drawings.extend(page_vector_drawings_data)
            
            doc.close()
            logging.info(f"PDF content extraction completed. Extracted {len(self.all_extracted_text)} text blocks, {len(self.all_extracted_raster_images)} raster images metadata, and {len(self.all_extracted_vector_drawings)} vector drawings metadata.")
            
            
        except Exception as e:
            logging.error(f"Critical error during PDF content extraction for {pdf_path}: {str(e)}")
            return {
                'extracted_text': [],
                'extracted_raster_images': [],
                'extracted_vector_drawings': []
            }


    def extract_all_text_simple(self, pdf_path: str) -> List[Dict]:
        """
        Extracts all plain text content from each page of the PDF.
        Args:
            pdf_path: Path to the PDF file
        Returns:
            List of dictionaries, each containing page number and its full text content.
        """
        self.all_text_content = []
        try:
            logging.info(f"Starting simple text extraction from: {pdf_path}")
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text() # Get all text as a single string
                
                # Filter out non-printable characters and then strip whitespace
                filtered_text = ''.join(filter(lambda x: x in string.printable, text)).strip()
                
                if filtered_text: # Only add if there's actual printable text after filtering
                    self.all_text_content.append({
                        'page_number': page.number + 1,
                        'text_content': filtered_text
                    })
                logging.debug(f"Extracted simple text from page {page.number + 1}")
            doc.close()
            logging.info(f"Simple text extraction completed for {len(self.all_text_content)} pages.")
        except Exception as e:
            logging.error(f"Error during simple text extraction from {pdf_path}: {str(e)}")
        return self.all_text_content

    
    