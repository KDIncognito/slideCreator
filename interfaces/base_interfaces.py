from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    """Standard result format for all processing operations."""
    success: bool
    data: Any = None
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class IPDFProcessor(ABC):
    """Interface for PDF processing components."""
    
    @abstractmethod
    def convert_pdf_to_images(self, pdf_path: str, output_dir: str) -> Dict[int, str]:
        """Convert PDF pages to images."""
        pass
    
    @abstractmethod
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[int, str]:
        """Extract text content from PDF pages."""
        pass
    
    @abstractmethod
    def validate_pdf_file(self, pdf_path: str) -> ProcessingResult:
        """Validate PDF file format and accessibility."""
        pass


class IVisualAnalyzer(ABC):
    """Interface for visual content analysis."""
    
    @abstractmethod
    def detect_visual_elements(self, image_path: str, page_num: int) -> List[Any]:
        """Detect visual elements in an image."""
        pass
    
    @abstractmethod
    def extract_text_sections(self, text_content: str, page_num: int) -> List[Any]:
        """Extract and categorize text sections."""
        pass
    
    @abstractmethod
    def create_mappings(self, text_sections: List[Any], visual_elements: List[Any]) -> List[Any]:
        """Create mappings between text and visual elements."""
        pass


class IAIProcessor(ABC):
    """Interface for AI processing components."""
    
    @abstractmethod
    def process_text_content(self, content: str, processing_type: str) -> ProcessingResult:
        """Process text content using AI."""
        pass
    
    @abstractmethod
    def analyze_image(self, image_data: str) -> ProcessingResult:
        """Analyze image using AI vision capabilities."""
        pass
    
    @abstractmethod
    def validate_response(self, response: str, expected_type: str) -> ProcessingResult:
        """Validate AI response against expected format."""
        pass


class IPresentationGenerator(ABC):
    """Interface for presentation generation."""
    
    @abstractmethod
    def create_presentation(self, slides_data: Dict, output_path: str, **kwargs) -> str:
        """Create presentation file from slide data."""
        pass
    
    @abstractmethod
    def validate_slide_data(self, slides_data: Dict) -> ProcessingResult:
        """Validate slide data structure."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        pass


class IValidator(ABC):
    """Interface for input validation components."""
    
    @abstractmethod
    def validate_input(self, data: Any, validation_type: str) -> ProcessingResult:
        """Validate input data."""
        pass
    
    @abstractmethod
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data."""
        pass


class ILogger(ABC):
    """Interface for logging components."""
    
    @abstractmethod
    def log_info(self, message: str, context: Dict = None) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def log_error(self, message: str, exception: Exception = None, context: Dict = None) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def log_debug(self, message: str, context: Dict = None) -> None:
        """Log debug message."""
        pass


class ISlideCreator(ABC):
    """Interface for the main slide creation orchestrator."""
    
    @abstractmethod
    def convert_pdf_to_slides(self, pdf_path: str, output_path: str = None) -> str:
        """Convert PDF to presentation slides."""
        pass
    
    @abstractmethod
    def validate_environment(self) -> ProcessingResult:
        """Validate system environment and dependencies."""
        pass
    
    @abstractmethod
    def get_conversion_info(self, pdf_path: str) -> Dict:
        """Get information about conversion without executing it."""
        pass
