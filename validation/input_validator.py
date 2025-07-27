import os
import re
from pathlib import Path
from typing import Any, Dict, List
from dataclasses import dataclass
from ..interfaces.base_interfaces import IValidator, ProcessingResult
from ..utils.logger import get_logger


@dataclass
class ValidationRule:
    """Represents a single validation rule."""
    name: str
    rule_type: str  # 'required', 'type', 'format', 'range', 'custom'
    parameters: Dict[str, Any]
    error_message: str


class InputValidator(IValidator):
    """Comprehensive input validation system."""
    
    def __init__(self):
        self.logger = get_logger()
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> Dict[str, List[ValidationRule]]:
        """Initialize validation rules for different input types."""
        return {
            'pdf_path': [
                ValidationRule(
                    name='required',
                    rule_type='required',
                    parameters={},
                    error_message='PDF path is required'
                ),
                ValidationRule(
                    name='file_exists',
                    rule_type='custom',
                    parameters={'function': self._validate_file_exists},
                    error_message='PDF file does not exist'
                ),
                ValidationRule(
                    name='pdf_extension',
                    rule_type='format',
                    parameters={'pattern': r'\.pdf$', 'case_sensitive': False},
                    error_message='File must have .pdf extension'
                ),
                ValidationRule(
                    name='file_readable',
                    rule_type='custom',
                    parameters={'function': self._validate_file_readable},
                    error_message='PDF file is not readable'
                ),
                ValidationRule(
                    name='file_size',
                    rule_type='range',
                    parameters={'min_size': 1024, 'max_size': 100 * 1024 * 1024},  # 1KB to 100MB
                    error_message='PDF file size must be between 1KB and 100MB'
                )
            ],
            'output_path': [
                ValidationRule(
                    name='valid_directory',
                    rule_type='custom',
                    parameters={'function': self._validate_output_directory},
                    error_message='Output directory does not exist or is not writable'
                ),
                ValidationRule(
                    name='valid_filename',
                    rule_type='format',
                    parameters={'pattern': r'^[^<>:"/\\|?*]+$'},
                    error_message='Output filename contains invalid characters'
                )
            ],
            'slide_data': [
                ValidationRule(
                    name='required_fields',
                    rule_type='custom',
                    parameters={'function': self._validate_slide_data_structure},
                    error_message='Slide data missing required fields'
                ),
                ValidationRule(
                    name='slide_count',
                    rule_type='range',
                    parameters={'min_count': 1, 'max_count': 50},
                    error_message='Slide count must be between 1 and 50'
                )
            ],
            'text_content': [
                ValidationRule(
                    name='not_empty',
                    rule_type='custom',
                    parameters={'function': self._validate_text_not_empty},
                    error_message='Text content cannot be empty'
                ),
                ValidationRule(
                    name='length_limit',
                    rule_type='range',
                    parameters={'min_length': 10, 'max_length': 1000000},  # 10 chars to 1MB
                    error_message='Text content length must be between 10 characters and 1MB'
                ),
                ValidationRule(
                    name='safe_content',
                    rule_type='custom',
                    parameters={'function': self._validate_safe_content},
                    error_message='Text content contains potentially unsafe elements'
                )
            ]
        }
    
    def validate_input(self, data: Any, validation_type: str) -> ProcessingResult:
        """
        Validate input data according to specified validation type.
        
        Args:
            data: Data to validate
            validation_type: Type of validation to perform
            
        Returns:
            ProcessingResult with validation outcome
        """
        
        if validation_type not in self.validation_rules:
            return ProcessingResult(
                success=False,
                errors=[f"Unknown validation type: {validation_type}"]
            )
        
        rules = self.validation_rules[validation_type]
        errors = []
        warnings = []
        
        for rule in rules:
            try:
                result = self._apply_validation_rule(data, rule)
                if not result['valid']:
                    if result.get('severity') == 'warning':
                        warnings.append(result['message'])
                    else:
                        errors.append(result['message'])
            except Exception as e:
                self.logger.error(f"(XXX) Validation rule '{rule.name}' failed: {str(e)}")
                errors.append(f"Validation error in rule '{rule.name}': {str(e)}")
        
        return ProcessingResult(
            success=len(errors) == 0,
            data=data,
            errors=errors,
            warnings=warnings,
            metadata={'validation_type': validation_type, 'rules_applied': len(rules)}
        )
    
    def sanitize_input(self, data: Any) -> Any:
        """
        Sanitize input data to remove potentially harmful content.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data
    
    def _apply_validation_rule(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Apply a single validation rule to data."""
        
        if rule.rule_type == 'required':
            return self._validate_required(data, rule)
        elif rule.rule_type == 'type':
            return self._validate_type(data, rule)
        elif rule.rule_type == 'format':
            return self._validate_format(data, rule)
        elif rule.rule_type == 'range':
            return self._validate_range(data, rule)
        elif rule.rule_type == 'custom':
            return self._validate_custom(data, rule)
        else:
            return {'valid': False, 'message': f"Unknown rule type: {rule.rule_type}"}
    
    def _validate_required(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate that required data is present."""
        if data is None or (isinstance(data, str) and not data.strip()):
            return {'valid': False, 'message': rule.error_message}
        return {'valid': True, 'message': 'Required validation passed'}
    
    def _validate_type(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate data type."""
        expected_type = rule.parameters.get('expected_type')
        if not isinstance(data, expected_type):
            return {'valid': False, 'message': f"{rule.error_message}. Expected {expected_type.__name__}, got {type(data).__name__}"}
        return {'valid': True, 'message': 'Type validation passed'}
    
    def _validate_format(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate data format using regex pattern."""
        if not isinstance(data, str):
            return {'valid': False, 'message': 'Format validation requires string input'}
        
        pattern = rule.parameters.get('pattern')
        case_sensitive = rule.parameters.get('case_sensitive', True)
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        if not re.search(pattern, data, flags):
            return {'valid': False, 'message': rule.error_message}
        return {'valid': True, 'message': 'Format validation passed'}
    
    def _validate_range(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate data falls within specified range."""
        params = rule.parameters
        
        # File size validation
        if 'min_size' in params and 'max_size' in params:
            if isinstance(data, str):  # File path
                try:
                    file_size = Path(data).stat().st_size
                    if not (params['min_size'] <= file_size <= params['max_size']):
                        return {'valid': False, 'message': rule.error_message}
                except Exception:
                    return {'valid': False, 'message': 'Cannot determine file size'}
        
        # Length validation
        elif 'min_length' in params and 'max_length' in params:
            length = len(data) if hasattr(data, '__len__') else 0
            if not (params['min_length'] <= length <= params['max_length']):
                return {'valid': False, 'message': rule.error_message}
        
        # Count validation
        elif 'min_count' in params and 'max_count' in params:
            if isinstance(data, dict) and 'slides' in data:
                count = len(data['slides'])
                if not (params['min_count'] <= count <= params['max_count']):
                    return {'valid': False, 'message': rule.error_message}
        
        return {'valid': True, 'message': 'Range validation passed'}
    
    def _validate_custom(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Apply custom validation function."""
        validation_function = rule.parameters.get('function')
        if callable(validation_function):
            return validation_function(data, rule)
        return {'valid': False, 'message': 'Invalid custom validation function'}
    
    # Custom validation functions
    def _validate_file_exists(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate that file exists."""
        try:
            if not isinstance(data, str):
                return {'valid': False, 'message': 'File path must be a string'}
            
            path = Path(data)
            if not path.exists():
                return {'valid': False, 'message': rule.error_message}
            if not path.is_file():
                return {'valid': False, 'message': 'Path exists but is not a file'}
            
            return {'valid': True, 'message': 'File exists validation passed'}
        except Exception as e:
            return {'valid': False, 'message': f'File validation error: {str(e)}'}
    
    def _validate_file_readable(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate that file is readable."""
        try:
            with open(data, 'rb') as f:
                f.read(1024)  # Try to read first 1KB
            return {'valid': True, 'message': 'File readable validation passed'}
        except Exception:
            return {'valid': False, 'message': rule.error_message}
    
    def _validate_output_directory(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate output directory is writable."""
        try:
            if not isinstance(data, str):
                return {'valid': False, 'message': 'Output path must be a string'}
            
            path = Path(data)
            directory = path.parent if path.suffix else path
            
            if not directory.exists():
                return {'valid': False, 'message': 'Output directory does not exist'}
            if not os.access(directory, os.W_OK):
                return {'valid': False, 'message': 'Output directory is not writable'}
            
            return {'valid': True, 'message': 'Output directory validation passed'}
        except Exception as e:
            return {'valid': False, 'message': f'Output directory validation error: {str(e)}'}
    
    def _validate_slide_data_structure(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate slide data has required structure."""
        if not isinstance(data, dict):
            return {'valid': False, 'message': 'Slide data must be a dictionary'}
        
        required_fields = ['slides', 'presentation_title']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {'valid': False, 'message': f"Missing required fields: {', '.join(missing_fields)}"}
        
        if not isinstance(data['slides'], list):
            return {'valid': False, 'message': 'Slides must be a list'}
        
        return {'valid': True, 'message': 'Slide data structure validation passed'}
    
    def _validate_text_not_empty(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate text content is not empty."""
        if not isinstance(data, str):
            return {'valid': False, 'message': 'Text content must be a string'}
        
        if not data.strip():
            return {'valid': False, 'message': rule.error_message}
        
        return {'valid': True, 'message': 'Text not empty validation passed'}
    
    def _validate_safe_content(self, data: Any, rule: ValidationRule) -> Dict[str, Any]:
        """Validate content doesn't contain potentially unsafe elements."""
        if not isinstance(data, str):
            return {'valid': True, 'message': 'Non-string content assumed safe'}
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script[^>]*>',  # Script tags
            r'javascript:',     # JavaScript URLs
            r'data:.*base64',   # Base64 data URLs
            r'eval\s*\(',       # Eval function calls
            r'exec\s*\(',       # Exec function calls
        ]
        
        warnings = []
        for pattern in suspicious_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                warnings.append(f"Potentially unsafe content pattern detected: {pattern}")
        
        if warnings:
            return {
                'valid': True, 
                'message': 'Content contains suspicious patterns but allowed',
                'severity': 'warning'
            }
        
        return {'valid': True, 'message': 'Safe content validation passed'}
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string input."""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove or escape potentially dangerous sequences
        dangerous_patterns = [
            (r'<script[^>]*>.*?</script>', ''),  # Remove script tags
            (r'javascript:', 'text:'),           # Replace javascript URLs
            (r'eval\s*\(', 'eval_disabled('),   # Disable eval calls
        ]
        
        for pattern, replacement in dangerous_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
