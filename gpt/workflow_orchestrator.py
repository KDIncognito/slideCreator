import json
from typing import Dict, List, Optional
from .core import gptHandler
from .supportContext import gptContext
from ..utils.logger import get_logger

class SlideCreationWorkflow:
    def __init__(self):
        self.gpt_handler = gptHandler()
        self.context = gptContext()
        self.processing_state = {}
        self.logger = get_logger()
    
    def process_document_to_slides(self, extracted_text: str, 
                                 image_analyses: List[str] = None) -> Dict:
        """Complete pipeline from extracted content to slide structure."""
        
        self.logger.info("(>>>) Starting GPT processing pipeline")
        
        # Step 1: Security check
        self.logger.debug("(^^^) Performing security check")
        security_result = self._check_content_security(extracted_text)
        if not security_result.get('is_safe', False):
            self.logger.error("(XXX) Content failed security check")
            return {'error': 'Content failed security check', 'details': security_result}
        
        # Step 2: Break down concepts
        self.logger.debug("(^^^) Extracting concepts from content")
        concepts = self._extract_concepts(extracted_text)
        
        # Step 3: Generate image prompts for visualization needs
        self.logger.debug("(^^^) Generating image prompts")
        image_prompts = self._generate_image_prompts(concepts)
        
        # Step 4: Convert to slide structure
        self.logger.debug("(^^^) Creating slide structure")
        slides = self._create_slide_structure(concepts)
        
        # Step 5: Integrate image analyses if provided
        if image_analyses:
            self.logger.debug("(^^^) Integrating existing visuals")
            slides = self._integrate_existing_visuals(slides, image_analyses)
        
        self.logger.info("(!!!) GPT processing pipeline completed")
        
        return {
            'security_check': security_result,
            'concepts': concepts,
            'image_prompts': image_prompts,
            'slides': slides,
            'processing_metadata': self.processing_state
        }
    
    def _check_content_security(self, text_content: str) -> Dict:
        """Security analysis of content."""
        try:
            response = self.gpt_handler.llm_handler(
                system=self.context.malicious.system,
                user=self.context.malicious.user.format(text_content=text_content)
            )
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"(XXX) Security check failed: {str(e)}")
            return {'is_safe': False, 'error': str(e)}
    
    def _extract_concepts(self, text_content: str) -> Dict:
        """Extract structured concepts from text."""
        try:
            response = self.gpt_handler.llm_handler(
                system=self.context.breakdownConcepts.system,
                user=self.context.breakdownConcepts.user.format(text_content=text_content)
            )
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"(XXX) Concept extraction failed: {str(e)}")
            return {'error': f'Concept extraction failed: {str(e)}'}
    
    def _generate_image_prompts(self, concepts: Dict) -> List[Dict]:
        """Generate image prompts for concepts needing visualization."""
        if 'concepts' not in concepts:
            return []
        
        # Filter concepts that need new generation
        concepts_needing_visuals = [
            concept for concept in concepts['concepts']
            if concept.get('visualization_opportunity', {}).get('needs_new_generation', False)
        ]
        
        if not concepts_needing_visuals:
            return []
        
        try:
            response = self.gpt_handler.llm_handler(
                system=self.context.generateImagePrompts.system,
                user=self.context.generateImagePrompts.user.format(
                    text_content=json.dumps(concepts_needing_visuals, indent=2)
                )
            )
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"(XXX) Image prompt generation failed: {str(e)}")
            return [{'error': f'Image prompt generation failed: {str(e)}'}]
    
    def _create_slide_structure(self, concepts: Dict) -> Dict:
        """Convert concepts to slide structure."""
        try:
            response = self.gpt_handler.llm_handler(
                system=self.context.convertToSlides.system,
                user=self.context.convertToSlides.user.format(
                    text_content=json.dumps(concepts, indent=2)
                )
            )
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"(XXX) Slide creation failed: {str(e)}")
            return {'error': f'Slide creation failed: {str(e)}'}
    
    def _integrate_existing_visuals(self, slides: Dict, 
                                  image_analyses: List[str]) -> Dict:
        """Integrate analysis of existing PDF visuals into slides."""
        self.processing_state['existing_visuals_integrated'] = len(image_analyses)
        return slides
    
    def analyze_pdf_image(self, image_data: str) -> str:
        """Analyze a single PDF page image."""
        messages = [
            {
                "role": "system",
                "content": self.context.imageAnalysis.system
            },
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": self.context.imageAnalysis.user},
                    {"type": "image_url", "url": f"data:image/jpeg;base64,{image_data}"}
                ]
            }
        ]
        
        return self.gpt_handler.llm_handler(
            system="", user="", request_type="vision", messages=messages
        )
