import re

class cleantext:
    """
    A class to clean text by removing code blocks and inline code formatting.
    """
    def __init__(self):
        """
        Initializes the clean_text class.
        """

    def clean_text(self, text:str = None):
        """Clean text by removing markdown code blocks and other unwanted characters"""
        # CRITICAL FIX: Ensure text is actually a string
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        
        # Debug what we're working with
        print(f"DEBUG cleanup.py: Input type: {type(text)}")
        print(f"DEBUG cleanup.py: Input: {repr(text)[:100]}...")
        
        try:
            # Remove markdown code blocks and backticks
            cleaned = re.sub(r"`+\w+|`+", "", text)
            return cleaned
        except Exception as e:
            print(f"ERROR in clean_text: {e}")
            print(f"ERROR text type: {type(text)}")
            print(f"ERROR text value: {repr(text)[:200]}...")
            return str(text)  # Fallback to original