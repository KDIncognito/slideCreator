import time
import json
from typing import Callable, Any, Dict, Optional
from functools import wraps

class GPTErrorHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def with_retry(self, func: Callable) -> Callable:
        """Decorator for adding retry logic to GPT calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    return self._validate_response(result)
                
                except json.JSONDecodeError as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        time.sleep(self.base_delay * (2 ** attempt))
                        continue
                
                except Exception as e:
                    last_exception = e
                    if attempt < self.max_retries:
                        time.sleep(self.base_delay * (2 ** attempt))
                        continue
            
            return self._create_error_response(last_exception)
        
        return wrapper
    
    def _validate_response(self, response: str) -> Dict:
        """Validate and parse GPT response."""
        try:
            parsed = json.loads(response)
            return {'success': True, 'data': parsed}
        except json.JSONDecodeError:
            # Try to extract JSON from response if it's wrapped in text
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return {'success': True, 'data': parsed}
                except json.JSONDecodeError:
                    pass
            
            return {'success': False, 'error': 'Invalid JSON response', 'raw_response': response}
    
    def _create_error_response(self, exception: Exception) -> Dict:
        """Create standardized error response."""
        return {
            'success': False,
            'error': str(exception),
            'error_type': type(exception).__name__
        }
