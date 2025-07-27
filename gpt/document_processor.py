from .image_analyzer import ImageAnalyzer
from .content_extractor import ContentExtractor
from typing import List, Dict, Any

class DocumentProcessor:
    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.content_extractor = ContentExtractor()
    
    def process_document_images(self, image_paths: List[str]) -> Dict[str, Any]:
        """Process all images from a PDF document and extract structured content."""
        print(f"Processing {len(image_paths)} images...")
        
        # Analyze each image
        page_analyses = []
        for i, image_path in enumerate(image_paths, 1):
            print(f"Analyzing page {i}/{len(image_paths)}...")
            analysis = self.image_analyzer.analyze_image(image_path)
            analysis["page_number"] = i
            page_analyses.append(analysis)
        
        # Extract and structure the content
        print("Extracting structured content...")
        structured_content = self.content_extractor.extract_document_structure(page_analyses)
        
        return {
            "total_pages": len(image_paths),
            "page_analyses": page_analyses,
            "structured_content": structured_content,
            "processing_status": "complete"
        }
    
    def get_document_summary(self, processed_document: Dict[str, Any]) -> str:
        """Generate a comprehensive summary of the entire document."""
        all_analyses = [page["analysis"] for page in processed_document["page_analyses"] 
                       if page["status"] == "success"]
        
        return self.content_extractor.generate_document_summary(all_analyses)
