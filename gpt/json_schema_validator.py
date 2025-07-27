import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from .schemas.response_schemas import ResponseSchemas

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    parsed_data: Optional[Dict] = None

class JSONSchemaValidator:
    """
    Validates GPT responses against expected JSON schemas.
    Uses centralized schema definitions from ResponseSchemas.
    """
    
    def __init__(self):
        self.schemas = ResponseSchemas.get_all_schemas()
    
    def validate_response(self, response_text: str, expected_type: str) -> ValidationResult:
        """
        Validate a GPT response against its expected schema.
        
        Args:
            response_text: Raw response from GPT API
            expected_type: Type of response (e.g., 'malicious', 'breakdownConcepts', etc.)
        """
        errors = []
        warnings = []
        parsed_data = None
        
        # Step 1: Parse JSON
        try:
            parsed_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            # Try to extract JSON from wrapped text
            extracted_json = self._extract_json_from_text(response_text)
            if extracted_json:
                try:
                    parsed_data = json.loads(extracted_json)
                    warnings.append("JSON was wrapped in additional text")
                except json.JSONDecodeError:
                    errors.append(f"Invalid JSON format: {str(e)}")
                    return ValidationResult(False, errors, warnings, None)
            else:
                errors.append(f"Invalid JSON format: {str(e)}")
                return ValidationResult(False, errors, warnings, None)
        
        # Step 2: Validate against schema
        if expected_type not in self.schemas:
            warnings.append(f"No schema defined for type: {expected_type}")
            return ValidationResult(True, errors, warnings, parsed_data)
        
        schema = self.schemas[expected_type]
        validation_errors = self._validate_against_schema(parsed_data, schema, expected_type)
        errors.extend(validation_errors)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, parsed_data)
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON from text that might be wrapped with additional content."""
        import re
        
        # Look for JSON object patterns
        json_patterns = [
            r'\{.*\}',  # Basic object
            r'\[.*\]',  # Array
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group()
        
        return None
    
    def _validate_against_schema(self, data: Dict, schema: Dict, context: str) -> List[str]:
        """Validate parsed data against a schema definition."""
        errors = []
        
        # Check required fields
        required_fields = schema.get('required_fields', [])
        for field in required_fields:
            if field not in data:
                errors.append(f"{context}: Missing required field '{field}'")
        
        # Check field types
        field_types = schema.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in data:
                if not self._check_type(data[field], expected_type):
                    errors.append(f"{context}: Field '{field}' has incorrect type. Expected {expected_type}, got {type(data[field])}")
        
        # Check enum values
        enum_values = schema.get('enum_values', {})
        for field, valid_values in enum_values.items():
            if field in data and data[field] not in valid_values:
                errors.append(f"{context}: Field '{field}' has invalid value '{data[field]}'. Valid values: {valid_values}")
        
        # Check nested validations
        nested_validations = schema.get('nested_validations', {})
        for field, nested_schema in nested_validations.items():
            if field in data and isinstance(data[field], list):
                for i, item in enumerate(data[field]):
                    if isinstance(item, dict):
                        item_errors = self._validate_nested_item(item, nested_schema, f"{context}.{field}[{i}]")
                        errors.extend(item_errors)
        
        return errors
    
    def _validate_nested_item(self, item: Dict, nested_schema: Dict, context: str) -> List[str]:
        """Validate a nested item against its schema."""
        errors = []
        
        # Check required fields for nested items
        required_fields = nested_schema.get('item_required_fields', [])
        for field in required_fields:
            if field not in item:
                errors.append(f"{context}: Missing required field '{field}'")
        
        # Check field types for nested items
        field_types = nested_schema.get('item_field_types', {})
        for field, expected_type in field_types.items():
            if field in item:
                if not self._check_type(item[field], expected_type):
                    errors.append(f"{context}: Field '{field}' has incorrect type. Expected {expected_type}, got {type(item[field])}")
        
        # Check enum values for nested items
        enum_values = nested_schema.get('item_enum_values', {})
        for field, valid_values in enum_values.items():
            if field in item and item[field] not in valid_values:
                errors.append(f"{context}: Field '{field}' has invalid value '{item[field]}'. Valid values: {valid_values}")
        
        return errors
    
    def _check_type(self, value: Any, expected_type: Union[type, tuple]) -> bool:
        """Check if a value matches the expected type."""
        if isinstance(expected_type, tuple):
            return isinstance(value, expected_type)
        return isinstance(value, expected_type)
    
    def validate_concept_ids_consistency(self, concepts_data: Dict) -> List[str]:
        """Validate that all concept ID references are consistent."""
        errors = []
        
        if 'concepts' not in concepts_data:
            return errors
        
        # Collect all concept IDs
        concept_ids = {concept.get('id') for concept in concepts_data['concepts'] if 'id' in concept}
        
        # Check relationships reference valid concept IDs
        for i, concept in enumerate(concepts_data['concepts']):
            if 'relationships' in concept:
                for j, relationship in enumerate(concept['relationships']):
                    related_id = relationship.get('related_concept_id')
                    if related_id and related_id not in concept_ids:
                        errors.append(f"Concept[{i}].relationships[{j}]: References non-existent concept ID '{related_id}'")
        
        return errors
    
    def get_schema_template(self, schema_type: str) -> str:
        """Get the JSON template for a schema type."""
        return ResponseSchemas.get_json_template(schema_type)
    
    def get_schema_description(self, schema_type: str) -> str:
        """Get description of a schema type."""
        return ResponseSchemas.get_schema_description(schema_type)
