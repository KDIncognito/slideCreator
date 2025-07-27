from typing import Dict, List, Tuple
from .json_schema_validator import JSONSchemaValidator, ValidationResult
from ..utils.logger import get_logger

class ResponseValidator:
    def __init__(self):
        self.json_validator = JSONSchemaValidator()
        self.logger = get_logger()
        self.required_fields = {
            'concepts': ['concepts', 'overall_confidence_score'],
            'slides': ['presentation_title', 'slides', 'number_of_slides'],
            'security': ['is_safe', 'threat_level', 'findings']
        }
    
    def validate_gpt_response(self, response_text: str, expected_type: str) -> ValidationResult:
        """
        Main validation method that combines JSON schema validation with business logic checks.
        
        Args:
            response_text: Raw response from GPT API
            expected_type: Type of expected response ('malicious', 'breakdownConcepts', etc.)
        """
        
        self.logger.debug(f"(^^^) Validating {expected_type} response")
        
        # First, validate JSON structure
        json_result = self.json_validator.validate_response(response_text, expected_type)
        
        if not json_result.is_valid:
            self.logger.warning(f"(!!!) JSON validation failed for {expected_type}")
            for error in json_result.errors:
                self.logger.debug(f"JSON Error: {error}")
            return json_result
        
        # Then, apply business logic validations
        business_logic_errors = []
        
        if expected_type == 'breakdownConcepts':
            concept_errors = self._validate_concept_business_logic(json_result.parsed_data)
            business_logic_errors.extend(concept_errors)
            
            # Check concept ID consistency
            id_consistency_errors = self.json_validator.validate_concept_ids_consistency(json_result.parsed_data)
            business_logic_errors.extend(id_consistency_errors)
        
        elif expected_type == 'convertToSlides':
            slide_errors = self._validate_slide_business_logic(json_result.parsed_data)
            business_logic_errors.extend(slide_errors)
        
        # Update validation result
        json_result.errors.extend(business_logic_errors)
        json_result.is_valid = len(json_result.errors) == 0
        
        if json_result.is_valid:
            self.logger.debug(f"(!!!) {expected_type} validation successful")
        else:
            self.logger.warning(f"(!!!) Business logic validation failed for {expected_type}")
            for error in business_logic_errors:
                self.logger.debug(f"Business Logic Error: {error}")
        
        return json_result
    
    def validate_concept_extraction(self, response: Dict) -> Tuple[bool, List[str]]:
        """Validate concept extraction response."""
        errors = []
        
        if not self._check_required_fields(response, 'concepts'):
            errors.append("Missing required fields for concept extraction")
        
        if 'concepts' in response:
            for i, concept in enumerate(response['concepts']):
                concept_errors = self._validate_single_concept(concept, i)
                errors.extend(concept_errors)
        
        return len(errors) == 0, errors
    
    def validate_slide_generation(self, response: Dict) -> Tuple[bool, List[str]]:
        """Validate slide generation response."""
        errors = []
        
        if not self._check_required_fields(response, 'slides'):
            errors.append("Missing required fields for slide generation")
        
        if 'slides' in response:
            for i, slide in enumerate(response['slides']):
                slide_errors = self._validate_single_slide(slide, i)
                errors.extend(slide_errors)
        
        # Check slide count consistency
        if 'number_of_slides' in response and 'slides' in response:
            if response['number_of_slides'] != len(response['slides']):
                errors.append("Slide count mismatch")
        
        return len(errors) == 0, errors
    
    def validate_security_check(self, response: Dict) -> Tuple[bool, List[str]]:
        """Validate security check response."""
        errors = []
        
        if not self._check_required_fields(response, 'security'):
            errors.append("Missing required fields for security check")
        
        # Validate threat level enum
        valid_threat_levels = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if response.get('threat_level') not in valid_threat_levels:
            errors.append(f"Invalid threat level: {response.get('threat_level')}")
        
        return len(errors) == 0, errors
    
    def _validate_concept_business_logic(self, data: Dict) -> List[str]:
        """Apply business logic validation to concept extraction data."""
        errors = []
        
        if 'concepts' in data:
            # Check for reasonable number of concepts
            if len(data['concepts']) > 20:
                errors.append("Too many concepts extracted (>20). Consider consolidation.")
            elif len(data['concepts']) == 0:
                errors.append("No concepts extracted. This may indicate processing failure.")
            
            # Check confidence score range
            confidence = data.get('overall_confidence_score', 0)
            if not (0.0 <= confidence <= 1.0):
                errors.append(f"Confidence score {confidence} outside valid range [0.0, 1.0]")
            
            # Check for duplicate concept IDs
            concept_ids = [concept.get('id') for concept in data['concepts'] if 'id' in concept]
            if len(concept_ids) != len(set(concept_ids)):
                errors.append("Duplicate concept IDs found")
        
        return errors
    
    def _validate_slide_business_logic(self, data: Dict) -> List[str]:
        """Apply business logic validation to slide generation data."""
        errors = []
        
        if 'slides' in data:
            # Check slide count consistency
            actual_count = len(data['slides'])
            expected_count = data.get('number_of_slides', actual_count)
            
            if actual_count != expected_count:
                errors.append(f"Slide count mismatch: expected {expected_count}, got {actual_count}")
            
            # Check for reasonable presentation length
            if actual_count > 20:
                errors.append("Presentation too long (>20 slides). Consider reducing content.")
            elif actual_count < 3:
                errors.append("Presentation too short (<3 slides). May need more content.")
            
            # Validate individual slides
            for i, slide in enumerate(data['slides']):
                slide_errors = self._validate_single_slide_logic(slide, i)
                errors.extend(slide_errors)
        
        return errors
    
    def _validate_single_slide_logic(self, slide: Dict, index: int) -> List[str]:
        """Validate business logic for a single slide."""
        errors = []
        
        # Check bullet point count
        bullet_points = slide.get('bullet_points', [])
        if len(bullet_points) > 8:
            errors.append(f"Slide {index}: Too many bullet points ({len(bullet_points)}). Max recommended: 8")
        elif len(bullet_points) == 0:
            errors.append(f"Slide {index}: No bullet points provided")
        
        # Check title length
        title = slide.get('title', '')
        if len(title.split()) > 12:
            errors.append(f"Slide {index}: Title too long ({len(title.split())} words). Max recommended: 12")
        
        # Validate visual placeholder consistency
        visual_placeholder = slide.get('generated_visual_placeholder')
        if visual_placeholder and isinstance(visual_placeholder, dict):
            need_image = visual_placeholder.get('need_image', False)
            if need_image and not visual_placeholder.get('source_text_for_visual'):
                errors.append(f"Slide {index}: Visual needed but no source text provided")
        
        return errors
    
    def _check_required_fields(self, response: Dict, response_type: str) -> bool:
        """Check if all required fields are present."""
        required = self.required_fields.get(response_type, [])
        return all(field in response for field in required)
    
    def _validate_single_concept(self, concept: Dict, index: int) -> List[str]:
        """Validate a single concept object."""
        errors = []
        required_concept_fields = ['id', 'title', 'summary', 'keywords']
        
        for field in required_concept_fields:
            if field not in concept:
                errors.append(f"Concept {index}: Missing required field '{field}'")
        
        # Validate relationships reference existing concept IDs
        if 'relationships' in concept:
            for rel in concept['relationships']:
                if 'related_concept_id' not in rel:
                    errors.append(f"Concept {index}: Relationship missing concept ID")
        
        return errors
    
    def _validate_single_slide(self, slide: Dict, index: int) -> List[str]:
        """Validate a single slide object."""
        errors = []
        required_slide_fields = ['slide_id', 'title', 'bullet_points']
        
        for field in required_slide_fields:
            if field not in slide:
                errors.append(f"Slide {index}: Missing required field '{field}'")
        
        # Validate bullet points
        if 'bullet_points' in slide:
            if not isinstance(slide['bullet_points'], list):
                errors.append(f"Slide {index}: bullet_points must be a list")
            elif len(slide['bullet_points']) > 8:
                errors.append(f"Slide {index}: Too many bullet points ({len(slide['bullet_points'])})")
        
        return errors
