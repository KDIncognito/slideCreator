import os
import sys
import io
from pathlib import Path
from typing import Dict, Optional
import logging

# Try different PIL import methods
try:
    from PIL import Image
except ImportError:
    try:
        import PIL.Image as Image
    except ImportError:
        print("Error: PIL/Pillow not found. Please install with: pip install Pillow")
        sys.exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not found. Please install with: pip install PyMuPDF")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFToImageConverter:
    """
    Convert PDF files to images optimized for GPT-4o/4o-mini ingestion.
    Maintains high resolution while ensuring compatibility with OpenAI's vision models.
    """
    
    def __init__(self, output_format: str = "PNG", dpi: int = 300, max_dimension: int = 2048):
        """
        Initialize the PDF converter.
        
        Args:
            output_format: Image format (PNG, JPEG)
            dpi: Resolution for conversion (300 recommended for quality)
            max_dimension: Maximum width/height to ensure GPT-4o compatibility
        """
        self.output_format = output_format.upper()
        self.dpi = dpi
        self.max_dimension = max_dimension
        
        # GPT-4o recommended settings
        self.max_file_size_mb = 20  # OpenAI limit
        self.supported_formats = ["PNG", "JPEG", "JPG"]
        
        if self.output_format not in self.supported_formats:
            raise ValueError(f"Unsupported format. Use: {', '.join(self.supported_formats)}")
    
    def convert_pdf_to_images(self, pdf_path: str, output_dir: Optional[str] = None) -> Dict[int, str]:
        """
        Convert a PDF file to a series of images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save images (optional, defaults to same as PDF)
            
        Returns:
            Dictionary mapping page numbers to image file paths
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if output_dir is None:
            output_dir = pdf_path.parent / f"{pdf_path.stem}_images"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Converting PDF: {pdf_path}")
        logger.info(f"Output directory: {output_dir}")
        
        try:
            # Use PyMuPDF for better quality and control
            doc = fitz.open(pdf_path)
            image_paths = {}  # Changed from list to dict
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Calculate matrix for desired DPI
                zoom = self.dpi / 72  # 72 is default DPI
                matrix = fitz.Matrix(zoom, zoom)
                
                # Render page to pixmap
                pix = page.get_pixmap(matrix=matrix)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Optimize for GPT-4o
                optimized_image = self._optimize_for_gpt4o(image)
                
                # Save image
                output_filename = f"page_{page_num + 1:03d}.{self.output_format.lower()}"
                output_path = output_dir / output_filename
                
                self._save_image(optimized_image, output_path)
                image_paths[page_num + 1] = str(output_path)  # 1-based page numbering
                
                logger.info(f"Converted page {page_num + 1}/{doc.page_count}")
            
            doc.close()
            logger.info(f"Successfully converted {len(image_paths)} pages")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF: {str(e)}")
            raise
    
    def _optimize_for_gpt4o(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for GPT-4o ingestion while maintaining quality.
        
        Args:
            image: PIL Image object
            
        Returns:
            Optimized PIL Image object
        """
        # Get current dimensions
        width, height = image.size
        
        # Check if resizing is needed
        if max(width, height) > self.max_dimension:
            # Calculate new dimensions maintaining aspect ratio
            if width > height:
                new_width = self.max_dimension
                new_height = int((height * self.max_dimension) / width)
            else:
                new_height = self.max_dimension
                new_width = int((width * self.max_dimension) / height)
            
            logger.info(f"Resizing from {width}x{height} to {new_width}x{new_height}")
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary (for JPEG)
        if self.output_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            # Create white background for transparency
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = background
        
        return image
    
    def _save_image(self, image: Image.Image, output_path: Path) -> None:
        """
        Save image with optimized settings for GPT-4o.
        
        Args:
            image: PIL Image object
            output_path: Path to save the image
        """
        save_kwargs = {}
        
        if self.output_format == "PNG":
            save_kwargs = {
                "optimize": True,
                "compress_level": 6  # Good balance of size and quality
            }
        elif self.output_format == "JPEG":
            save_kwargs = {
                "quality": 95,  # High quality for text readability
                "optimize": True
            }
        
        image.save(output_path, format=self.output_format, **save_kwargs)
        
        # Check file size and warn if too large
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            logger.warning(f"Image {output_path.name} is {file_size_mb:.1f}MB, "
                         f"which exceeds GPT-4o limit of {self.max_file_size_mb}MB")
    
    def batch_convert(self, pdf_directory: str, output_base_dir: Optional[str] = None) -> dict:
        """
        Convert multiple PDF files in a directory.
        
        Args:
            pdf_directory: Directory containing PDF files
            output_base_dir: Base directory for output (optional)
            
        Returns:
            Dictionary mapping PDF filenames to dictionaries of page-to-image mappings
        """
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            raise FileNotFoundError(f"Directory not found: {pdf_dir}")
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return {}
        
        results = {}
        
        for pdf_file in pdf_files:
            try:
                if output_base_dir:
                    output_dir = Path(output_base_dir) / f"{pdf_file.stem}_images"
                else:
                    output_dir = None
                
                image_paths = self.convert_pdf_to_images(pdf_file, output_dir)
                results[pdf_file.name] = image_paths
                
            except Exception as e:
                logger.error(f"Failed to convert {pdf_file.name}: {str(e)}")
                results[pdf_file.name] = []
        
        return results
    
    def get_image_info(self, image_path: str) -> dict:
        """
        Get information about a converted image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image information
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with Image.open(image_path) as img:
            file_size_mb = image_path.stat().st_size / (1024 * 1024)
            
            return {
                "filename": image_path.name,
                "dimensions": img.size,
                "format": img.format,
                "mode": img.mode,
                "file_size_mb": round(file_size_mb, 2),
                "gpt4o_compatible": file_size_mb <= self.max_file_size_mb
            }


def main():
    """
    Command line interface for PDF to image conversion.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert PDF to images for GPT-4o ingestion")
    parser.add_argument("pdf_path", help="Path to PDF file or directory")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("-f", "--format", choices=["PNG", "JPEG"], default="PNG", help="Output format")
    parser.add_argument("-d", "--dpi", type=int, default=300, help="DPI for conversion")
    parser.add_argument("-m", "--max-dimension", type=int, default=2048, help="Maximum image dimension")
    parser.add_argument("--batch", action="store_true", help="Process all PDFs in directory")
    
    args = parser.parse_args()
    
    try:
        converter = PDFToImageConverter(
            output_format=args.format,
            dpi=args.dpi,
            max_dimension=args.max_dimension
        )
        
        if args.batch:
            results = converter.batch_convert(args.pdf_path, args.output)
            print(f"Processed {len(results)} PDF files")
            for pdf_name, images in results.items():
                print(f"  {pdf_name}: {len(images)} images")
        else:
            image_paths = converter.convert_pdf_to_images(args.pdf_path, args.output)
            print(f"Successfully converted to {len(image_paths)} images:")
            for path in image_paths.values():
                info = converter.get_image_info(path)
                print(f"  {info['filename']}: {info['dimensions']} - {info['file_size_mb']}MB")
    
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
