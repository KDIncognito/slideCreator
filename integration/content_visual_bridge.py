import json
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from ..analysis.visual_text_mapper import VisualTextMapper, ContentVisualMapping, VisualElement, TextSection
from ..gpt.workflow_orchestrator import SlideCreationWorkflow
from ..gpt.core import gptHandler
from ..gpt.supportContext import gptContext
from ..utils.logger import get_logger

class ContentVisualBridge:
    """
    Bridges the gap between visual analysis (visual_text_mapper) and GPT processing.
    This class orchestrates the complete pipeline from PDF analysis to slide generation.
    """
    
    def __init__(self):
        self.visual_mapper = VisualTextMapper()
        self.slide_workflow = SlideCreationWorkflow()
        self.gpt_handler = gptHandler()
        self.context = gptContext()
        self.logger = get_logger()
    
    def process_complete_document(self, 
                                extracted_text_by_page: Dict[int, str],
                                image_paths_by_page: Dict[int, str]) -> Dict:
        """
        Complete pipeline: PDF text + images → slide-ready content
        
        Args:
            extracted_text_by_page: {page_num: text_content}
            image_paths_by_page: {page_num: image_path}
        """
        
        self.logger.info("(>>>) Starting complete document processing pipeline")
        
        # Step 1: Analyze visual-text relationships
        self.logger.debug("(^^^) Creating visual-text mappings")
        visual_mappings = self._create_visual_text_mappings(
            extracted_text_by_page, image_paths_by_page
        )
        
        # Step 2: Enhance text with visual context for GPT
        self.logger.debug("(^^^) Enriching text with visual context")
        enriched_text = self._enrich_text_with_visual_context(
            extracted_text_by_page, visual_mappings
        )
        
        # Step 3: Get detailed image analyses using GPT Vision
        self.logger.debug("(^^^) Analyzing images with GPT Vision")
        image_analyses = self._analyze_images_with_gpt(image_paths_by_page)
        
        # Step 4: Process through GPT workflow with visual context
        self.logger.debug("(^^^) Processing through GPT workflow")
        slide_result = self.slide_workflow.process_document_to_slides(
            enriched_text, image_analyses
        )
        
        # Step 5: Map existing visuals to generated slides
        self.logger.debug("(^^^) Integrating visual mappings to slides")
        final_slides = self._integrate_visual_mappings_to_slides(
            slide_result, visual_mappings, image_analyses
        )
        
        self.logger.info("(!!!) Document processing pipeline completed successfully")
        
        return {
            'visual_mappings': [asdict(mapping) for mapping in visual_mappings],
            'image_analyses': image_analyses,
            'slides': final_slides,
            'processing_metadata': {
                'total_pages': len(extracted_text_by_page),
                'visual_elements_found': len([m for m in visual_mappings if m.visual_element]),
                'high_confidence_mappings': len([m for m in visual_mappings if m.confidence_score > 0.7])
            }
        }
    
    def _create_visual_text_mappings(self, 
                                   text_by_page: Dict[int, str],
                                   image_paths: Dict[int, str]) -> List[ContentVisualMapping]:
        """Create mappings between text and visual elements across all pages."""
        
        all_text_sections = []
        all_visual_elements = []
        
        # Extract text sections from all pages
        for page_num, text_content in text_by_page.items():
            sections = self.visual_mapper.extract_text_sections(text_content, page_num)
            all_text_sections.extend(sections)
        
        self.logger.debug(f"Extracted {len(all_text_sections)} text sections")
        
        # Detect visual elements from all pages
        for page_num, image_path in image_paths.items():
            elements = self.visual_mapper.detect_visual_elements(image_path, page_num)
            all_visual_elements.extend(elements)
        
        self.logger.debug(f"Detected {len(all_visual_elements)} visual elements")
        
        # Create mappings
        mappings = self.visual_mapper.create_mappings(all_text_sections, all_visual_elements)
        
        self.logger.debug(f"Created {len(mappings)} visual-text mappings")
        
        return mappings
    
    def _enrich_text_with_visual_context(self, 
                                       text_by_page: Dict[int, str],
                                       mappings: List[ContentVisualMapping]) -> str:
        """Enrich text content with visual context information for better GPT processing."""
        
        # Combine all text
        combined_text = "\n\n".join([
            f"=== PAGE {page_num} ===\n{text}" 
            for page_num, text in text_by_page.items()
        ])
        
        # Add visual context annotations
        visual_context = "\n\n=== VISUAL ELEMENTS CONTEXT ===\n"
        
        for mapping in mappings:
            if mapping.confidence_score > 0.5:  # Only include high-confidence mappings
                visual_context += f"""
VISUAL ELEMENT on Page {mapping.visual_element.page_number}:
- Type: {mapping.visual_element.element_type}
- Relationship: {mapping.relationship_type} (confidence: {mapping.confidence_score:.2f})
- Related Text: "{mapping.text_section.content[:200]}..."
- Location: {mapping.visual_element.bbox}

"""
        
        return combined_text + visual_context
    
    def _analyze_images_with_gpt(self, image_paths: Dict[int, str]) -> List[Dict]:
        """Use GPT Vision to analyze each image in detail."""
        
        image_analyses = []
        
        for page_num, image_path in image_paths.items():
            try:
                self.logger.debug(f"Analyzing image for page {page_num}: {image_path}")
                
                # Convert image to base64 (you'll need to implement this)
                image_data = self._image_to_base64(image_path)
                
                # Analyze with GPT Vision
                analysis = self.slide_workflow.analyze_pdf_image(image_data)
                
                image_analyses.append({
                    'page_number': page_num,
                    'image_path': image_path,
                    'gpt_analysis': analysis,
                    'analysis_timestamp': self._get_timestamp()
                })
                
            except Exception as e:
                self.logger.warning(f"(!!!) Failed to analyze image for page {page_num}: {str(e)}")
                image_analyses.append({
                    'page_number': page_num,
                    'image_path': image_path,
                    'error': str(e),
                    'analysis_timestamp': self._get_timestamp()
                })
        
        return image_analyses
    
    def _integrate_visual_mappings_to_slides(self, 
                                           slide_result: Dict,
                                           mappings: List[ContentVisualMapping],
                                           image_analyses: List[Dict]) -> Dict:
        """Integrate visual mappings into the generated slide structure."""
        
        if 'slides' not in slide_result or 'slides' not in slide_result['slides']:
            return slide_result
        
        slides = slide_result['slides']['slides']
        
        # For each slide, try to match it with relevant visuals
        for slide in slides:
            slide_concepts = slide.get('concept_ids_covered', [])
            
            # Find visual mappings that relate to this slide's concepts
            relevant_visuals = self._find_relevant_visuals_for_slide(
                slide_concepts, mappings, image_analyses
            )
            
            # Add visual recommendations to slide
            if relevant_visuals:
                slide['existing_visual_suggestions'] = relevant_visuals
                
                # If slide doesn't have a generated visual, suggest using an existing one
                if not slide.get('generated_visual_placeholder', {}).get('need_image', False):
                    best_visual = max(relevant_visuals, key=lambda x: x['confidence'])
                    slide['recommended_existing_visual'] = best_visual
        
        return slide_result
    
    def _find_relevant_visuals_for_slide(self, 
                                       slide_concepts: List[str],
                                       mappings: List[ContentVisualMapping],
                                       image_analyses: List[Dict]) -> List[Dict]:
        """Find visual elements that are relevant to a specific slide."""
        
        relevant_visuals = []
        
        for mapping in mappings:
            # Check if this mapping relates to the slide's concepts
            # (This is a simplified approach - you might want more sophisticated matching)
            
            # Get the corresponding image analysis
            image_analysis = next(
                (img for img in image_analyses 
                 if img['page_number'] == mapping.visual_element.page_number),
                None
            )
            
            if image_analysis and mapping.confidence_score > 0.4:
                relevant_visuals.append({
                    'visual_element': asdict(mapping.visual_element),
                    'confidence': mapping.confidence_score,
                    'relationship_type': mapping.relationship_type,
                    'gpt_analysis': image_analysis.get('gpt_analysis', ''),
                    'usage_suggestion': self._generate_visual_usage_suggestion(mapping, image_analysis)
                })
        
        return relevant_visuals
    
    def _generate_visual_usage_suggestion(self, 
                                        mapping: ContentVisualMapping,
                                        image_analysis: Dict) -> str:
        """Generate a suggestion for how to use this visual in the presentation."""
        
        prompt = f"""
        Based on this visual-text relationship, suggest how to use this visual in a presentation slide:
        
        Visual Type: {mapping.visual_element.element_type}
        Relationship: {mapping.relationship_type}
        Text Context: {mapping.text_section.content[:300]}
        GPT Visual Analysis: {image_analysis.get('gpt_analysis', 'Not available')[:300]}
        
        Provide a brief suggestion (1-2 sentences) for how to incorporate this visual.
        """
        
        try:
            response = self.gpt_handler.llm_handler(
                system="You are a presentation design expert. Provide concise, actionable suggestions.",
                user=prompt
            )
            return response
        except Exception as e:
            return f"Use this {mapping.visual_element.element_type} to support the main content."
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string."""
        import base64
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
