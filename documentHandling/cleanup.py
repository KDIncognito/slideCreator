import re

class clean_text:
    """
    A class to clean text by removing code blocks and inline code formatting.
    """
    def __init__(self):
        """
        Initializes the clean_text class.
        """

    def clean_text(self, text:str=None):
        """
        Cleans the text by removing code blocks and inline code formatting.
        Args:
            text (str): The text to be cleaned.
        Returns:
            str: The cleaned text with code blocks and inline code removed.
        """
        return re.sub(r"`+\w+|`+","", text)
