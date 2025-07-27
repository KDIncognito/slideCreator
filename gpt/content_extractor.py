from .core import gptHandler
from typing import List, Dict, Any

class ContentExtractor:
    def __init__(self):
        self.gpt_handler = gptHandler()
        self.structure_system = """You are an expert document analyzer. Extract and organize content into structured formats. Always respond in JSON format."""
        
        self.structure_prompt = """
        Based on the following page analyses from a PDF document, extract and organize the content into a structured format:
        
        1. Document title and main topic
        2. Key sections and their hierarchical structure
        3. Main concepts and ideas organized by topic
        4. Important data points, statistics, or findings
        5. Visual elements and their significance
        6. Overall document flow and logical progression
        
        Provide a well-organized summary that captures the document's essence and structure.
        """
        
        self.summary_system = """You are an expert document summarizer. Create comprehensive summaries that capture the essence of documents. Always respond in JSON format."""
        
        self.summary_prompt = """
        Create a comprehensive summary of this entire document based on all page analyses.
        Focus on:
        1. Main purpose and objectives
        2. Key findings or conclusions
        3. Important concepts covered
        4. Data insights or statistics
        5. Overall document structure and flow
        
        Provide a concise but thorough summary that someone could use to understand the document's content without reading it.
        """
    
    def extract_document_structure(self, page_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract structured content from all page analyses."""
        # Combine all successful analyses
        successful_analyses = [page["analysis"] for page in page_analyses 
                             if page["status"] == "success" and page["analysis"]]
        
        if not successful_analyses:
            return {"error": "No successful page analyses to process"}
        
        # Create combined analysis text
        combined_text = "\n\n--- PAGE SEPARATOR ---\n\n".join(successful_analyses)
        
        try:
            # Use gptHandler to structure the content
            structured_analysis = self.gpt_handler.llm_handler(
                system=self.structure_system,
                user=f"{self.structure_prompt}\n\nPAGE ANALYSES:\n{combined_text}",
                request_type="text"
            )
            
            return {
                "structured_content": structured_analysis,
                "total_analyzed_pages": len(successful_analyses),
                "extraction_status": "success"
            }
            
        except Exception as e:
            return {
                "error": f"Failed to extract structure: {str(e)}",
                "extraction_status": "failed"
            }
    
    def generate_document_summary(self, analyses: List[str]) -> str:
        """Generate a comprehensive document summary."""
        if not analyses:
            return "No content available for summary generation."
        
        combined_text = "\n\n--- PAGE SEPARATOR ---\n\n".join(analyses)
        
        try:
            summary = self.gpt_handler.llm_handler(
                system=self.summary_system,
                user=f"{self.summary_prompt}\n\nDOCUMENT CONTENT:\n{combined_text}",
                request_type="text"
            )
            return summary
            
        except Exception as e:
            return f"Failed to generate summary: {str(e)}"
