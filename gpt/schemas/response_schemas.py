from typing import Dict, Any, List, Union
from dataclasses import dataclass
import json

@dataclass
class SchemaField:
    """Represents a field in a JSON schema with validation rules."""
    name: str
    field_type: type
    required: bool = True
    enum_values: List[str] = None
    description: str = ""
    example: Any = None

@dataclass
class NestedSchema:
    """Represents nested object schemas within arrays or objects."""
    required_fields: List[str]
    field_types: Dict[str, type]
    enum_values: Dict[str, List[str]] = None
    description: str = ""

class ResponseSchemas:
    """
    Centralized JSON schema definitions for all GPT prompt responses.
    Used by both prompt generation and response validation systems.
    """
    
    @staticmethod
    def get_malicious_schema() -> Dict[str, Any]:
        """Schema for malicious content detection responses."""
        return {
            'type': 'object',
            'required_fields': ['is_safe', 'threat_level', 'findings', 'overall_assessment'],
            'field_types': {
                'is_safe': bool,
                'threat_level': str,
                'findings': list,
                'overall_assessment': str
            },
            'enum_values': {
                'threat_level': ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            },
            'nested_validations': {
                'findings': {
                    'item_required_fields': ['type', 'description', 'confidence', 'location_hint', 'recommended_action', 'excerpt'],
                    'item_field_types': {
                        'type': str,
                        'description': str,
                        'confidence': float,
                        'location_hint': str,
                        'recommended_action': str,
                        'excerpt': str
                    },
                    'item_enum_values': {
                        'type': ['OBFUSCATION', 'MALICIOUS_URL', 'SCRIPT_INJECTION', 'PHISHING', 'ANOMALY', 'OTHER'],
                        'recommended_action': ['CONTINUE_WITH_CAUTION', 'REVIEW_MANUALLY', 'REJECT_DOCUMENT_PROCESSING']
                    }
                }
            },
            'example': {
                "is_safe": True,
                "threat_level": "NONE",
                "findings": [],
                "overall_assessment": "Content appears safe for processing."
            },
            'json_template': '''
{
    "is_safe": true,
    "threat_level": "NONE",
    "findings": [
        {
            "type": "OBFUSCATION",
            "description": "Detailed description of the potential threat found.",
            "confidence": 0.85,
            "location_hint": "paragraph 3, sentence 2",
            "recommended_action": "CONTINUE_WITH_CAUTION",
            "excerpt": "Short snippet of suspicious text"
        }
    ],
    "overall_assessment": "Concise overall conclusion on safety."
}'''
        }
    
    @staticmethod
    def get_breakdown_concepts_schema() -> Dict[str, Any]:
        """Schema for concept breakdown responses."""
        return {
            'type': 'object',
            'required_fields': ['concepts', 'overall_confidence_score', 'notes'],
            'field_types': {
                'concepts': list,
                'overall_confidence_score': float,
                'notes': list
            },
            'nested_validations': {
                'concepts': {
                    'item_required_fields': ['id', 'title', 'summary', 'keywords', 'context_reference', 'relationships', 'visualization_opportunity'],
                    'item_field_types': {
                        'id': str,
                        'title': str,
                        'summary': str,
                        'keywords': list,
                        'context_reference': str,
                        'relationships': list,
                        'visualization_opportunity': dict
                    }
                }
            },
            'example': {
                "concepts": [
                    {
                        "id": "quantum_ml_overview",
                        "title": "Quantum Machine Learning Overview",
                        "summary": "Explores quantum-AI fusion for enhanced data processing.",
                        "keywords": ["Quantum Computing", "Machine Learning", "AI"],
                        "context_reference": "Introduction: Section 1.1",
                        "relationships": [],
                        "visualization_opportunity": {
                            "needs_new_generation": True,
                            "data_present_for_graph": False,
                            "suggested_visual_types": ["Conceptual Diagram"],
                            "visual_purpose": "Illustrate quantum-AI synergy",
                            "key_visual_elements_hint": ["Quantum sphere", "Neural network"],
                            "source_text_for_visual": "Sample text about quantum ML"
                        }
                    }
                ],
                "overall_confidence_score": 0.95,
                "notes": ["Processing completed successfully"]
            },
            'json_template': '''
{
    "concepts": [
        {
            "id": "concept_unique_id",
            "title": "Concept Title (max 10 words)",
            "summary": "Brief summary (max 50 words)",
            "keywords": ["keyword1", "keyword2"],
            "context_reference": "Section reference",
            "relationships": [
                {
                    "related_concept_id": "other_concept_id",
                    "type": "SUPPORTS",
                    "description": "Relationship description"
                }
            ],
            "visualization_opportunity": {
                "needs_new_generation": true,
                "data_present_for_graph": false,
                "suggested_visual_types": ["Conceptual Diagram"],
                "visual_purpose": "Purpose description",
                "key_visual_elements_hint": ["element1", "element2"],
                "source_text_for_visual": "Exact text from source"
            }
        }
    ],
    "overall_confidence_score": 0.95,
    "notes": ["Processing notes"]
}'''
        }
    
    @staticmethod
    def get_convert_to_slides_schema() -> Dict[str, Any]:
        """Schema for slide conversion responses."""
        return {
            'type': 'object',
            'required_fields': ['presentation_title', 'number_of_slides', 'slides', 'overall_presentation_guidance', 'disclaimer'],
            'field_types': {
                'presentation_title': str,
                'number_of_slides': int,
                'slides': list,
                'overall_presentation_guidance': list,
                'disclaimer': str
            },
            'nested_validations': {
                'slides': {
                    'item_required_fields': ['slide_id', 'concept_ids_covered', 'title', 'main_text_summary', 'bullet_points', 'generated_visual_placeholder', 'speaking_notes_key_points', 'suggested_layout_type'],
                    'item_field_types': {
                        'slide_id': str,
                        'concept_ids_covered': list,
                        'title': str,
                        'main_text_summary': str,
                        'bullet_points': list,
                        'generated_visual_placeholder': (dict, type(None)),
                        'speaking_notes_key_points': list,
                        'suggested_layout_type': str
                    }
                }
            },
            'json_template': '''
{
    "presentation_title": "Presentation Title",
    "number_of_slides": 3,
    "slides": [
        {
            "slide_id": "slide_01_intro",
            "concept_ids_covered": ["concept_id1"],
            "title": "Slide Title",
            "main_text_summary": "Brief slide summary",
            "bullet_points": ["Point 1", "Point 2", "Point 3"],
            "generated_visual_placeholder": {
                "image_placeholder_id": "slide_01_visual_01",
                "concept_id_link": "concept_id1",
                "description_for_audience": "Figure 1: Description",
                "recommended_placement": "FULL_SLIDE",
                "need_image": true,
                "caption": "Visual caption",
                "source_text_for_visual": "Source text for visual"
            },
            "speaking_notes_key_points": ["Note 1", "Note 2"],
            "suggested_layout_type": "TITLE_CONTENT_BULLETS",
            "call_to_action_or_takeaway": "Main takeaway"
        }
    ],
    "overall_presentation_guidance": ["Guidance 1", "Guidance 2"],
    "disclaimer": "AI-generated content disclaimer"
}'''
        }
    
    @staticmethod
    def get_visual_element_extraction_schema() -> Dict[str, Any]:
        """Schema for visual element extraction responses."""
        return {
            'type': 'object',
            'required_fields': ['visual_elements', 'text_content_summary', 'overall_page_purpose'],
            'field_types': {
                'visual_elements': list,
                'text_content_summary': str,
                'overall_page_purpose': str
            },
            'nested_validations': {
                'visual_elements': {
                    'item_required_fields': ['type', 'data_insight', 'key_points', 'slide_suitability', 'suggested_context', 'location_description'],
                    'item_field_types': {
                        'type': str,
                        'data_insight': str,
                        'key_points': list,
                        'slide_suitability': str,
                        'suggested_context': str,
                        'location_description': str
                    },
                    'item_enum_values': {
                        'slide_suitability': ['high', 'medium', 'low']
                    }
                }
            },
            'json_template': '''
{
    "visual_elements": [
        {
            "type": "bar_chart",
            "data_insight": "Shows quarterly revenue growth",
            "key_points": ["Q4 shows 30% increase", "Consistent upward trend"],
            "slide_suitability": "high",
            "suggested_context": "Financial performance overview",
            "location_description": "Center of page, below heading"
        }
    ],
    "text_content_summary": "Brief summary of non-visual text",
    "overall_page_purpose": "What this page aims to communicate"
}'''
        }
    
    @staticmethod
    def get_all_schemas() -> Dict[str, Dict[str, Any]]:
        """Get all schemas in a single dictionary."""
        return {
            'malicious': ResponseSchemas.get_malicious_schema(),
            'breakdownConcepts': ResponseSchemas.get_breakdown_concepts_schema(),
            'convertToSlides': ResponseSchemas.get_convert_to_slides_schema(),
            'visual_element_extraction': ResponseSchemas.get_visual_element_extraction_schema(),
            'slide_content_extraction': {
                'required_fields': ['potential_slide_titles', 'key_bullet_points', 'supporting_data', 'main_takeaway', 'audience_relevance'],
                'field_types': {
                    'potential_slide_titles': list,
                    'key_bullet_points': list,
                    'supporting_data': list,
                    'main_takeaway': str,
                    'audience_relevance': str
                }
            },
            'chart_data_extraction': {
                'required_fields': ['charts_data', 'summary'],
                'field_types': {
                    'charts_data': list,
                    'summary': str
                },
                'nested_validations': {
                    'charts_data': {
                        'item_required_fields': ['chart_type', 'title', 'data_points', 'insights', 'axis_labels'],
                        'item_field_types': {
                            'chart_type': str,
                            'title': str,
                            'data_points': list,
                            'insights': list,
                            'axis_labels': dict
                        }
                    }
                }
            }
        }
    
    @staticmethod
    def get_json_template(schema_name: str) -> str:
        """Get the JSON template for a specific schema."""
        schema = ResponseSchemas.get_all_schemas().get(schema_name, {})
        return schema.get('json_template', '{}')
    
    @staticmethod
    def get_schema_description(schema_name: str) -> str:
        """Get a human-readable description of the schema."""
        descriptions = {
            'malicious': 'Security analysis response with threat assessment and findings',
            'breakdownConcepts': 'Structured concept extraction with visualization opportunities',
            'convertToSlides': 'Complete slide presentation structure with visual placeholders',
            'visual_element_extraction': 'Analysis of visual elements in images for slide integration',
            'slide_content_extraction': 'Slide-ready content extraction from images',
            'chart_data_extraction': 'Detailed data extraction from charts and graphs'
        }
        return descriptions.get(schema_name, 'Schema description not available')
