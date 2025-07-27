import cv2
import numpy as np
from typing import Dict, List, Tuple
import re
from dataclasses import dataclass

@dataclass
class VisualElement:
    image_path: str
    page_number: int
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    element_type: str  # 'chart', 'graph', 'table', 'diagram'
    extracted_text: str
    features: Dict
    confidence: float

@dataclass
class TextSection:
    content: str
    page_number: int
    section_type: str  # 'paragraph', 'heading', 'caption', 'reference'
    keywords: List[str]
    data_references: List[str]

@dataclass
class ContentVisualMapping:
    text_section: TextSection
    visual_element: VisualElement
    relationship_type: str  # 'direct_reference', 'supporting_data', 'explanation', 'summary'
    confidence_score: float
    contextual_distance: int  # pages between text and visual

class VisualTextMapper:
    def __init__(self):
        self.data_keywords = [
            'figure', 'chart', 'graph', 'table', 'diagram', 'plot', 'analysis',
            'results', 'data', 'statistics', 'percentage', 'ratio', 'correlation',
            'trend', 'comparison', 'distribution', 'frequency', 'average', 'median'
        ]
        self.reference_patterns = [
            r'[Ff]igure\s+\d+',
            r'[Tt]able\s+\d+',
            r'[Cc]hart\s+\d+',
            r'[Gg]raph\s+\d+',
            r'see\s+above',
            r'see\s+below',
            r'as\s+shown',
            r'depicted\s+in'
        ]
    
    def detect_visual_elements(self, image_path: str, page_num: int) -> List[VisualElement]:
        """Detect and classify visual elements in an image."""
        # Load image
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        visual_elements = []
        
        # Detect chart-like structures
        charts = self._detect_charts(gray, image_path, page_num)
        visual_elements.extend(charts)
        
        # Detect tables
        tables = self._detect_tables(gray, image_path, page_num)
        visual_elements.extend(tables)
        
        return visual_elements
    
    def _detect_charts(self, gray_image, image_path: str, page_num: int) -> List[VisualElement]:
        """Detect chart and graph elements."""
        charts = []
        
        # Look for rectangular regions with high edge density (potential charts)
        edges = cv2.Canny(gray_image, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5000:  # Minimum area for a chart
                x, y, w, h = cv2.boundingRect(contour)
                
                # Extract region for analysis
                roi = gray_image[y:y+h, x:x+w]
                
                # Analyze if it looks like a chart
                chart_confidence = self._analyze_chart_features(roi)
                
                if chart_confidence > 0.6:
                    charts.append(VisualElement(
                        image_path=image_path,
                        page_number=page_num,
                        bbox=(x, y, w, h),
                        element_type='chart',
                        extracted_text='',
                        features={'edge_density': chart_confidence},
                        confidence=chart_confidence
                    ))
        
        return charts
    
    def _detect_tables(self, gray_image, image_path: str, page_num: int) -> List[VisualElement]:
        """Detect table structures."""
        tables = []
        
        # Look for grid-like structures
        horizontal_lines = cv2.morphologyEx(gray_image, cv2.MORPH_OPEN, 
                                          cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
        vertical_lines = cv2.morphologyEx(gray_image, cv2.MORPH_OPEN,
                                        cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
        
        grid = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0)
        contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 3000:
                x, y, w, h = cv2.boundingRect(contour)
                tables.append(VisualElement(
                    image_path=image_path,
                    page_number=page_num,
                    bbox=(x, y, w, h),
                    element_type='table',
                    extracted_text='',
                    features={'grid_strength': area / (w * h)},
                    confidence=0.8
                ))
        
        return tables
    
    def _analyze_chart_features(self, roi) -> float:
        """Analyze if a region contains chart-like features."""
        # Simple heuristic: charts have moderate edge density and some structure
        edges = cv2.Canny(roi, 50, 150)
        edge_density = np.sum(edges > 0) / (roi.shape[0] * roi.shape[1])
        
        # Look for axis-like structures (straight lines)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=50)
        line_count = len(lines) if lines is not None else 0
        
        confidence = min(edge_density * 10 + line_count * 0.1, 1.0)
        return confidence
    
    def extract_text_sections(self, text_content: str, page_num: int) -> List[TextSection]:
        """Extract and categorize text sections."""
        sections = []
        
        # Split into paragraphs
        paragraphs = text_content.split('\n\n')
        
        for para in paragraphs:
            if len(para.strip()) < 50:  # Skip very short paragraphs
                continue
                
            # Extract keywords and data references
            keywords = self._extract_keywords(para)
            data_refs = self._extract_data_references(para)
            
            # Classify section type
            section_type = self._classify_section_type(para)
            
            sections.append(TextSection(
                content=para,
                page_number=page_num,
                section_type=section_type,
                keywords=keywords,
                data_references=data_refs
            ))
        
        return sections
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract data-related keywords from text."""
        keywords = []
        text_lower = text.lower()
        
        for keyword in self.data_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _extract_data_references(self, text: str) -> List[str]:
        """Extract references to figures, tables, etc."""
        references = []
        
        for pattern in self.reference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        return references
    
    def _classify_section_type(self, text: str) -> str:
        """Classify the type of text section."""
        text_lower = text.lower()
        
        if any(ref in text_lower for ref in ['figure', 'table', 'chart']):
            return 'caption'
        elif len(text) < 200 and text.isupper():
            return 'heading'
        elif any(word in text_lower for word in ['reference', 'cite', 'bibliography']):
            return 'reference'
        else:
            return 'paragraph'
    
    def create_mappings(self, text_sections: List[TextSection], 
                       visual_elements: List[VisualElement]) -> List[ContentVisualMapping]:
        """Create mappings between text sections and visual elements."""
        mappings = []
        
        for text_section in text_sections:
            for visual_element in visual_elements:
                relationship = self._analyze_relationship(text_section, visual_element)
                
                if relationship['confidence'] > 0.3:  # Threshold for meaningful relationship
                    mappings.append(ContentVisualMapping(
                        text_section=text_section,
                        visual_element=visual_element,
                        relationship_type=relationship['type'],
                        confidence_score=relationship['confidence'],
                        contextual_distance=abs(text_section.page_number - visual_element.page_number)
                    ))
        
        # Sort by confidence score
        mappings.sort(key=lambda x: x.confidence_score, reverse=True)
        return mappings
    
    def _analyze_relationship(self, text_section: TextSection, 
                            visual_element: VisualElement) -> Dict:
        """Analyze the relationship between a text section and visual element."""
        confidence = 0.0
        relationship_type = 'supporting_data'
        
        # Direct reference check
        if text_section.data_references:
            confidence += 0.5
            relationship_type = 'direct_reference'
        
        # Keyword overlap
        if text_section.keywords:
            confidence += len(text_section.keywords) * 0.1
        
        # Page proximity
        page_distance = abs(text_section.page_number - visual_element.page_number)
        if page_distance == 0:
            confidence += 0.3
        elif page_distance == 1:
            confidence += 0.2
        elif page_distance <= 3:
            confidence += 0.1
        
        # Section type bonus
        if text_section.section_type == 'caption':
            confidence += 0.4
            relationship_type = 'explanation'
        
        return {
            'confidence': min(confidence, 1.0),
            'type': relationship_type
        }
