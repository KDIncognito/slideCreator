import openai
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class SlideContent:
    title: str
    bullet_points: List[str]
    speaker_notes: str
    suggested_visual: str

class ContentProcessor:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def transform_academic_to_presentation(self, text_content: str, 
                                         context: Dict = None) -> SlideContent:
        """Transform dense academic text into presentation-friendly content."""
        prompt = f"""
        Transform this academic content into a presentation slide format:

        Academic Text:
        {text_content}

        Requirements:
        - Create a clear, engaging slide title
        - Extract 3-5 key bullet points (max 10 words each)
        - Write concise speaker notes
        - Suggest appropriate visual aids

        Context: {context if context else 'General academic presentation'}

        Return as JSON with keys: title, bullet_points, speaker_notes, suggested_visual
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return SlideContent(**result)
    
    def analyze_visual_content(self, image_description: str, 
                             surrounding_text: str) -> Dict:
        """Analyze what a visual element represents and how to describe it."""
        prompt = f"""
        Analyze this visual element and its context:

        Visual Description: {image_description}
        Surrounding Text: {surrounding_text}

        Provide:
        1. What the visual shows (data type, trends, relationships)
        2. Key insights from the visual
        3. How to reference it in a presentation
        4. Suggested slide title that incorporates the visual

        Return as JSON with keys: visual_summary, key_insights, presentation_reference, slide_title
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_slide_narrative(self, slide_contents: List[SlideContent]) -> str:
        """Create a cohesive narrative flow across slides."""
        slides_summary = "\n".join([
            f"Slide {i+1}: {slide.title} - {', '.join(slide.bullet_points[:2])}"
            for i, slide in enumerate(slide_contents)
        ])
        
        prompt = f"""
        Create smooth transitions between these presentation slides:

        {slides_summary}

        Provide transition phrases and connection points to ensure logical flow.
        Return as JSON with keys: transitions, overall_narrative, suggested_reordering
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        
        return json.loads(response.choices[0].message.content)
    
    def suggest_missing_visuals(self, text_content: str, 
                              existing_visuals: List[str]) -> List[Dict]:
        """Suggest new charts/graphs that would enhance the presentation."""
        prompt = f"""
        Based on this content, suggest visual aids that would improve understanding:

        Content: {text_content}
        Existing Visuals: {existing_visuals}

        Suggest 2-3 new charts/graphs with:
        - Type of chart (bar, line, pie, scatter, etc.)
        - Data to visualize
        - Purpose/insight it would show
        - Where in presentation it should go

        Return as JSON array with keys: chart_type, data_focus, purpose, placement_suggestion
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        return json.loads(response.choices[0].message.content)
    
    def extract_key_terminology(self, text_content: str) -> Dict:
        """Extract and define key terms for presentation clarity."""
        prompt = f"""
        Identify key technical terms and concepts from this academic text:

        {text_content}

        For each term provide:
        - Simple definition for general audience
        - Whether it needs explanation in presentation
        - Suggested slide for definition

        Return as JSON with keys: terms (dict of term:definition), explanation_needed, definition_slides
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        return json.loads(response.choices[0].message.content)
